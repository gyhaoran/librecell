"""
Task 02: Test spice_parser module in lccommon
"""
import pytest
from lccommon.spice_parser import parse_spice, MOSFET, Subckt, Resistor, Capacitor, Include


@pytest.mark.unit
class TestSpiceParser:
    """Test SPICE parser functionality."""

    def test_parse_subcircuit(self):
        """Parse .subckt definition."""
        input_text = """
.subckt inv1 in out vcc gnd
MN1 out in gnd gnd NMOS L=0.35U W=2.0U
MP2 out in vcc vcc PMOS L=0.35U W=4.0U
.ends inv1
"""
        parsed = parse_spice(input_text)
        
        subckts = [e for e in parsed if isinstance(e, Subckt)]
        assert len(subckts) >= 1
        sub = subckts[0]
        assert sub.name == 'inv1'
        assert len(sub.ports) >= 4

    def test_parse_include(self):
        """Parse .include directive."""
        input_text = ".include mylibrary.sp\n.subckt empty\n.ends"
        parsed = parse_spice(input_text)
        
        includes = [e for e in parsed if isinstance(e, Include)]
        assert len(includes) >= 1

    def test_parse_full_netlist(self):
        """Parse complete standard cell netlist."""
        input_text = """
.subckt inv1 in out vcc gnd
MN1 out in gnd gnd NMOS L=0.35U W=2.0U
MP2 out in vcc vcc PMOS L=0.35U W=4.0U
.ends inv1
.subckt nand2 a b y vdd gnd
MN1 y a tmp gnd NMOS
MN2 tmp b gnd gnd NMOS
MP1 vdd a y vdd PMOS
MP2 y b vdd vdd PMOS
.ends nand2
"""
        parsed = parse_spice(input_text)
        subckts = [e for e in parsed if isinstance(e, Subckt)]
        assert len(subckts) >= 2


@pytest.mark.unit
def test_spice_parser_legacy():
    """Legacy inline test from spice_parser.py."""
    input_text = """
.subckt testCircuit in1 in2 out1
R1 gnd vdd 4.7
M1 gnd in1 vdd gnd nmos
.ends testCircuit
.subckt inv1 in out vcc gnd
MN1 out in gnd gnd NMOS
MP2 out in vcc vcc PMOS
.ends inv1
"""
    parsed = parse_spice(input_text)
    assert len(parsed) > 0
    subckts = [p for p in parsed if isinstance(p, Subckt)]
    assert len(subckts) >= 2
