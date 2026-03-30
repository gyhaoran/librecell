"""
Task 02: Test CMOS simulation module
"""
import pytest
import sympy


@pytest.mark.unit
class TestCmosSimBasic:
    """Test CMOS simulation module imports."""

    def test_cmos_sim_module_import(self):
        """cmos_sim module can be imported."""
        from lclib.logic import cmos_sim
        assert cmos_sim is not None

    def test_sympy_logic_operations(self):
        """Sympy can perform basic logic operations."""
        a = sympy.Symbol('a')
        b = sympy.Symbol('b')
        
        # Test NOT
        not_a = ~a
        assert not_a is not None
        
        # Test AND
        a_and_b = a & b
        assert a_and_b is not None
        
        # Test OR
        a_or_b = a | b
        assert a_or_b is not None

    def test_sympy_symbol_creation(self):
        """Sympy symbols can be created."""
        a = sympy.Symbol('a')
        assert a is not None
        
        a, b = sympy.symbols('a b')
        assert a is not None
        assert b is not None

    def test_sympy_simplify_logic(self):
        """Sympy simplify_logic function works."""
        a, b = sympy.symbols('a b')
        
        # Test DNF conversion
        expr = (a & b) | (~a & ~b)
        dnf = sympy.simplify_logic(expr, form='dnf')
        assert dnf is not None
        
        # Test CNF conversion
        cnf = sympy.simplify_logic(expr, form='cnf')
        assert cnf is not None
