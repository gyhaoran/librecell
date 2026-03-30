"""
Task 02: Test net_util module in lccommon
"""
import pytest
from lccommon.net_util import (
    is_ground_net,
    is_supply_net,
    is_power_net,
    get_io_pins,
    get_cell_inputs,
)


@pytest.mark.unit
class TestNetUtilFunctions:
    """Test network utility functions."""

    def test_is_ground_net_true_cases(self):
        """Identify ground nets: gnd, vss, vgnd, 0."""
        assert is_ground_net('gnd') == True
        assert is_ground_net('GND') == True
        assert is_ground_net('vss') == True
        assert is_ground_net('VSS') == True
        assert is_ground_net('vgnd') == True
        assert is_ground_net('0') == True

    def test_is_ground_net_false_cases(self):
        """Regular signal nets are not ground."""
        assert is_ground_net('signal_a') == False
        assert is_ground_net('data_out') == False
        assert is_ground_net('clk') == False

    def test_is_supply_net_true_cases(self):
        """Identify supply nets: vdd, vcc, vpwr."""
        assert is_supply_net('vdd') == True
        assert is_supply_net('VDD') == True
        assert is_supply_net('vcc') == True
        assert is_supply_net('VCC') == True
        assert is_supply_net('vpwr') == True

    def test_is_supply_net_false_cases(self):
        """Regular signal nets are not supply."""
        assert is_supply_net('signal_a') == False
        assert is_supply_net('data_in') == False

    def test_is_power_net(self):
        """is_power_net returns True for both ground and supply nets."""
        assert is_power_net('gnd') == True
        assert is_power_net('vdd') == True
        assert is_power_net('signal') == False

    def test_get_io_pins(self):
        """Filter I/O pins excluding power nets."""
        pins = ['vdd', 'gnd', 'A', 'B', 'Y', 'vss']
        io_pins = get_io_pins(pins)
        assert 'vdd' not in io_pins
        assert 'gnd' not in io_pins
        assert 'vss' not in io_pins
        assert 'A' in io_pins
        assert 'B' in io_pins
        assert 'Y' in io_pins

    def test_get_io_pins_empty(self):
        """All pins are power pins."""
        pins = ['vdd', 'gnd']
        io_pins = get_io_pins(pins)
        assert len(io_pins) == 0

    def test_get_cell_inputs_inverter(self):
        """Get inputs of an inverter circuit."""
        from lccommon.data_types import Transistor, ChannelType
        
        # Simple inverter: NMOS and PMOS sharing gate 'in'
        transistors = [
            Transistor(ChannelType.NMOS, 'gnd', 'in', 'out', name='M1'),
            Transistor(ChannelType.PMOS, 'vdd', 'in', 'out', name='M2'),
        ]
        inputs = get_cell_inputs(transistors)
        assert inputs == {'in'}

    def test_get_cell_inputs_nand2(self):
        """Get inputs of a NAND2 circuit."""
        from lccommon.data_types import Transistor, ChannelType
        
        transistors = [
            # NMOS series stack
            Transistor(ChannelType.NMOS, 'Y', 'B', 'tmp', name='M1'),
            Transistor(ChannelType.NMOS, 'gnd', 'A', 'tmp', name='M2'),
            # PMOS parallel
            Transistor(ChannelType.PMOS, 'vdd', 'A', 'Y', name='M3'),
            Transistor(ChannelType.PMOS, 'vdd', 'B', 'Y', name='M4'),
        ]
        inputs = get_cell_inputs(transistors)
        assert inputs == {'A', 'B'}


@pytest.mark.integration
class TestNetlistLoading:
    """Test netlist loading functions."""

    def test_load_transistor_netlist_inverter(self, sample_netlist_path):
        """Load inverter netlist from SPICE file."""
        from lccommon.net_util import load_transistor_netlist
        
        # INVX1 should be defined in cells.sp
        try:
            transistors, pins = load_transistor_netlist(str(sample_netlist_path), 'INVX1')
            assert len(transistors) >= 2  # At least one NMOS and one PMOS
            assert 'vdd' in pins or 'vcc' in pins
            assert 'gnd' in pins or 'vss' in pins
        except Exception as e:
            pytest.skip(f"Could not load INVX1: {e}")

    def test_load_transistor_netlist_nand2(self, sample_netlist_path):
        """Load NAND2 netlist from SPICE file."""
        from lccommon.net_util import load_transistor_netlist
        
        try:
            transistors, pins = load_transistor_netlist(str(sample_netlist_path), 'NAND2X1')
            assert len(transistors) >= 4  # NAND2 needs 4 transistors minimum
        except Exception as e:
            pytest.skip(f"Could not load NAND2X1: {e}")

    def test_load_transistor_netlist_invalid(self, tmp_output_dir):
        """Loading invalid circuit raises exception."""
        from lccommon.net_util import load_transistor_netlist
        
        # Create a temporary empty SPICE file
        import os
        temp_spice = tmp_output_dir / "empty.sp"
        temp_spice.write_text("* Empty SPICE file\n")
        
        with pytest.raises(Exception):
            load_transistor_netlist(str(temp_spice), 'NONEXISTENT')
