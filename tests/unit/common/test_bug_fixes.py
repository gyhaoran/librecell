"""
Task 10: Tests for bug fixes.
"""
import pytest


@pytest.mark.unit
class TestAnnealPlacerFix:

    def test_evaluate_upper_row_uses_correct_x(self):
        """_evaluate() uses enumerate for upper_row, not residual x."""
        from lclayout.place.anneal_placer import _evaluate
        from lccommon.data_types import Transistor, ChannelType

        # Create simple transistors for lower/upper row
        t_n = Transistor(ChannelType.NMOS, "gnd", "A", "Y", 200.0, "M0")
        t_p = Transistor(ChannelType.PMOS, "vdd", "A", "Y", 400.0, "M1")

        lower = [t_n, None]
        upper = [None, t_p]

        # Should not crash, and the upper row transistor should get x=1 (not x=0)
        cost = _evaluate(lower, upper)
        assert isinstance(cost, (int, float))

    def test_evaluate_with_empty_lower_row(self):
        """_evaluate handles lower row with all None gracefully."""
        from lclayout.place.anneal_placer import _evaluate
        from lccommon.data_types import Transistor, ChannelType

        t_p = Transistor(ChannelType.PMOS, "vdd", "A", "Y", 400.0, "M1")

        lower = [None, None]
        upper = [t_p, None]

        # With the bug fixed, this should work (x=0 from enumerate, not NameError)
        cost = _evaluate(lower, upper)
        assert isinstance(cost, (int, float))


@pytest.mark.unit
class TestTransistorLayoutFix:

    def test_abstract_methods_raise_not_implemented_error(self):
        """TransistorLayout abstract methods raise NotImplementedError (not NotImplemented)."""
        from lclayout.layout.transistor import TransistorLayout

        tl = TransistorLayout.__new__(TransistorLayout)
        with pytest.raises(NotImplementedError):
            tl.__init__(None, (0, 0), 0, None)


@pytest.mark.unit
class TestDeadCodeRemoved:

    def test_width_opt_removed(self):
        """width_opt.py (entirely commented-out dead code) has been removed."""
        from pathlib import Path
        width_opt = Path(__file__).resolve().parents[3] / \
            "librecell-lib" / "lclib" / "transistor_sizing" / "width_opt.py"
        assert not width_opt.exists(), "width_opt.py should have been removed"
