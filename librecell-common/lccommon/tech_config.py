#
# TechConfig — Pydantic v2 models for LibreCell technology configuration.
#
# Replaces the untyped Python module tech config (dummy_tech.py) with
# schema-validated, YAML-serializable data models.
#
from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Set, Tuple, Union

from pydantic import BaseModel, ConfigDict, Discriminator, Field, PrivateAttr, Tag


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class CellConfig(BaseModel):
    """Cell geometry parameters."""
    unit_cell_width: float
    unit_cell_height: float
    gate_length: float
    gate_extension: float
    transistor_offset_y: float
    power_rail_width: float
    minimum_gate_width_nfet: float
    minimum_gate_width_pfet: float
    minimum_pin_width: float
    transistor_channel_width_sizing: float = 1.0
    pin_layer: str = "metal2"
    power_layer: str = "metal2"


class RoutingConfig(BaseModel):
    """Routing grid and weight parameters."""
    routing_grid_pitch_x: float
    routing_grid_pitch_y: float
    grid_offset_x: float = 0
    grid_offset_y: float = 0
    orientation_change_penalty: float = 100
    routing_layers: Dict[str, str] = {}
    wire_width: Dict[str, float] = {}
    wire_width_horizontal: Dict[str, float] = {}
    via_size: Dict[str, float] = {}
    weights_horizontal: Dict[str, float] = {}
    weights_vertical: Dict[str, float] = {}
    connectable_layers: List[str] = []


class DrcConfig(BaseModel):
    """Design-rule-check parameters (spacing, width, enclosure, etc.)."""
    minimum_width: Dict[str, float] = {}
    minimum_notch: Dict[str, float] = {}
    min_area: Dict[str, float] = {}
    # Nested dicts — YAML friendly.  Flat tuple-key access via TechConfig properties.
    min_spacing: Dict[str, Dict[str, float]] = {}
    minimum_enclosure: Dict[str, Dict[str, float]] = {}


class ViaConfig(BaseModel):
    """Via weight and multi-via parameters (nested dicts)."""
    via_weights: Dict[str, Dict[str, float]] = {}
    multi_via: Dict[str, Dict[str, int]] = {}


# ---------------------------------------------------------------------------
# Writer config — discriminated union
# ---------------------------------------------------------------------------

class MagWriterConfig(BaseModel):
    type: Literal["mag"] = "mag"
    tech_name: str = "scmos"
    scale_factor: float = 1.0
    output_map: Dict[str, Union[str, List[str]]] = {}


class LefWriterConfig(BaseModel):
    type: Literal["lef"] = "lef"
    db_unit: float = 1e-6
    site: str = "CORE"


class GdsWriterConfig(BaseModel):
    type: Literal["gds"] = "gds"
    db_unit: Optional[float] = None  # defaults to general db_unit


WriterConfigUnion = Annotated[
    Union[
        Annotated[MagWriterConfig, Tag("mag")],
        Annotated[LefWriterConfig, Tag("lef")],
        Annotated[GdsWriterConfig, Tag("gds")],
    ],
    Discriminator(lambda v: v.get("type") if isinstance(v, dict) else v.type),
]


# ---------------------------------------------------------------------------
# Layer / Via / Power domain definitions (for future Tasks 04-06)
# ---------------------------------------------------------------------------

class LayerDefinition(BaseModel):
    """Single process layer."""
    name: str
    gds_layer: int
    gds_purpose: int = 0
    material: Optional[str] = None
    direction: Optional[str] = None
    min_width: Optional[float] = None
    min_spacing: Optional[float] = None


class ViaDefinition(BaseModel):
    """Via layer connecting two metal layers."""
    name: str
    gds_layer: int
    gds_purpose: int = 0
    bottom_layer: str = ""
    top_layer: str = ""
    size: float = 0


class PowerDomain(BaseModel):
    """Power domain (supply + ground nets)."""
    name: str = "default"
    supply_net: str = "VDD"
    ground_net: str = "VSS"
    voltage: Optional[float] = None


# ---------------------------------------------------------------------------
# Top-level TechConfig
# ---------------------------------------------------------------------------

