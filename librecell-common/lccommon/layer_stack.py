#
# LayerStack — Dynamic layer stack built from TechConfig.
#
# Replaces hardcoded layers.py with runtime-constructed layer information,
# supporting arbitrary metal layer counts (2-6).
#
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx


class LayerStack:
    """Dynamic layer stack constructed from TechConfig.

    Provides:
    - ``layermap``: layer name → (gds_layer, gds_purpose) mapping
    - ``layermap_reverse``: (gds_layer, gds_purpose) → layer name
    - ``via_layers``: networkx Graph encoding via connectivity
    - Legacy ``l_xxx`` class-level constants for backward compat
    - Query helpers: ``get_metal_layers()``, ``get_via_between()``, etc.
    """

    # Legacy layer name constants (same values as layers.py)
    l_ndiffusion = 'ndiffusion'
    l_pdiffusion = 'pdiffusion'
    l_nwell = 'nwell'
    l_pwell = 'pwell'
    l_poly = 'poly'
    l_poly_label = 'poly_label'
    l_pdiff_contact = 'pdiff_contact'
    l_ndiff_contact = 'ndiff_contact'
    l_poly_contact = 'poly_contact'
    l_metal1 = 'metal1'
    l_metal1_label = 'metal1_label'
    l_metal1_pin = 'metal1_pin'
    l_via1 = 'via1'
    l_metal2 = 'metal2'
    l_metal2_label = 'metal2_label'
    l_metal2_pin = 'metal2_pin'
    l_abutment_box = 'abutment_box'

    # BCD / HV layer name constants
    l_hv_nwell = 'hv_nwell'
    l_hv_pwell = 'hv_pwell'
    l_thick_oxide = 'thick_oxide'
    l_deep_nwell = 'deep_nwell'

    def __init__(self, tech_config):
        """Build layer stack from a TechConfig instance.

        :param tech_config: TechConfig with output_map and via_connectivity.
        """
        self._tech = tech_config
        self._layermap = self._build_layermap(tech_config)
        self._layermap_reverse: Dict[Tuple[int, int], str] = {}
        for name, gds in self._layermap.items():
            # First mapping wins (no overwrite) — keeps the primary layer name
            if gds not in self._layermap_reverse:
                self._layermap_reverse[gds] = name
        self._via_layers = self._build_via_graph(tech_config)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_layermap(tech_config) -> Dict[str, Tuple[int, int]]:
        """Build layermap from output_map_resolved.

        output_map maps layer names to either:
        - (gds_layer, gds_purpose) — single layer
        - [(gds_layer, gds_purpose), ...] — multi-layer (one-to-many)

        For multi-layer mappings we use the *first* entry as the primary
        GDS mapping (the internal layermap needs a unique mapping per name).
        """
        lmap: Dict[str, Tuple[int, int]] = {}
        for name, spec in tech_config.output_map_resolved.items():
            if isinstance(spec, tuple) and len(spec) == 2 and isinstance(spec[0], int):
                lmap[name] = spec
            elif isinstance(spec, list) and len(spec) > 0:
                # Multi-layer: take the first entry as the primary mapping
                lmap[name] = tuple(spec[0]) if isinstance(spec[0], list) else spec[0]
            else:
                # Fallback: try to use as-is
                lmap[name] = spec
        return lmap

    @staticmethod
    def _build_via_graph(tech_config) -> nx.Graph:
        """Build via connectivity graph.

        Prefers explicit ``via_connectivity`` from TechConfig.
        Falls back to legacy ``layers.py`` defaults if not provided.
        """
        g = nx.Graph()

        via_conn = getattr(tech_config, 'via_connectivity', [])
        if via_conn:
            for vc in via_conn:
                g.add_edge(vc.bottom, vc.top, layer=vc.via)
        else:
            # Legacy fallback: import from layers.py
            from lclayout.layout.layers import via_layers as legacy_via_layers
            return legacy_via_layers.copy()

        return g

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def layermap(self) -> Dict[str, Tuple[int, int]]:
        """Layer name → (gds_layer, gds_purpose)."""
        return self._layermap

    @property
    def layermap_reverse(self) -> Dict[Tuple[int, int], str]:
        """(gds_layer, gds_purpose) → layer name."""
        return self._layermap_reverse

    @property
    def via_layers(self) -> nx.Graph:
        """Networkx Graph encoding via connectivity.

        Edges: (bottom_layer, top_layer) with ``data['layer']`` = via layer name.
        """
        return self._via_layers

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def all_layers(self) -> List[Tuple[str, int, int]]:
        """Return all (name, gds_layer, gds_purpose) triples."""
        return [(name, gds[0], gds[1]) for name, gds in self._layermap.items()]

    def get_metal_layers(self) -> List[str]:
        """Return metal layer names in order (metal1, metal2, ...)."""
        metals = []
        for name in self._layermap:
            if name.startswith('metal') and '_' not in name:
                metals.append(name)
        return sorted(metals)

    def get_via_between(self, l1: str, l2: str) -> Optional[str]:
        """Return the via layer name connecting l1 and l2, or None."""
        if self._via_layers.has_edge(l1, l2):
            return self._via_layers[l1][l2]['layer']
        return None

    def get_via_definitions(self) -> List[Dict[str, str]]:
        """Return list of via definitions as dicts with 'via', 'bottom', 'top' keys."""
        result = []
        for l1, l2, data in self._via_layers.edges(data=True):
            result.append({'via': data['layer'], 'bottom': l1, 'top': l2})
        return result

    def get_label_layer(self, metal_name: str) -> Optional[str]:
        """Return the label layer for a metal layer (e.g. 'metal1' -> 'metal1_label')."""
        label_name = metal_name + '_label'
        if label_name in self._layermap:
            return label_name
        return None

    def get_pin_layer(self, metal_name: str) -> Optional[str]:
        """Return the pin layer for a metal layer (e.g. 'metal1' -> 'metal1_pin')."""
        pin_name = metal_name + '_pin'
        if pin_name in self._layermap:
            return pin_name
        return None

    # ------------------------------------------------------------------
    # Legacy class method
    # ------------------------------------------------------------------

    @classmethod
    def from_legacy(cls) -> 'LayerStack':
        """Create a LayerStack from the hardcoded layers.py defaults.

        Useful for backward compatibility and testing.
        """
        from lclayout.layout import layers as legacy

        class _FakeTech:
            """Minimal object that provides what LayerStack.__init__ needs."""
            output_map_resolved = {name: gds for name, gds in legacy.layermap.items()}
            via_connectivity = []

        stack = cls.__new__(cls)
        stack._tech = None
        stack._layermap = dict(legacy.layermap)
        stack._layermap_reverse = dict(legacy.layermap_reverse)
        stack._via_layers = legacy.via_layers.copy()
        return stack
