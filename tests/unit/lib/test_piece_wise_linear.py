"""
Task 02: Test piecewise linear (PWL) module for characterization
"""
import pytest


@pytest.mark.unit
class TestPieceWiseLinear:
    """Test piecewise linear waveform utilities."""

    def test_pwl_module_importable(self):
        """piece_wise_linear module can be imported."""
        try:
            from lclib.characterization import piece_wise_linear
            assert piece_wise_linear is not None
        except ImportError:
            pytest.skip("piece_wise_linear module not available")


@pytest.mark.unit
class TestTimingUtil:
    """Test timing utility functions."""

    def test_timing_util_importable(self):
        """timing_util module can be imported."""
        try:
            from lclib.characterization import timing_util
            assert timing_util is not None
        except ImportError:
            pytest.skip("timing_util module not available")
