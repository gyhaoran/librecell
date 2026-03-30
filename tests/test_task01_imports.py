"""
Task 01: Test package structure and circular dependency fixes.
"""
import importlib
import sys
import pytest


@pytest.mark.unit
class TestPackageImports:
    """Test that imports work correctly after refactoring."""

    def test_common_no_layout_dependency(self):
        """librecell-common should not depend on librecell-layout
        (core types are now in lccommon).
        """
        import lccommon.data_types
        assert hasattr(lccommon.data_types, 'Transistor')
        assert hasattr(lccommon.data_types, 'ChannelType')
        assert hasattr(lccommon.data_types, 'Cell')

    def test_layout_backward_compat(self):
        """lclayout.data_types should still work (backward compatibility re-export)."""
        from lclayout.data_types import Transistor, ChannelType, Cell
        assert Transistor is not None
        assert ChannelType is not None
        assert Cell is not None

    def test_lclib_uses_lccommon_types(self):
        """lclib imports types from lccommon, not lclayout.data_types directly."""
        import lclib.logic.functional_abstraction as fa
        # Verify module can be imported
        assert hasattr(fa, 'ChannelType')

    def test_common_data_types_independent(self):
        """lccommon.data_types can be imported independently without triggering lclayout import."""
        # Clear any cached imports
        mods_to_clear = [k for k in sys.modules.keys()
                        if k == 'lclayout' or k.startswith('lclayout.')]
        for mod_name in mods_to_clear:
            del sys.modules[mod_name]

        # Also clear lccommon to force fresh import
        if 'lccommon' in sys.modules:
            del sys.modules['lccommon']
        if 'lccommon.data_types' in sys.modules:
            del sys.modules['lccommon.data_types']

        # Re-import lccommon.data_types
        importlib.reload(importlib.import_module('lccommon.data_types'))

        # Check that lclayout was not imported
        leaked = [k for k in sys.modules if k == 'lclayout' or k.startswith('lclayout.')]
        assert len(leaked) == 0, f"lclayout should not be imported, but found: {leaked}"

    def test_transistor_can_be_created(self):
        """Test that Transistor can be instantiated."""
        from lccommon.data_types import Transistor, ChannelType

        t = Transistor(
            channel_type=ChannelType.NMOS,
            source_net='s',
            gate_net='g',
            drain_net='d',
            channel_width=1.0,
            name='M1'
        )
        assert t.channel_type == ChannelType.NMOS
        assert t.source_net == 's'
        assert t.gate_net == 'g'
        assert t.drain_net == 'd'
        assert t.channel_width == 1.0

    def test_cell_can_be_created(self):
        """Test that Cell can be instantiated."""
        from lccommon.data_types import Cell, Transistor, ChannelType

        cell = Cell(width=4)
        assert cell.width == 4
        assert len(cell.upper) == 4
        assert len(cell.lower) == 4

    def test_channel_type_enum(self):
        """Test ChannelType enum values."""
        from lccommon.data_types import ChannelType

        assert ChannelType.NMOS.value == 1
        assert ChannelType.PMOS.value == 2
