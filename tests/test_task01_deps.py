"""
Task 01: Test dependency configuration.
"""
import pytest


@pytest.mark.unit
class TestDependencies:
    """Test that required packages are importable."""

    def test_all_packages_importable(self):
        """All three sub-packages can be imported."""
        import lccommon
        import lclayout
        import lclib

        assert lccommon is not None
        assert lclayout is not None
        assert lclib is not None

    def test_dev_dependencies(self):
        """Development dependencies are available."""
        import pytest
        assert pytest is not None

        # Check optional coverage
        try:
            import coverage
        except ImportError:
            pytest.skip("coverage not installed")

    def test_lccommon_core_types(self):
        """lccommon.data_types contains core types."""
        from lccommon import data_types
        assert hasattr(data_types, 'Transistor')
        assert hasattr(data_types, 'ChannelType')
        assert hasattr(data_types, 'Cell')

    def test_net_util_import(self):
        """lccommon.net_util can be imported after refactoring."""
        from lccommon import net_util
        assert hasattr(net_util, 'load_transistor_netlist')

    def test_lclayout_standalone(self):
        """lclayout.standalone can be imported."""
        from lclayout import standalone
        assert hasattr(standalone, 'LcLayout')

    def test_lclib_modules_importable(self):
        """lclib modules can be imported."""
        from lclib.logic import functional_abstraction
        from lclib.logic import seq_recognition
        from lclib.logic import cmos_sim

        assert functional_abstraction is not None
        assert seq_recognition is not None
        assert cmos_sim is not None
