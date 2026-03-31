"""
Integration tests for multi-track pipeline (Task 05).
"""
import pytest
import networkx as nx


@pytest.mark.integration
class TestMultiTrackLcLayout:
    """Test LcLayout initialization with multi-track configs."""

    @pytest.mark.parametrize("num_tracks", [6, 7, 9, 10, 12])
    def test_lclayout_init_with_track_config(self, project_root, num_tracks):
        """LcLayout can be initialized with multi-track tech config."""
        from lclayout.tech_util import load_tech_file
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter
        import klayout.db as db

        path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{num_tracks}t.yaml"
        tech = load_tech_file(str(path))

        layout = db.Layout()
        placer = EulerPlacer()
        router = GraphRouter()

        lc = LcLayout(tech=tech, layout=layout, placer=placer, router=router)
        assert lc.tech.unit_cell_height == num_tracks * 300

    @pytest.mark.parametrize("num_tracks", [7, 9, 12])
    def test_routing_graph_scales_with_tracks(self, project_root, num_tracks):
        """Grid2D produces more Y points for taller cells."""
        from lclayout.tech_util import load_tech_file
        from lclayout.layout.grid import Grid2D

        path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{num_tracks}t.yaml"
        tech = load_tech_file(str(path))

        grid = Grid2D(
            (int(tech.grid_offset_x), int(tech.grid_offset_y)),
            (int(tech.grid_offset_x + tech.unit_cell_width), int(tech.grid_offset_y + tech.unit_cell_height)),
            (int(tech.routing_grid_pitch_x), int(tech.routing_grid_pitch_y)),
        )
        y_values = sorted(set(y for _, y in grid))
        # More tracks → more Y routing points
        assert len(y_values) >= num_tracks - 2

    def test_9t_more_y_tracks_than_7t(self, project_root):
        """9T config produces more Y routing tracks than 7T."""
        from lclayout.tech_util import load_tech_file
        from lclayout.layout.grid import Grid2D

        def count_y_tracks(n):
            path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{n}t.yaml"
            tech = load_tech_file(str(path))
            grid = Grid2D(
                (int(tech.grid_offset_x), int(tech.grid_offset_y)),
                (int(tech.grid_offset_x + tech.unit_cell_width), int(tech.grid_offset_y + tech.unit_cell_height)),
                (int(tech.routing_grid_pitch_x), int(tech.routing_grid_pitch_y)),
            )
            return len(set(y for _, y in grid))

        assert count_y_tracks(9) > count_y_tracks(7)


@pytest.mark.integration
class TestMultiTrackConsistency:
    """Cross-track consistency tests."""

    @pytest.mark.parametrize("num_tracks", [6, 7, 9, 10, 12])
    def test_cell_height_matches_tracks(self, project_root, num_tracks):
        """Cell height equals num_tracks * track_pitch."""
        from lclayout.tech_util import load_tech_file
        path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{num_tracks}t.yaml"
        tech = load_tech_file(str(path))
        assert tech.unit_cell_height == num_tracks * tech.track_pitch

    @pytest.mark.parametrize("num_tracks", [6, 7, 9, 10, 12])
    def test_power_rail_within_cell(self, project_root, num_tracks):
        """Power rail width is less than cell height."""
        from lclayout.tech_util import load_tech_file
        path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{num_tracks}t.yaml"
        tech = load_tech_file(str(path))
        assert tech.power_rail_width < tech.unit_cell_height

    @pytest.mark.parametrize("num_tracks", [6, 7, 9, 10, 12])
    def test_transistor_offset_within_cell(self, project_root, num_tracks):
        """Transistor offset is within cell height."""
        from lclayout.tech_util import load_tech_file
        path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{num_tracks}t.yaml"
        tech = load_tech_file(str(path))
        assert 0 < tech.transistor_offset_y < tech.unit_cell_height

    def test_routing_graph_with_multi_track(self, project_root):
        """Routing graph can be built with multi-track config."""
        from lclayout.tech_util import load_tech_file
        from lclayout.layout.grid import Grid2D
        from lclayout.routing_graph import create_routing_graph_base

        path = project_root / "librecell-layout" / "examples" / "dummy_tech_9t.yaml"
        tech = load_tech_file(str(path))

        grid = Grid2D(
            (int(tech.grid_offset_x), int(tech.grid_offset_y)),
            (int(tech.grid_offset_x + tech.unit_cell_width), int(tech.grid_offset_y + tech.unit_cell_height)),
            (int(tech.routing_grid_pitch_x), int(tech.routing_grid_pitch_y)),
        )

        graph = create_routing_graph_base(grid, tech, tech.via_layers)
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() > 0


@pytest.mark.integration
class TestBackwardCompatibility:
    """Verify existing configs still work unchanged."""

    def test_baseline_dummy_tech_unchanged(self, dummy_tech):
        """Original dummy_tech (8T equivalent) still loads and works."""
        assert dummy_tech.unit_cell_height == 2400
        assert dummy_tech.routing_grid_pitch_y == 300
        assert dummy_tech.transistor_offset_y == 125

    def test_baseline_yaml_unchanged(self, project_root):
        """Original dummy_tech.yaml still loads (explicit height, no num_tracks)."""
        from lclayout.tech_util import load_tech_file
        path = project_root / "librecell-layout" / "examples" / "dummy_tech.yaml"
        tech = load_tech_file(str(path))
        assert tech.unit_cell_height == 2400
        assert tech.num_tracks is None
