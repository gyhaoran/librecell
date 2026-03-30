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
    """Load the dummy_tech.py configuration as TechConfig."""
    from lclayout.tech_util import load_tech_file
    return load_tech_file(str(dummy_tech_path))


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
        Transistor(
            channel_type=ChannelType.NMOS,
            source_net='gnd',
            gate_net='in',
            drain_net='out',
            channel_width=1.0,
            name='M1'
        ),
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
def nand2_transistors():
    """Return NAND2 transistor list for testing."""
    from lccommon.data_types import Transistor, ChannelType
    return [
        # NMOS series stack
        Transistor(ChannelType.NMOS, 'Y', 'B', 'tmp', channel_width=0.5, name='M1'),
        Transistor(ChannelType.NMOS, 'gnd', 'A', 'tmp', channel_width=0.5, name='M2'),
        # PMOS parallel
        Transistor(ChannelType.PMOS, 'vdd', 'A', 'Y', channel_width=0.5, name='M3'),
        Transistor(ChannelType.PMOS, 'vdd', 'B', 'Y', channel_width=0.5, name='M4'),
    ]


@pytest.fixture
def klayout_layout():
    """Create a KLayout Layout object for testing."""
    import klayout.db as db
    layout = db.Layout()
    return layout


@pytest.fixture
def euler_placer():
    """Create an EulerPlacer instance for testing."""
    from lclayout.place.euler_placer import EulerPlacer
    return EulerPlacer()


@pytest.fixture
def graph_router():
    """Create a GraphRouter instance for testing."""
    from lclayout.graphrouter.graphrouter import RoutingGraph
    return RoutingGraph()


@pytest.fixture
def lclayout_instance(dummy_tech, klayout_layout):
    """Create a properly configured LcLayout instance."""
    from lclayout.standalone import LcLayout
    from lclayout.place.euler_placer import EulerPlacer
    from lclayout.graphrouter.graphrouter import GraphRouter
    
    placer = EulerPlacer()
    router = GraphRouter()
    
    layout = LcLayout(
        tech=dummy_tech,
        layout=klayout_layout,
        placer=placer,
        router=router
    )
    return layout


@pytest.fixture
def tmp_output_dir():
    """Create a temporary output directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def tech_config(dummy_tech):
    """Return a dict-like object with tech config attributes from dummy_tech module."""
    class TechConfig:
        def __init__(self, module):
            self.unit_cell_width = getattr(module, 'unit_cell_width', None)
            self.routing_grid_pitch_x = getattr(module, 'routing_grid_pitch_x', None)
            self.db_unit = getattr(module, 'db_unit', None)
            self.unit_cell_height = getattr(module, 'unit_cell_height', None)
    return TechConfig(dummy_tech)
