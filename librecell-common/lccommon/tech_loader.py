#
# Tech loader — YAML loading, saving, and Python module conversion.
#
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import yaml

from lccommon.tech_config import (
    CellConfig,
    DrcConfig,
    GdsWriterConfig,
    LefWriterConfig,
    MagWriterConfig,
    PowerDomain,
    RoutingConfig,
    TechConfig,
    ViaConfig,
    ViaConnectivity,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# YAML load / save  (with file-based cache keyed on abs path + mtime)
# ---------------------------------------------------------------------------

_tech_yaml_cache: Dict[Tuple[str, float], TechConfig] = {}


def load_tech_yaml(path: str) -> TechConfig:
    """Load a TechConfig from a YAML file.

    Results are cached by (absolute path, mtime) so repeated loads of the
    same unchanged file skip YAML parsing and Pydantic validation.
    """
    abs_path = os.path.abspath(path)
    try:
        mtime = os.path.getmtime(abs_path)
    except OSError:
        mtime = 0.0
    cache_key = (abs_path, mtime)
    if cache_key in _tech_yaml_cache:
        logger.debug("Cache hit for %s", abs_path)
        return _tech_yaml_cache[cache_key].model_copy(deep=True)

    logger.info("Loading YAML tech file: %s", abs_path)
    with open(abs_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        from lccommon.exceptions import TechConfigError
        raise TechConfigError(f"Empty YAML file: {path}")
    config = TechConfig.model_validate(data)
    _tech_yaml_cache[cache_key] = config
    return config.model_copy(deep=True)


def save_tech_yaml(config: TechConfig, path: str) -> None:
    """Serialize a TechConfig to a YAML file."""
    data = config.model_dump(
        exclude={"_writer_instances", "_output_map_cache",
                 "_min_spacing_cache", "_minimum_enclosure_cache",
                 "_via_weights_cache", "_multi_via_cache"},
        exclude_none=True,
    )
    abs_path = os.path.abspath(path)
    with open(abs_path, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False, allow_unicode=True)
    # Invalidate any cached entry for this path (any mtime)
    keys_to_remove = [k for k in _tech_yaml_cache if k[0] == abs_path]
    for k in keys_to_remove:
        del _tech_yaml_cache[k]


# ---------------------------------------------------------------------------
# Python tech module → TechConfig conversion
# ---------------------------------------------------------------------------

def _tuple_keys_to_nested(d: Dict[Tuple[str, str], Any]) -> Dict[str, Dict[str, Any]]:
    """``{(a, b): v}`` → ``{a: {b: v}}``."""
    result: Dict[str, Dict[str, Any]] = {}
    for (k1, k2), v in d.items():
        result.setdefault(k1, {})[k2] = v
    return result


def _output_map_to_yaml(omap: Dict[str, Any]) -> Dict[str, Any]:
    """Convert output_map from Python tuple values to YAML-safe list values.

    ``('ndiffusion', (1, 0))`` → ``{'ndiffusion': [1, 0]}``
    ``('nwell', [(2,0),(2,1)])`` → ``{'nwell': [[2, 0], [2, 1]]}``
    """
    result: Dict[str, Any] = {}
    for name, spec in omap.items():
        if isinstance(spec, tuple):
            result[name] = list(spec)
        elif isinstance(spec, list):
            result[name] = [list(s) if isinstance(s, tuple) else s for s in spec]
        else:
            result[name] = spec
    return result


def _writer_to_config(writer: Any) -> Union[MagWriterConfig, LefWriterConfig, GdsWriterConfig]:
    """Reverse-engineer a Writer instance into a WriterConfig descriptor."""
    # Import here to avoid circular dependency at module level
    from lclayout.writer.gds_writer import GdsWriter
    from lclayout.writer.lef_writer import LefWriter
    from lclayout.writer.magic_writer import MagWriter

    if isinstance(writer, MagWriter):
        return MagWriterConfig(
            tech_name=writer.tech_name,
            scale_factor=writer.scale_factor,
            output_map=writer.output_map,
        )
    elif isinstance(writer, LefWriter):
        return LefWriterConfig(
            db_unit=writer.db_unit,
            site=getattr(writer, "site", "CORE"),
        )
    elif isinstance(writer, GdsWriter):
        return GdsWriterConfig(
            db_unit=writer.db_unit,
        )
    else:
        raise TypeError(f"Unknown writer type: {type(writer)}")


def python_tech_to_config(module: Any) -> TechConfig:
    """Convert a loaded Python tech module to a ``TechConfig`` instance.

    Handles all attribute extraction and format conversions (tuple-key dicts
    → nested dicts, output_map tuples → lists, Writer instances → WriterConfig).
    """

    def _get(attr: str, default: Any = None) -> Any:
        return getattr(module, attr, default)

    # --- Cell ---
    cell = CellConfig(
        unit_cell_width=_get("unit_cell_width"),
        unit_cell_height=_get("unit_cell_height"),
        gate_length=_get("gate_length"),
        gate_extension=_get("gate_extension"),
        transistor_offset_y=_get("transistor_offset_y"),
        power_rail_width=_get("power_rail_width"),
        minimum_gate_width_nfet=_get("minimum_gate_width_nfet"),
        minimum_gate_width_pfet=_get("minimum_gate_width_pfet"),
        minimum_pin_width=_get("minimum_pin_width"),
        transistor_channel_width_sizing=_get("transistor_channel_width_sizing", 1.0),
        pin_layer=_get("pin_layer", "metal2"),
        power_layer=_get("power_layer", "metal2"),
    )

    # --- Routing ---
    connectable = _get("connectable_layers", set())
    routing = RoutingConfig(
        routing_grid_pitch_x=_get("routing_grid_pitch_x"),
        routing_grid_pitch_y=_get("routing_grid_pitch_y"),
        grid_offset_x=_get("grid_offset_x", 0),
        grid_offset_y=_get("grid_offset_y", 0),
        orientation_change_penalty=_get("orientation_change_penalty", 100),
        routing_layers=_get("routing_layers", {}),
        wire_width=_get("wire_width", {}),
        wire_width_horizontal=_get("wire_width_horizontal", {}),
        via_size=_get("via_size", {}),
        weights_horizontal=_get("weights_horizontal", {}),
        weights_vertical=_get("weights_vertical", {}),
        connectable_layers=list(connectable) if isinstance(connectable, set) else list(connectable),
    )

    # --- DRC (convert tuple-key dicts to nested) ---
    drc = DrcConfig(
        minimum_width=_get("minimum_width", {}),
        minimum_notch=_get("minimum_notch", {}),
        min_area=_get("min_area", {}),
        min_spacing=_tuple_keys_to_nested(_get("min_spacing", {})),
        minimum_enclosure=_tuple_keys_to_nested(_get("minimum_enclosure", {})),
    )

    # --- Via ---
    via = ViaConfig(
        via_weights=_tuple_keys_to_nested(_get("via_weights", {})),
        multi_via=_tuple_keys_to_nested(_get("multi_via", {})),
    )

    # --- Output map ---
    raw_output_map = _get("output_map", {})
    output_map = _output_map_to_yaml(raw_output_map)

    # --- Writers ---
    raw_writers = _get("output_writers", [])
    writer_configs: List[Union[MagWriterConfig, LefWriterConfig, GdsWriterConfig]] = []
    for w in raw_writers:
        try:
            writer_configs.append(_writer_to_config(w))
        except TypeError:
            logger.warning("Skipping unknown writer type: %s", type(w))

    # --- Via connectivity (from via_layers graph if present) ---
    via_connectivity_list: List[ViaConnectivity] = []
    raw_via_layers = _get("via_layers", None)
    if raw_via_layers is not None and hasattr(raw_via_layers, 'edges'):
        for l1, l2, data in raw_via_layers.edges(data=True):
            via_connectivity_list.append(ViaConnectivity(
                via=data['layer'], bottom=l1, top=l2,
            ))

    return TechConfig(
        name=_get("__name__", "python_tech"),
        node="",
        db_unit=_get("db_unit", 1e-9),
        cell=cell,
        routing=routing,
        drc=drc,
        via=via,
        output_map=output_map,
        writers=writer_configs,
        via_connectivity=via_connectivity_list,
    )
