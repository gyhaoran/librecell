"""
Task 02: Test CMOS synthesis module
"""
import pytest
import sympy
import networkx as nx


@pytest.mark.unit
class TestCmosSynthImports:
    """Test cmos_synth module imports."""

    def test_cmos_synth_module_importable(self):
        """cmos_synth module can be imported."""
        from lclib.logic.cmos_synth import (
            synthesize_circuit,
            synthesize_minimal_circuit,
            synthesize_transistors,
            formula_from_string,
            enumerate_all_multi_graphs
        )
        assert synthesize_circuit is not None

    def test_formula_from_string_function_exists(self):
        """formula_from_string function exists."""
        from lclib.logic.cmos_synth import formula_from_string
        assert callable(formula_from_string)


@pytest.mark.unit
class TestFormulaConversion:
    """Test boolean formula parsing and conversion."""

    def test_parse_simple_formula(self):
        """Parse simple boolean formula."""
        from lclib.logic.cmos_synth import formula_from_string
        a = sympy.Symbol('a')
        result = formula_from_string('a')
        assert result == a

    def test_parse_and_formula(self):
        """Parse AND formula."""
        from lclib.logic.cmos_synth import formula_from_string
        result = formula_from_string('a & b')
        a, b = sympy.symbols('a b')
        expected = a & b
        assert result == expected

    def test_parse_or_formula(self):
        """Parse OR formula."""
        from lclib.logic.cmos_synth import formula_from_string
        result = formula_from_string('a | b')
        a, b = sympy.symbols('a b')
        expected = a | b
        assert result == expected


@pytest.mark.unit
class TestCircuitSynthesis:
    """Test CMOS circuit synthesis."""

    def test_synthesize_inverter(self):
        """Synthesize inverter circuit."""
        from lclib.logic.cmos_synth import synthesize_circuit
        a = sympy.symbols('a')
        cmos = synthesize_circuit(~a)
        assert cmos is not None
        assert isinstance(cmos, nx.MultiGraph)
        # Inverter has 2 transistors (1 NMOS, 1 PMOS)
        assert cmos.number_of_edges() == 2

    def test_synthesize_nand_gate(self):
        """Synthesize NAND gate."""
        from lclib.logic.cmos_synth import synthesize_circuit
        a, b = sympy.symbols('a b')
        nand = ~(a & b)
        cmos = synthesize_circuit(nand)
        assert cmos is not None
        assert isinstance(cmos, nx.MultiGraph)
        assert cmos.number_of_edges() >= 2


@pytest.mark.unit
class TestMinimalCircuitSynthesis:
    """Test minimal circuit synthesis."""

    def test_synthesize_minimal_inverter(self):
        """Synthesize minimal inverter."""
        from lclib.logic.cmos_synth import synthesize_minimal_circuit
        a = sympy.symbols('a')
        cmos = synthesize_minimal_circuit(~a)
        assert cmos is not None
        assert isinstance(cmos, nx.MultiGraph)

    def test_synthesize_minimal_nand(self):
        """Synthesize minimal NAND gate."""
        from lclib.logic.cmos_synth import synthesize_minimal_circuit
        a, b = sympy.symbols('a b')
        nand = sympy.Not(a & b)
        cmos = synthesize_minimal_circuit(nand)
        assert cmos is not None
        assert isinstance(cmos, nx.MultiGraph)


@pytest.mark.unit
class TestTransistorGeneration:
    """Test transistor network generation."""

    def test_synthesize_transistors_returns_list(self):
        """synthesize_transistors returns a list."""
        from lclib.logic.cmos_synth import synthesize_transistors
        a = sympy.symbols('a')
        transistors = synthesize_transistors(~a)
        assert transistors is not None
        assert isinstance(transistors, list)
        assert len(transistors) >= 2


@pytest.mark.unit
class TestGraphEnumeration:
    """Test graph enumeration utilities."""

    def test_enumerate_single_edge_graph(self):
        """Enumerate graphs with 0 extra nodes."""
        from lclib.logic.cmos_synth import enumerate_all_multi_graphs
        graphs = enumerate_all_multi_graphs(0, 0)
        assert graphs is not None
        assert isinstance(graphs, list)

    def test_enumerate_small_graphs(self):
        """Enumerate small graphs."""
        from lclib.logic.cmos_synth import enumerate_all_multi_graphs
        graphs = enumerate_all_multi_graphs(2, 1)
        assert graphs is not None
        assert len(graphs) > 0

    def test_enumerated_graphs_are_multigraphs(self):
        """Enumerated results are MultiGraph instances."""
        from lclib.logic.cmos_synth import enumerate_all_multi_graphs
        graphs = enumerate_all_multi_graphs(1, 1)
        for g in graphs:
            assert isinstance(g, nx.MultiGraph)
