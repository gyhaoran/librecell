"""
Task 06: Tests for Transistor voltage_domain and is_high_voltage attributes.
"""
import pytest
from lccommon.data_types import Transistor, ChannelType


def test_transistor_voltage_domain_default():
    """Transistor defaults to 'default' voltage domain."""
    t = Transistor(ChannelType.NMOS, 'gnd', 'in', 'out', channel_width=1.0, name='M1')
    assert t.voltage_domain == 'default'


def test_transistor_is_hv_default():
    """Transistor defaults to non-high-voltage."""
    t = Transistor(ChannelType.NMOS, 'gnd', 'in', 'out', channel_width=1.0, name='M1')
    assert t.is_high_voltage is False


def test_transistor_voltage_domain():
    """Transistor can be assigned a voltage domain."""
    t = Transistor(
        ChannelType.PMOS, 'vddh', 'in', 'out',
        channel_width=2.0, name='M2',
        voltage_domain='io_hv'
    )
    assert t.voltage_domain == 'io_hv'


def test_transistor_is_hv():
    """Transistor can be marked as high voltage."""
    t = Transistor(
        ChannelType.NMOS, 'gnd', 'in', 'out',
        channel_width=1.0, name='M3',
        is_high_voltage=True
    )
    assert t.is_high_voltage is True


def test_transistor_hv_hash_differs():
    """Two transistors differing only in HV flag have different hashes."""
    t_normal = Transistor(ChannelType.NMOS, 'gnd', 'in', 'out', channel_width=1.0, name='M1')
    t_hv = Transistor(
        ChannelType.NMOS, 'gnd', 'in', 'out',
        channel_width=1.0, name='M1',
        is_high_voltage=True
    )
    assert hash(t_normal) != hash(t_hv)
    assert t_normal != t_hv


def test_transistor_hv_equality():
    """Two HV transistors with same params are equal."""
    t1 = Transistor(
        ChannelType.NMOS, 'gnd', 'in', 'out',
        channel_width=1.0, name='M1',
        voltage_domain='hv', is_high_voltage=True
    )
    t2 = Transistor(
        ChannelType.NMOS, 'gnd', 'in', 'out',
        channel_width=1.0, name='M1',
        voltage_domain='hv', is_high_voltage=True
    )
    assert t1 == t2


def test_transistor_flipped_preserves_hv():
    """Flipping a transistor preserves HV attributes."""
    t = Transistor(
        ChannelType.NMOS, 'gnd', 'in', 'out',
        channel_width=1.0, name='M1',
        voltage_domain='io_hv', is_high_voltage=True
    )
    t_flip = t.flipped()
    assert t_flip.voltage_domain == 'io_hv'
    assert t_flip.is_high_voltage is True
