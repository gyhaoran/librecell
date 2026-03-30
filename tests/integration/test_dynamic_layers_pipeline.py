"""
Integration tests for dynamic layer stack across the pipeline.
"""
import pytest
import networkx as nx


@pytest.fixture
def layer_stack(dummy_tech):
    from lccommon.layer_stack import LayerStack
    return LayerStack(dummy_tech)


class TestLayerStackWithRoutingGraph:
    """Test that routing_graph works with dynamic via_layers."""

    def test_create_routing_graph_with_dynamic_via_layers(self, dummy_tech, layer_stack):
        """Routing graph creation accepts dynamic via_layers."""
        from lclayout.routing_graph import create_routing_graph_base

        tech = dummy_tech
        pitch_x = tech.routing_grid_pitch_x
        pitch_y = tech.routing_grid_pitch_y

        # Grid is a list of (x, y) coordinate tuples
        grid = [(x * pitch_x, y * pitch_y)
                for x in range(3) for y in range(3)]

        # Should not raise with dynamic via_layers
        graph = create_routing_graph_base(grid, tech, layer_stack.via_layers)
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() > 0


class TestLayerStackWithWriters:
    """Test that writers work with dynamic layermap."""

    def test_remap_layers_with_dynamic_layermap(self, layer_stack):
        """remap_layers accepts dynamic layermap_reverse."""
        from lclayout.writer.writer import remap_layers
        import klayout.db as db

        layout = db.Layout()
        cell = layout.create_cell("TEST")

        # Register a metal1 layer and add a shape
        gds = layer_stack.layermap.get('metal1')
        if gds:
            idx = layout.layer(*gds)
            cell.shapes(idx).insert(db.Box(0, 0, 100, 100))

        # Build output_map from layermap (identity mapping for test)
        output_map = {name: gds for name, gds in layer_stack.layermap.items()}

        result = remap_layers(layout, output_map, layermap_reverse=layer_stack.layermap_reverse)
        assert isinstance(result, db.Layout)


class TestLayerStackConsistency:
    """Test consistency between LayerStack and TechConfig."""

    def test_via_layers_consistent_with_tech(self, dummy_tech, layer_stack):
        """via_layers from LayerStack should match TechConfig.via_layers."""
        tech_vias = dummy_tech.via_layers
        stack_vias = layer_stack.via_layers
        assert set(tech_vias.edges()) == set(stack_vias.edges())

    def test_layermap_consistent_with_tech(self, dummy_tech, layer_stack):
        """layermap from LayerStack should match TechConfig.layermap."""
        assert dummy_tech.layermap == layer_stack.layermap

    def test_all_via_layers_in_layermap(self, layer_stack):
        """All layers referenced by via connectivity should exist in the layermap."""
        for l1, l2, data in layer_stack.via_layers.edges(data=True):
            via_name = data['layer']
            assert l1 in layer_stack.layermap, f"Via endpoint {l1} not in layermap"
            assert l2 in layer_stack.layermap, f"Via endpoint {l2} not in layermap"
            assert via_name in layer_stack.layermap, f"Via {via_name} not in layermap"

    def test_metal_layers_have_label_and_pin(self, layer_stack):
        """Each metal layer should have corresponding label and pin layers."""
        for metal in layer_stack.get_metal_layers():
            assert layer_stack.get_label_layer(metal) is not None, \
                f"Missing label layer for {metal}"
            assert layer_stack.get_pin_layer(metal) is not None, \
                f"Missing pin layer for {metal}"


class TestLayerStackDrcCleaner:
    """Test DRC cleaner dynamic containment constraints."""

    def test_containment_constraints_dynamic(self, dummy_tech, layer_stack):
        """Containment constraints should be derivable from via_layers."""
        # Simulate what drc_cleaner.py does dynamically
        constraints = []

        # Diffusion contains its contacts
        for bottom, top, data in layer_stack.via_layers.edges(data=True):
            via_name = data['layer']
            if bottom in layer_stack.layermap and via_name in layer_stack.layermap:
                constraints.append(([bottom], [via_name]))
            if top in layer_stack.layermap and via_name in layer_stack.layermap:
                constraints.append(([top], [via_name]))

        # Should have containment for all via connections
        assert len(constraints) >= 8  # 4 vias * 2 endpoints each
