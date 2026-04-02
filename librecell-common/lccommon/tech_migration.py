#
# Tech Migration Engine — migrate TechConfig between process nodes / track configs.
#
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel

from lccommon.tech_config import TechConfig

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Data models
# -------------------------------------------------------------------------


class MigrationRule(BaseModel):
    """Describes how to transform a source TechConfig into a target one."""
    source_node: str
    target_node: str
    scale_factor: float = 1.0

    # Per-path scale factor overrides (dot-path → factor).
    # Applied *instead of* scale_factor for that path.
    overrides: Dict[str, float] = {}

    # Absolute value overrides — set directly, no scaling.
    fixed_values: Dict[str, Any] = {}


class MigrationReport(BaseModel):
    """Result of validate_feasibility()."""
    feasible: bool = True
    warnings: List[str] = []
    errors: List[str] = []
    param_changes: Dict[str, Any] = {}  # dot_path → [old, new]


# -------------------------------------------------------------------------
# Helpers — dot-path resolution
# -------------------------------------------------------------------------


def _resolve_dot_path(data: dict, path: str) -> Any:
    """Read a value from a nested dict using a dot-separated path.

    >>> _resolve_dot_path({"cell": {"gate_length": 50}}, "cell.gate_length")
    50
    """
    parts = path.split('.')
    current = data
    for i, part in enumerate(parts):
        if isinstance(current, dict):
            if part not in current:
                available = list(current.keys())
                raise ValueError(
                    f"Path '{'.'.join(parts[:i+1])}' not found. "
                    f"Available keys: {available}"
                )
            current = current[part]
        else:
            raise ValueError(
                f"Cannot descend into non-dict at '{'.'.join(parts[:i])}' "
                f"(type={type(current).__name__})"
            )
    return current


def _set_dot_path(data: dict, path: str, value: Any) -> None:
    """Set a value in a nested dict using a dot-separated path.

    Creates intermediate dicts if they don't exist.
    """
    parts = path.split('.')
    current = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


# -------------------------------------------------------------------------
# Helpers — recursive scaling
# -------------------------------------------------------------------------

# Top-level keys that should NOT be scaled at all.
_NO_SCALE_KEYS = frozenset({
    'name', 'node', 'db_unit',
    'layers', 'vias', 'via_connectivity',
    'power_domains', 'bcd', 'scripts',
    'output_map', 'writers', 'extensions',
})

# Keys inside scalable sub-trees whose *values* should not be scaled.
_SKIP_VALUE_KEYS = frozenset({
    'pin_layer', 'power_layer',
    'num_tracks', 'transistor_channel_width_sizing',
    'routing_layers', 'connectable_layers',
    'orientation_change_penalty',
    'weights_horizontal', 'weights_vertical',
    'via_weights', 'multi_via',
})


def _scale_value(value: Any, factor: float) -> Any:
    """Scale a single value: round floats to int, recurse into containers."""
    if isinstance(value, float):
        return round(value * factor)
    if isinstance(value, int):
        # Integers are discrete — don't scale
        return value
    if isinstance(value, dict):
        return _scale_dict(value, factor)
    if isinstance(value, list):
        return [_scale_value(v, factor) for v in value]
    # str, bool, None, etc. — pass through
    return value


def _scale_dict(data: dict, factor: float) -> dict:
    """Recursively scale float values in a dict, skipping known non-geometric keys."""
    result = {}
    for key, value in data.items():
        if key in _SKIP_VALUE_KEYS:
            result[key] = value  # copy as-is
        else:
            result[key] = _scale_value(value, factor)
    return result


# -------------------------------------------------------------------------
# TechMigrator
# -------------------------------------------------------------------------


