"""
Test configuration and shared fixtures for LibreCell tests.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest


# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def dummy_tech_path(project_root):
    """Return path to dummy_tech.py example file."""
    return project_root / "librecell-layout" / "examples" / "dummy_tech.py"


@pytest.fixture(scope="session")
def dummy_tech(dummy_tech_path):
    """Load the dummy_tech.py configuration module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("dummy_tech", dummy_tech_path)
    dummy_tech_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dummy_tech_module)
    return dummy_tech_module


@pytest.fixture(scope="session")
def shared_netlist_path(project_root):
    """Return path to shared netlist file in fixtures directory."""
    return project_root / "tests" / "fixtures" / "netlists" / "cells.sp"


@pytest.fixture(scope="session")
def sample_netlist_path(project_root):
    """Return path to sample netlist (from librecell-lib test_data)."""
    return project_root / "librecell-lib" / "test_data" / "cells.sp"


@pytest.fixture
def inverter_transistors():
    """Return a simple inverter transistor list for testing."""
    from lccommon.data_types import Transistor, ChannelType
    return [
        # NMOS
        Transistor(
            channel_type=ChannelType.NMOS,
            source_net='gnd',
            gate_net='in',
            drain_net='out',
            channel_width=1.0,
            name='M1'
        ),
        # PMOS
        Transistor(
            channel_type=ChannelType.PMOS,
            source_net='vdd',
            gate_net='in',
            drain_net='out',
            channel_width=2.0,
            name='M2'
        ),
    ]


@pytest.fixture
def tmp_output_dir():
    """Create a temporary output directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def tech_config(dummy_tech):
    """Return a dict-like object with tech config attributes from dummy_tech module."""
    # Create a simple namespace with the key attributes from dummy_tech
    class TechConfig:
        def __init__(self, module):
            self.unit_cell_width = getattr(module, 'unit_cell_width', None)
            self.routing_grid_pitch_x = getattr(module, 'routing_grid_pitch_x', None)
            self.db_unit = getattr(module, 'db_unit', None)
            self.unit_cell_height = getattr(module, 'unit_cell_height', None)
    return TechConfig(dummy_tech)
