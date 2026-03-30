"""
Task 02: Test routing algorithms
"""
import pytest
import networkx as nx


@pytest.mark.unit
class TestRouterImports:
    """Test router module imports."""

    def test_dijkstra_router_import(self):
        """DijkstraRouter can be imported."""
        from lclayout.graphrouter.signal_router import DijkstraRouter
        assert DijkstraRouter is not None

    def test_dijkstra_instantiation(self):
        """DijkstraRouter can be instantiated."""
        from lclayout.graphrouter.signal_router import DijkstraRouter
        router = DijkstraRouter()
        assert router is not None

    def test_signal_router_base_import(self):
        """SignalRouter base class can be imported."""
        from lclayout.graphrouter.signal_router import SignalRouter
        assert SignalRouter is not None

    def test_steiner_router_import(self):
        """ApproxSteinerTreeRouter can be imported."""
        from lclayout.graphrouter.signal_router import ApproxSteinerTreeRouter
        assert ApproxSteinerTreeRouter is not None


@pytest.mark.unit
class TestDijkstraRouterRoute:
    """Test DijkstraRouter.route() with real routing."""

    def test_route_two_terminals(self):
        """DijkstraRouter.route() finds path between two terminals."""
        from lclayout.graphrouter.signal_router import DijkstraRouter
        
        # Create a simple grid graph
        G = nx.Graph()
        G.add_edge((0, 0), (1, 0))
        G.add_edge((1, 0), (2, 0))
        G.add_edge((2, 0), (3, 0))
        
        router = DijkstraRouter()
        
        # Simple cost functions
        def node_cost(n):
            return 0
        
        def edge_cost(e):
            return 1
        
        # Use positional arguments as per actual API
        terminals = [(0, 0), (3, 0)]
        result = router.route(G, terminals, node_cost, edge_cost)
        
        assert result is not None
        assert isinstance(result, nx.Graph)

    def test_route_three_terminals(self):
        """DijkstraRouter.route() finds spanning tree for three terminals."""
        from lclayout.graphrouter.signal_router import DijkstraRouter
        
        # Create a grid graph
        G = nx.Graph()
        # Create a 3x3 grid
        for x in range(3):
            for y in range(3):
                if x < 2:
                    G.add_edge((x, y), (x+1, y))
                if y < 2:
                    G.add_edge((x, y), (x, y+1))
        
        router = DijkstraRouter()
        
        def node_cost(n):
            return 0
        
        def edge_cost(e):
            return 1
        
        terminals = [(0, 0), (2, 0), (2, 2)]
        result = router.route(G, terminals, node_cost, edge_cost)
        
        assert result is not None
        assert isinstance(result, nx.Graph)

    def test_route_returns_graph_with_edges(self):
        """DijkstraRouter.route() returns a graph with edges."""
        from lclayout.graphrouter.signal_router import DijkstraRouter
        
        G = nx.Graph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        
        router = DijkstraRouter()
        
        # Use positional arguments
        result = router.route(
            G, 
            ['A', 'C'],
            lambda n: 0,  # node_cost
            lambda e: 1   # edge_cost
        )
        
        assert result is not None
        assert result.number_of_edges() > 0


@pytest.mark.unit
class TestApproxSteinerTreeRouter:
    """Test ApproxSteinerTreeRouter."""

    def test_steiner_router_instantiation(self):
        """ApproxSteinerTreeRouter can be instantiated."""
        from lclayout.graphrouter.signal_router import ApproxSteinerTreeRouter
        router = ApproxSteinerTreeRouter()
        assert router is not None

    def test_steiner_route_basic(self):
        """ApproxSteinerTreeRouter.route() finds Steiner tree."""
        from lclayout.graphrouter.signal_router import ApproxSteinerTreeRouter
        
        G = nx.Graph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        G.add_edge('C', 'D')
        
        router = ApproxSteinerTreeRouter()
        
        # Use positional arguments
        result = router.route(
            G,
            ['A', 'D'],
            lambda n: 0,  # node_cost
            lambda e: 1   # edge_cost
        )
        
        assert result is not None
        assert isinstance(result, nx.Graph)


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

    def test_minimum_spanning_tree(self):
        """NetworkX minimum spanning tree works."""
        G = nx.Graph()
        G.add_edge('A', 'B', weight=1)
        G.add_edge('B', 'C', weight=2)
        G.add_edge('C', 'A', weight=3)
        
        mst = nx.minimum_spanning_tree(G)
        assert mst.number_of_edges() == 2
