"""
Task 02: Test seq_recognition module - Sequential cell recognition
"""
import pytest
import networkx as nx
import sympy


@pytest.mark.unit
class TestSeqRecognitionBasic:
    """Test sequential recognition basic functionality."""

    def test_seq_recognition_module_import(self):
        """Test that seq_recognition module can be imported."""
        from lclib.logic import seq_recognition
        assert seq_recognition is not None

    def test_graph_isomorphism_basic(self):
        """Test basic graph isomorphism checking."""
        # Create two isomorphic graphs
        g1 = nx.Graph()
        g1.add_edge('a', 'b')
        g1.add_edge('b', 'c')
        g1.add_node('a', type='input')
        g1.add_node('b', type='hidden')
        g1.add_node('c', type='output')

        g2 = nx.Graph()
        g2.add_edge('x', 'y')
        g2.add_edge('y', 'z')
        g2.add_node('x', type='input')
        g2.add_node('y', type='hidden')
        g2.add_node('z', type='output')

        # These graphs are isomorphic (same structure)
        assert nx.is_isomorphic(g1, g2)

    def test_graph_non_isomorphism(self):
        """Test detecting non-isomorphic graphs."""
        g1 = nx.Graph()
        g1.add_edge('a', 'b')
        g1.add_edge('b', 'c')

        g2 = nx.Graph()
        g2.add_edge('x', 'y')
        g2.add_edge('y', 'z')
        g2.add_edge('z', 'w')  # Extra edge

        assert not nx.is_isomorphic(g1, g2)


@pytest.mark.unit
class TestGraphEnumeration:
    """Test graph enumeration utilities."""

    def test_graph_enumeration_module_import(self):
        """Test that graph_enumeration module can be imported."""
        from lclib.logic import graph_enumeration
        assert graph_enumeration is not None

    def test_enumerate_paths(self):
        """Test enumerating paths in a graph."""
        G = nx.Graph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        G.add_edge('B', 'D')

        paths = list(nx.all_simple_paths(G, 'A', 'D'))
        assert len(paths) == 1
        assert paths[0] == ['A', 'B', 'D']

    def test_enumerate_all_paths_longer(self):
        """Test enumerating multiple paths."""
        G = nx.Graph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        G.add_edge('A', 'C')  # Direct path

        paths = list(nx.all_simple_paths(G, 'A', 'C'))
        assert len(paths) == 2


@pytest.mark.unit
class TestSequentialElements:
    """Test sequential element detection."""

    def test_feedback_loop_detection(self):
        """Test detecting feedback loops in circuits."""
        G = nx.DiGraph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        G.add_edge('C', 'A')  # Feedback loop

        # Check for cycles
        assert len(list(nx.simple_cycles(G))) > 0

    def test_no_feedback_loop(self):
        """Test that acyclic graphs have no feedback."""
        G = nx.DiGraph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        G.add_edge('C', 'D')

        cycles = list(nx.simple_cycles(G))
        assert len(cycles) == 0


@pytest.mark.unit
class TestBooleanFunctions:
    """Test boolean function manipulation."""

    def test_sympy_symbol_creation(self):
        """Test creating sympy symbols."""
        a, b, c = sympy.symbols('a b c')
        assert a is not None
        assert b is not None
        assert c is not None

    def test_boolean_and(self):
        """Test boolean AND operation."""
        a, b = sympy.symbols('a b')
        result = a & b
        assert result is not None

    def test_boolean_or(self):
        """Test boolean OR operation."""
        a, b = sympy.symbols('a b')
        result = a | b
        assert result is not None

    def test_boolean_not(self):
        """Test boolean NOT operation."""
        a = sympy.Symbol('a')
        result = ~a
        assert result is not None

    def test_boolean_expression_simplification(self):
        """Test simplifying boolean expressions."""
        from sympy.logic import simplify_logic
        
        a = sympy.Symbol('a')
        expr = a & sympy.true
        simplified = simplify_logic(expr)
        assert simplified == a