class TechMigrator:
    """Applies a MigrationRule to transform a TechConfig."""

    def __init__(self, rule: MigrationRule):
        self.rule = rule

    def migrate(self, source: TechConfig) -> TechConfig:
        """Apply migration rule, return new TechConfig."""
        data = source.model_dump()
        factor = self.rule.scale_factor

        # 1. Scale geometric sub-trees
        scaled = {}
        for key, value in data.items():
            if key in _NO_SCALE_KEYS:
                scaled[key] = value
            elif isinstance(value, dict) and factor != 1.0:
                scaled[key] = _scale_dict(value, factor)
            else:
                scaled[key] = value

        # 2. Apply per-path overrides (scale by override factor instead)
        for path, override_factor in self.rule.overrides.items():
            try:
                original = _resolve_dot_path(data, path)
            except ValueError:
                logger.warning("Override path '%s' not found in source, skipping", path)
                continue
            if isinstance(original, (int, float)):
                _set_dot_path(scaled, path, round(original * override_factor))
            else:
                logger.warning("Override path '%s' points to non-numeric value, skipping", path)

        # 3. Apply fixed values (absolute, no scaling)
        for path, value in self.rule.fixed_values.items():
            _set_dot_path(scaled, path, value)

        # 4. Set target node name
        scaled['node'] = self.rule.target_node

        # 5. For track migration: clear auto-derived fields so validators re-derive
        if 'cell' in scaled and 'num_tracks' in scaled.get('cell', {}):
            cell = scaled['cell']
            num_tracks = cell.get('num_tracks')
            track_pitch = cell.get('track_pitch')
            if num_tracks is not None and track_pitch is not None:
                # Remove unit_cell_height so the validator computes it
                cell.pop('unit_cell_height', None)
                # Remove routing auto-derived values
                routing = scaled.get('routing', {})
                routing.pop('routing_grid_pitch_y', None)
                routing.pop('grid_offset_y', None)
                # Remove transistor_offset_y so it gets auto-computed
                cell.pop('transistor_offset_y', None)

        # 6. Rebuild via Pydantic validation (triggers auto-derivation)
        target = TechConfig.model_validate(scaled)
        return target

    def validate_feasibility(
        self,
        source: TechConfig,
        target: TechConfig,
        cell_names: Optional[List[str]] = None,
    ) -> MigrationReport:
        """Check migration feasibility, especially for downward track migration."""
        report = MigrationReport()

        source_tracks = source.cell.num_tracks
        target_tracks = target.cell.num_tracks

        if source_tracks is not None and target_tracks is not None:
            if target_tracks < source_tracks:
                report.warnings.append(
                    f"Downward track migration: {source_tracks}T -> {target_tracks}T. "
                    f"Some complex cells may not fit."
                )

                # Check each cell if names provided
                if cell_names:
                    from lclayout.routing_graph import estimate_min_tracks
                    from lccommon.data_types import Transistor, ChannelType

                    for cell_name in cell_names:
                        # Use heuristic: estimate based on cell name complexity
                        min_tracks = _estimate_cell_min_tracks(cell_name)
                        if min_tracks > target_tracks:
                            msg = (
                                f"Cell '{cell_name}' estimated to need >= {min_tracks} tracks, "
                                f"target has only {target_tracks}T"
                            )
                            report.errors.append(msg)
                            report.feasible = False

        # Check for extreme scaling
        if self.rule.scale_factor < 0.4:
            report.warnings.append(
                f"Aggressive scaling factor {self.rule.scale_factor:.3f} — "
                f"verify all DRC rules are physically realizable"
            )

        # Record parameter changes
        report.param_changes = self._compute_param_changes(source, target)

        return report

    def generate_migration_report(self, source: TechConfig, target: TechConfig) -> str:
        """Generate human-readable migration report."""
        lines = [
            f"Migration Report: {self.rule.source_node} -> {self.rule.target_node}",
            f"Scale factor: {self.rule.scale_factor}",
            "=" * 60,
        ]

        changes = self._compute_param_changes(source, target)
        if changes:
            lines.append(f"\nParameter changes ({len(changes)}):")
            for path, (old, new) in sorted(changes.items()):
                lines.append(f"  {path}: {old} -> {new}")
        else:
            lines.append("\nNo parameter changes detected.")

        if self.rule.overrides:
            lines.append(f"\nOverrides applied ({len(self.rule.overrides)}):")
            for path, factor in self.rule.overrides.items():
                lines.append(f"  {path}: x{factor}")

        if self.rule.fixed_values:
            lines.append(f"\nFixed values ({len(self.rule.fixed_values)}):")
            for path, value in self.rule.fixed_values.items():
                lines.append(f"  {path} = {value}")

        return "\n".join(lines)

    def _compute_param_changes(
        self, source: TechConfig, target: TechConfig
    ) -> Dict[str, Tuple[Any, Any]]:
        """Compare source and target, return {dot_path: (old_val, new_val)}."""
        src_data = source.model_dump()
        tgt_data = target.model_dump()
        changes: Dict[str, Tuple[Any, Any]] = {}
        _diff_dicts(src_data, tgt_data, "", changes)
        return changes


def _diff_dicts(
    src: Any, tgt: Any, prefix: str, out: Dict[str, Tuple[Any, Any]]
) -> None:
    """Recursively diff two nested dicts, recording (old, new) for changed leaf values."""
    if isinstance(src, dict) and isinstance(tgt, dict):
        all_keys = set(src.keys()) | set(tgt.keys())
        for k in sorted(all_keys):
            path = f"{prefix}.{k}" if prefix else k
            _diff_dicts(src.get(k), tgt.get(k), path, out)
    elif src != tgt:
        out[prefix] = (src, tgt)


def _estimate_cell_min_tracks(cell_name: str) -> int:
    """Heuristic: estimate minimum tracks from cell name complexity.

    Simple cells (INV, BUF, NAND2, NOR2) → ~5 tracks
    Medium cells (AOI, OAI, MUX) → ~7 tracks
    Complex cells (DFF, LATCH) → ~9 tracks
    """
    name_upper = cell_name.upper()
    if any(k in name_upper for k in ('DFF', 'LATCH', 'SDFF', 'DLATCH')):
        return 9
    if any(k in name_upper for k in ('AOI', 'OAI', 'MUX', 'ADDER', 'FA', 'HA')):
        return 7
    if any(k in name_upper for k in ('NAND3', 'NOR3', 'AND3', 'OR3', 'NAND4', 'NOR4')):
        return 6
    # Simple: INV, BUF, NAND2, NOR2, AND2, OR2, XOR2, XNOR2
    return 5


# -------------------------------------------------------------------------
# YAML loading
# -------------------------------------------------------------------------


def load_migration_rule(path: str) -> MigrationRule:
    """Load a MigrationRule from a YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return MigrationRule.model_validate(data)


def save_migration_rule(rule: MigrationRule, path: str) -> None:
    """Save a MigrationRule to a YAML file."""
    data = rule.model_dump(exclude_none=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
