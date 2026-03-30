"""
Task 03: Integration tests for YAML tech pipeline.
"""
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "librecell-layout" / "examples"


@pytest.mark.integration
class TestTechUtilDispatch:
    """tech_util.load_tech_file dispatches by extension."""

    def test_loads_yaml(self):
        """load_tech_file('.yaml') returns TechConfig."""
        from lclayout.tech_util import load_tech_file
        from lccommon.tech_config import TechConfig
        config = load_tech_file(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        assert isinstance(config, TechConfig)
        assert config.unit_cell_width == 400

    def test_loads_python(self):
        """load_tech_file('.py') returns TechConfig (converted)."""
        from lclayout.tech_util import load_tech_file
        from lccommon.tech_config import TechConfig
        config = load_tech_file(str(EXAMPLES_DIR / "dummy_tech.py"))
        assert isinstance(config, TechConfig)
        assert config.unit_cell_width == 400

    def test_python_and_yaml_same_spacing_graph(self):
        """spacing_graph built from Python and YAML configs are equivalent."""
        from lclayout.tech_util import load_tech_file, spacing_graph
        py_config = load_tech_file(str(EXAMPLES_DIR / "dummy_tech.py"))
        yaml_config = load_tech_file(str(EXAMPLES_DIR / "dummy_tech.yaml"))

        g_py = spacing_graph(py_config.min_spacing)
        g_yaml = spacing_graph(yaml_config.min_spacing)

        # Same edges (same layer pairs have spacing rules)
        assert set(g_py.edges()) == set(g_yaml.edges())
        # Same weights
        for u, v, data in g_py.edges(data=True):
            yaml_data = g_yaml.edges[u, v]
            assert data["min_spacing"] == yaml_data["min_spacing"], \
                f"Mismatch for ({u}, {v}): {data} vs {yaml_data}"


@pytest.mark.integration
class TestYamlTechWithLcLayout:
    """YAML tech config works with LcLayout."""

    def test_lclayout_init_with_yaml_tech(self):
        """LcLayout can be initialized with a YAML-loaded TechConfig."""
        from lclayout.tech_util import load_tech_file
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter
        import klayout.db as db

        config = load_tech_file(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        layout = db.Layout()
        placer = EulerPlacer()
        router = GraphRouter()

        lc = LcLayout(tech=config, layout=layout, placer=placer, router=router)
        assert lc.tech is config
        assert lc.tech.unit_cell_width == 400
        assert lc.tech.gate_length == 50

    def test_lclayout_init_with_python_tech(self):
        """LcLayout still works with Python tech (converted to TechConfig)."""
        from lclayout.tech_util import load_tech_file
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter
        import klayout.db as db

        config = load_tech_file(str(EXAMPLES_DIR / "dummy_tech.py"))
        layout = db.Layout()
        placer = EulerPlacer()
        router = GraphRouter()

        lc = LcLayout(tech=config, layout=layout, placer=placer, router=router)
        assert lc.tech.unit_cell_width == 400

    def test_legacy_via_layers_accessible(self):
        """TechConfig provides via_layers from layers.py (backward compat)."""
        from lclayout.tech_util import load_tech_file
        import networkx as nx
        config = load_tech_file(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        assert isinstance(config.via_layers, nx.Graph)
        assert config.via_layers.number_of_edges() > 0

    def test_legacy_layermap_accessible(self):
        """TechConfig provides layermap from layers.py (backward compat)."""
        from lclayout.tech_util import load_tech_file
        config = load_tech_file(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        assert isinstance(config.layermap, dict)
        assert "metal1" in config.layermap