class TechConfig(BaseModel):
    """Complete technology configuration.

    Provides ~30 flat ``@property`` accessors so that existing code using
    ``tech.unit_cell_width`` style attribute access continues to work
    unchanged.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Metadata
    name: str = "unnamed"
    node: str = ""
    db_unit: float = 1e-9

    # Sub-models (structured storage)
    cell: CellConfig
    routing: RoutingConfig
    drc: DrcConfig = DrcConfig()
    via: ViaConfig = ViaConfig()

    # Layer / via / power-domain definitions (optional, filled by Tasks 04-06)
    layers: List[LayerDefinition] = []
    vias: List[ViaDefinition] = []
    power_domains: List[PowerDomain] = Field(default_factory=lambda: [PowerDomain()])

    # Output map — internal layer name → GDS (layer, purpose) or list thereof.
    # Stored as nested lists for YAML; property converts to tuples.
    output_map: Dict[str, Any] = {}

    # Writer descriptors
    writers: List[WriterConfigUnion] = Field(default_factory=list)

    # Optional extensions
    extensions: Dict[str, Any] = {}

    # Private cached fields
    _writer_instances: Optional[List] = PrivateAttr(default=None)
    _output_map_cache: Optional[Dict] = PrivateAttr(default=None)
    _min_spacing_cache: Optional[Dict] = PrivateAttr(default=None)
    _minimum_enclosure_cache: Optional[Dict] = PrivateAttr(default=None)
    _via_weights_cache: Optional[Dict] = PrivateAttr(default=None)
    _multi_via_cache: Optional[Dict] = PrivateAttr(default=None)

    # ------------------------------------------------------------------
    # Helpers: nested ↔ tuple-key conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _nested_to_tuple_keys(nested: Dict[str, Dict[str, Any]]) -> Dict[Tuple[str, str], Any]:
        """``{a: {b: v}}`` → ``{(a, b): v}``."""
        result: Dict[Tuple[str, str], Any] = {}
        for outer, inner in nested.items():
            for inner_key, value in inner.items():
                result[(outer, inner_key)] = value
        return result

    @staticmethod
    def _tuple_keys_to_nested(d: Dict[Tuple[str, str], Any]) -> Dict[str, Dict[str, Any]]:
        """``{(a, b): v}`` → ``{a: {b: v}}``."""
        result: Dict[str, Dict[str, Any]] = {}
        for (k1, k2), v in d.items():
            result.setdefault(k1, {})[k2] = v
        return result

    @staticmethod
    def _resolve_output_map(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Convert YAML list representations to tuples for engine consumption.

        - ``[1, 0]``  → ``(1, 0)``  (single layer)
        - ``[[2,0],[2,1]]`` → ``[(2,0),(2,1)]``  (multi-layer)
        """
        resolved: Dict[str, Any] = {}
        for name, spec in raw.items():
            if isinstance(spec, (list, tuple)):
                if len(spec) == 0:
                    resolved[name] = spec
                elif isinstance(spec[0], (list, tuple)):
                    # Multi-layer: [[2,0],[2,1]]
                    resolved[name] = [tuple(s) for s in spec]
                elif isinstance(spec[0], int):
                    # Single layer: [1,0]
                    resolved[name] = tuple(spec)
                else:
                    resolved[name] = spec
            else:
                resolved[name] = spec
        return resolved

    # ------------------------------------------------------------------
    # Flat property accessors — cell sub-model
    # ------------------------------------------------------------------

    @property
    def unit_cell_width(self) -> float:
        return self.cell.unit_cell_width

    @property
    def unit_cell_height(self) -> float:
        return self.cell.unit_cell_height

    @property
    def gate_length(self) -> float:
        return self.cell.gate_length

    @property
    def gate_extension(self) -> float:
        return self.cell.gate_extension

    @property
    def transistor_offset_y(self) -> float:
        return self.cell.transistor_offset_y

    @property
    def power_rail_width(self) -> float:
        return self.cell.power_rail_width

    @property
    def minimum_gate_width_nfet(self) -> float:
        return self.cell.minimum_gate_width_nfet

    @property
    def minimum_gate_width_pfet(self) -> float:
        return self.cell.minimum_gate_width_pfet

    @property
    def minimum_pin_width(self) -> float:
        return self.cell.minimum_pin_width

    @property
    def transistor_channel_width_sizing(self) -> float:
        return self.cell.transistor_channel_width_sizing

    @property
    def pin_layer(self) -> str:
        return self.cell.pin_layer

    @property
    def power_layer(self) -> str:
        return self.cell.power_layer

    # ------------------------------------------------------------------
    # Flat property accessors — routing sub-model
    # ------------------------------------------------------------------

    @property
    def routing_grid_pitch_x(self) -> float:
        return self.routing.routing_grid_pitch_x

    @property
    def routing_grid_pitch_y(self) -> float:
        return self.routing.routing_grid_pitch_y

    @property
    def grid_offset_x(self) -> float:
        return self.routing.grid_offset_x

    @property
    def grid_offset_y(self) -> float:
        return self.routing.grid_offset_y

    @property
    def orientation_change_penalty(self) -> float:
        return self.routing.orientation_change_penalty

    @property
    def routing_layers(self) -> Dict[str, str]:
        return self.routing.routing_layers

    @property
    def wire_width(self) -> Dict[str, float]:
        return self.routing.wire_width

    @property
    def wire_width_horizontal(self) -> Dict[str, float]:
        return self.routing.wire_width_horizontal

    @property
    def via_size(self) -> Dict[str, float]:
        return self.routing.via_size

    @property
    def weights_horizontal(self) -> Dict[str, float]:
        return self.routing.weights_horizontal

    @property
    def weights_vertical(self) -> Dict[str, float]:
        return self.routing.weights_vertical

    @property
    def connectable_layers(self) -> Set[str]:
        return set(self.routing.connectable_layers)

    # ------------------------------------------------------------------
    # Flat property accessors — DRC sub-model
    # ------------------------------------------------------------------

    @property
    def minimum_width(self) -> Dict[str, float]:
        return self.drc.minimum_width

    @property
    def minimum_notch(self) -> Dict[str, float]:
        return self.drc.minimum_notch

    @property
    def min_area(self) -> Dict[str, float]:
        return self.drc.min_area

    @property
    def min_spacing(self) -> Dict[Tuple[str, str], float]:
        if self._min_spacing_cache is None:
            self._min_spacing_cache = self._nested_to_tuple_keys(self.drc.min_spacing)
        return self._min_spacing_cache

    @property
    def minimum_enclosure(self) -> Dict[Tuple[str, str], float]:
        if self._minimum_enclosure_cache is None:
            self._minimum_enclosure_cache = self._nested_to_tuple_keys(self.drc.minimum_enclosure)
        return self._minimum_enclosure_cache

    # ------------------------------------------------------------------
    # Flat property accessors — via sub-model
    # ------------------------------------------------------------------

    @property
    def via_weights(self) -> Dict[Tuple[str, str], float]:
        if self._via_weights_cache is None:
            self._via_weights_cache = self._nested_to_tuple_keys(self.via.via_weights)
        return self._via_weights_cache

    @property
    def multi_via(self) -> Dict[Tuple[str, str], int]:
        if self._multi_via_cache is None:
            self._multi_via_cache = self._nested_to_tuple_keys(self.via.multi_via)
        return self._multi_via_cache

    # ------------------------------------------------------------------
    # Output map (resolved to tuple format)
    # ------------------------------------------------------------------

    @property
    def output_map_resolved(self) -> Dict[str, Any]:
        """Output map with list values converted to tuples."""
        if self._output_map_cache is None:
            self._output_map_cache = self._resolve_output_map(self.output_map)
        return self._output_map_cache

    # ------------------------------------------------------------------
    # Writers (lazy instantiation)
    # ------------------------------------------------------------------

    @property
    def output_writers(self) -> List:
        """Return Writer instances, lazily created from WriterConfig descriptors."""
        if self._writer_instances is None:
            self._writer_instances = self._create_writers()
        return self._writer_instances

    def _create_writers(self) -> List:
        # Lazy imports to avoid circular dependency (writers live in lclayout)
        from lclayout.writer.gds_writer import GdsWriter
        from lclayout.writer.lef_writer import LefWriter
        from lclayout.writer.magic_writer import MagWriter

        resolved_map = self.output_map_resolved
        instances: list = []
        for wc in self.writers:
            if isinstance(wc, MagWriterConfig):
                instances.append(MagWriter(
                    tech_name=wc.tech_name,
                    scale_factor=wc.scale_factor,
                    output_map=wc.output_map,
                ))
            elif isinstance(wc, LefWriterConfig):
                instances.append(LefWriter(
                    db_unit=wc.db_unit,
                    output_map=resolved_map,
                    site=wc.site,
                ))
            elif isinstance(wc, GdsWriterConfig):
                instances.append(GdsWriter(
                    db_unit=wc.db_unit if wc.db_unit is not None else self.db_unit,
                    output_map=resolved_map,
                ))
        return instances

    # ------------------------------------------------------------------
    # Legacy compat: via_layers / layermap (from layers.py, Task 04 replaces)
    # ------------------------------------------------------------------

    @property
    def via_layers(self):
        """Return the via connectivity graph from layers.py (backward compat)."""
        from lclayout.layout.layers import via_layers
        return via_layers

    @property
    def layermap(self):
        """Return the internal layermap from layers.py (backward compat)."""
        from lclayout.layout.layers import layermap
        return layermap
