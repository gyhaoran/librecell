"""
Task 02: Test routing algorithms
"""
import pytest
import networkx as nx


@pytest.mark.unit
class TestRouterImports:
    """Test router module imports."""

    def test_signal_router_import(self):
        """Signal router modules can be imported."""
        from lclayout.graphrouter.signal_router import DijkstraRouter
        assert DijkstraRouter is not None

    def test_dijkstra_instantiation(self):
        """DijkstraRouter can be instantiated."""
        from lclayout.graphrouter.signal_router import DijkstraRouter
        router = DijkstraRouter()
        assert router is not None


@pytest.mark.unit
class TestNetworkXGraph:
    """Test NetworkX graph functionality."""

    def test_graph_creation(self):
        """NetworkX graph creation works."""
        G = nx.Graph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        assert G.has_node('A')
        assert G.has_node('B')
        assert G.has_node('C')

    def test_shortest_path(self):
        """NetworkX shortest path works."""
        G = nx.Graph()
        G.add_edge('A', 'B', weight=1)
        G.add_edge('B', 'C', weight=1)
        G.add_edge('C', 'D', weight=1)
        
        path = nx.shortest_path(G, 'A', 'D')
        assert path == ['A', 'B', 'C', 'D']

    def test_path_length(self):
        """NetworkX path length calculation works."""
        G = nx.Graph()
        G.add_edge('A', 'B', weight=1)
        G.add_edge('B', 'C', weight=1)
        
        length = nx.shortest_path_length(G, 'A', 'C')
        assert length == 2

    def test_dijkstra_path_length(self):
        """NetworkX Dijkstra works."""
        G = nx.Graph()
        G.add_edge('A', 'B', weight=1)
        G.add_edge('B', 'C', weight=1)
        G.add_edge('C', 'D', weight=1)
        
        length = nx.dijkstra_path_length(G, 'A', 'D')
        assert length == 3
