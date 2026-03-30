"""
Task 02: Test data types in lccommon.data_types
"""
import pytest
from lccommon.data_types import Transistor, Cell, ChannelType


@pytest.mark.unit
class TestDataTypes:
    """Test core data types."""

    def test_transistor_creation(self):
        """Transistor correctly created with all parameters."""
        t = Transistor(
            channel_type=ChannelType.NMOS,
            source_net='source',
            gate_net='gate',
            drain_net='drain',
            channel_width=1.0,
            name='M1'
        )
        assert t.channel_type == ChannelType.NMOS
        assert t.source_net == 'source'
        assert t.gate_net == 'gate'
        assert t.drain_net == 'drain'
        assert t.channel_width == 1.0
        assert t.name == 'M1'

    def test_transistor_terminals(self):
        """Transistor terminals() returns correct tuple."""
        t = Transistor(
            channel_type=ChannelType.PMOS,
            source_net='vdd',
            gate_net='in',
            drain_net='out',
            channel_width=2.0,
            name='M1'
        )
        terminals = t.terminals()
        assert terminals == ('vdd', 'in', 'out')

    def test_transistor_flipped(self):
        """Transistor flipped() swaps source and drain."""
        t = Transistor(
            channel_type=ChannelType.NMOS,
            source_net='s',
            gate_net='g',
            drain_net='d',
            channel_width=1.0,
            name='M1'
        )
        f = t.flipped()
        assert f.source_net == 'd'
        assert f.drain_net == 's'
        assert f.gate_net == 'g'

    def test_transistor_equality(self):
        """Transistors with same parameters are equal."""
        t1 = Transistor(
            channel_type=ChannelType.NMOS,
            source_net='s',
            gate_net='g',
            drain_net='d',
            name='M1'
        )
        t2 = Transistor(
            channel_type=ChannelType.NMOS,
            source_net='s',
            gate_net='g',
            drain_net='d',
            name='M1'
        )
        assert t1 == t2
        assert hash(t1) == hash(t2)

    def test_transistor_inequality(self):
        """Transistors with different parameters are not equal."""
        t1 = Transistor(
            channel_type=ChannelType.NMOS,
            source_net='s1',
            gate_net='g',
            drain_net='d',
            name='M1'
        )
        t2 = Transistor(
            channel_type=ChannelType.NMOS,
            source_net='s2',
            gate_net='g',
            drain_net='d',
            name='M1'
        )
        assert t1 != t2

    def test_channel_type_enum(self):
        """ChannelType enum contains NMOS and PMOS."""
        assert ChannelType.NMOS.value == 1
        assert ChannelType.PMOS.value == 2

    def test_cell_structure(self):
        """Cell contains upper and lower rows."""
        cell = Cell(width=4)
        assert cell.width == 4
        assert len(cell.upper) == 4
        assert len(cell.lower) == 4
        assert all(x is None for x in cell.upper)
        assert all(x is None for x in cell.lower)

    def test_cell_place_transistor(self):
        """Transistors can be placed in cell."""
        cell = Cell(width=4)
        t = Transistor(
            channel_type=ChannelType.NMOS,
            source_net='s',
            gate_net='g',
            drain_net='d',
            name='M1'
        )
        cell.upper[0] = t
        assert cell.upper[0] == t

    def test_cell_get_transistor_locations(self):
        """get_transistor_locations returns all placed transistors."""
        cell = Cell(width=2)
        t1 = Transistor(ChannelType.NMOS, 's', 'g', 'd', name='M1')
        t2 = Transistor(ChannelType.PMOS, 's', 'g', 'd', name='M2')
        cell.lower[0] = t1
        cell.upper[1] = t2

        locations = cell.get_transistor_locations()
        assert len(locations) == 2

    def test_cell_repr(self):
        """Cell __repr__ produces readable output."""
        cell = Cell(width=2)
        t = Transistor(ChannelType.NMOS, 's', 'g', 'd', name='M1')
        cell.lower[0] = t
        repr_str = repr(cell)
        assert 'M1' in repr_str or 's' in repr_str
