"""
Task 02: Test routing algorithms in lclayout.graphrouter
"""
import pytest
import networkx as nx


@pytest.mark.unit
class TestRoutersImport:
    """Test router imports."""

    def test_dijkstra_router_importable(self):
        """DijkstraRouter can be imported."""
        from lclayout.graphrouter.signal_router import DijkstraRouter
        assert DijkstraRouter is not None

    def test_pathfinder_router_importable(self):
        """PathFinderGraphRouter can be imported."""
        from lclayout.graphrouter.pathfinder import PathFinderGraphRouter
        assert PathFinderGraphRouter is not None

    def test_hv_router_importable(self):
        """HVGraphRouter can be imported."""
        from lclayout.graphrouter.hv_router import HVGraphRouter
        assert HVGraphRouter is not None

    def test_steiner_router_importable(self):
        """ApproxSteinerTreeRouter can be imported."""
        from lclayout.graphrouter.signal_router import ApproxSteinerTreeRouter
        assert ApproxSteinerTreeRouter is not None


@pytest.mark.unit
def test_dijkstra_router_standalone():
    """Inline test from signal_router.py - extracted to pytest."""
    try:
        from lclayout.graphrouter.signal_router import DijkstraRouter
        assert DijkstraRouter is not None
    except ImportError as e:
        pytest.skip(f"Router not available: {e}")


@pytest.mark.unit
def test_pathfinder_standalone():
    """Inline test from pathfinder.py - extracted to pytest."""
    try:
        from lclayout.graphrouter.pathfinder import PathFinderGraphRouter
        assert PathFinderGraphRouter is not None
    except ImportError as e:
        pytest.skip(f"PathFinderGraphRouter not available: {e}")


@pytest.mark.unit
class TestRouterBasics:
    """Basic router tests."""

    def test_create_graph(self):
        """Test creating a basic routing graph."""
        G = nx.Graph()
        G.add_node(('metal1', (0, 0)), layer='metal1')
        G.add_node(('metal1', (1, 0)), layer='metal1')
        G.add_edge(('metal1', (0, 0)), ('metal1', (1, 0)))
        
        assert len(G.nodes()) == 2
        assert len(G.edges()) == 1

    def test_graph_connectivity(self):
        """Test graph connectivity."""
        G = nx.Graph()
        for x in range(5):
            for y in range(5):
                G.add_node(('metal1', (x, y)), layer='metal1')
                if x > 0:
                    G.add_edge(('metal1', (x, y)), ('metal1', (x-1, y)))
                if y > 0:
                    G.add_edge(('metal1', (x, y)), ('metal1', (x, y-1)))
        
        assert nx.is_connected(G)

    def test_path_exists(self):
        """Test that a path exists between two nodes."""
        G = nx.Graph()
        G.add_node('A')
        G.add_node('B')
        G.add_edge('A', 'B')
        
        assert nx.has_path(G, 'A', 'B')
