"""
Unit tests for LayerStack dynamic layer system.
"""
import pytest
import networkx as nx


@pytest.fixture
def layer_stack(dummy_tech):
    """Create LayerStack from dummy_tech TechConfig."""
    from lccommon.layer_stack import LayerStack
    return LayerStack(dummy_tech)


class TestLayerStackConstruction:
    """Test LayerStack construction from TechConfig."""

    def test_create_from_tech_config(self, dummy_tech):
        from lccommon.layer_stack import LayerStack
        ls = LayerStack(dummy_tech)
        assert ls is not None

    def test_layermap_not_empty(self, layer_stack):
        assert len(layer_stack.layermap) > 0

    def test_layermap_has_core_layers(self, layer_stack):
        for name in ['ndiffusion', 'pdiffusion', 'poly', 'metal1', 'metal2',
                      'nwell', 'pwell', 'abutment_box']:
            assert name in layer_stack.layermap, f"Missing layer: {name}"

    def test_layermap_values_are_gds_tuples(self, layer_stack):
        for name, gds in layer_stack.layermap.items():
            assert isinstance(gds, tuple), f"{name}: expected tuple, got {type(gds)}"
            assert len(gds) == 2, f"{name}: expected 2-tuple, got {len(gds)}-tuple"
            assert isinstance(gds[0], int) and isinstance(gds[1], int), \
                f"{name}: expected (int, int), got ({type(gds[0])}, {type(gds[1])})"

    def test_layermap_reverse_roundtrip(self, layer_stack):
        for name, gds in layer_stack.layermap.items():
            if gds in layer_stack.layermap_reverse:
                reverse_name = layer_stack.layermap_reverse[gds]
                assert layer_stack.layermap[reverse_name] == gds


class TestViaLayers:
    """Test via connectivity graph."""

    def test_via_layers_is_graph(self, layer_stack):
        assert isinstance(layer_stack.via_layers, nx.Graph)

    def test_via_layers_has_edges(self, layer_stack):
        assert layer_stack.via_layers.number_of_edges() > 0

    def test_ndiff_contact_connects_ndiffusion_metal1(self, layer_stack):
        assert layer_stack.via_layers.has_edge('ndiffusion', 'metal1')
        assert layer_stack.via_layers['ndiffusion']['metal1']['layer'] == 'ndiff_contact'

    def test_pdiff_contact_connects_pdiffusion_metal1(self, layer_stack):
        assert layer_stack.via_layers.has_edge('pdiffusion', 'metal1')
        assert layer_stack.via_layers['pdiffusion']['metal1']['layer'] == 'pdiff_contact'

    def test_poly_contact_connects_poly_metal1(self, layer_stack):
        assert layer_stack.via_layers.has_edge('poly', 'metal1')
        assert layer_stack.via_layers['poly']['metal1']['layer'] == 'poly_contact'

    def test_via1_connects_metal1_metal2(self, layer_stack):
        assert layer_stack.via_layers.has_edge('metal1', 'metal2')
        assert layer_stack.via_layers['metal1']['metal2']['layer'] == 'via1'


class TestQueryHelpers:
    """Test LayerStack query methods."""

    def test_all_layers_returns_triples(self, layer_stack):
        for name, gds_layer, gds_purpose in layer_stack.all_layers():
            assert isinstance(name, str)
            assert isinstance(gds_layer, int)
            assert isinstance(gds_purpose, int)

    def test_get_metal_layers_sorted(self, layer_stack):
        metals = layer_stack.get_metal_layers()
        assert metals == sorted(metals)
        assert 'metal1' in metals
        assert 'metal2' in metals

    def test_get_metal_layers_excludes_labels_pins(self, layer_stack):
        metals = layer_stack.get_metal_layers()
        for m in metals:
            assert '_label' not in m
            assert '_pin' not in m

    def test_get_via_between_existing(self, layer_stack):
        assert layer_stack.get_via_between('metal1', 'metal2') == 'via1'
        assert layer_stack.get_via_between('ndiffusion', 'metal1') == 'ndiff_contact'

    def test_get_via_between_nonexistent(self, layer_stack):
        assert layer_stack.get_via_between('ndiffusion', 'metal2') is None

    def test_get_via_definitions(self, layer_stack):
        vias = layer_stack.get_via_definitions()
        assert len(vias) >= 4
        via_names = {v['via'] for v in vias}
        assert 'ndiff_contact' in via_names
        assert 'via1' in via_names

    def test_get_label_layer(self, layer_stack):
        assert layer_stack.get_label_layer('metal1') == 'metal1_label'
        assert layer_stack.get_label_layer('metal2') == 'metal2_label'

    def test_get_pin_layer(self, layer_stack):
        assert layer_stack.get_pin_layer('metal1') == 'metal1_pin'
        assert layer_stack.get_pin_layer('metal2') == 'metal2_pin'

    def test_get_label_layer_nonexistent(self, layer_stack):
        assert layer_stack.get_label_layer('nonexistent') is None


class TestLegacyConstants:
    """Test backward-compatible class constants."""

    def test_l_constants_are_strings(self, layer_stack):
        assert layer_stack.l_ndiffusion == 'ndiffusion'
        assert layer_stack.l_pdiffusion == 'pdiffusion'
        assert layer_stack.l_nwell == 'nwell'
        assert layer_stack.l_pwell == 'pwell'
        assert layer_stack.l_poly == 'poly'
        assert layer_stack.l_metal1 == 'metal1'
        assert layer_stack.l_metal2 == 'metal2'
        assert layer_stack.l_abutment_box == 'abutment_box'

    def test_l_constants_match_class_level(self):
        from lccommon.layer_stack import LayerStack
        assert LayerStack.l_ndiffusion == 'ndiffusion'
        assert LayerStack.l_metal1 == 'metal1'


class TestFromLegacy:
    """Test LayerStack.from_legacy() classmethod."""

    def test_from_legacy_creates_layer_stack(self):
        from lccommon.layer_stack import LayerStack
        ls = LayerStack.from_legacy()
        assert ls is not None

    def test_from_legacy_layermap_matches(self):
        from lccommon.layer_stack import LayerStack
        from lclayout.layout.layers import layermap
        ls = LayerStack.from_legacy()
        assert ls.layermap == layermap

    def test_from_legacy_via_layers_edges(self):
        from lccommon.layer_stack import LayerStack
        from lclayout.layout.layers import via_layers
        ls = LayerStack.from_legacy()
        assert set(ls.via_layers.edges()) == set(via_layers.edges())


class TestTechConfigIntegration:
    """Test LayerStack integration with TechConfig properties."""

    def test_tech_config_layer_stack_property(self, dummy_tech):
        ls = dummy_tech.layer_stack
        assert ls is not None

    def test_tech_config_via_layers_property(self, dummy_tech):
        via_layers = dummy_tech.via_layers
        assert isinstance(via_layers, nx.Graph)
        assert via_layers.number_of_edges() >= 4

    def test_tech_config_layermap_property(self, dummy_tech):
        lmap = dummy_tech.layermap
        assert 'metal1' in lmap
        assert 'metal2' in lmap

    def test_tech_config_layermap_reverse_property(self, dummy_tech):
        lmap_rev = dummy_tech.layermap_reverse
        assert len(lmap_rev) > 0
