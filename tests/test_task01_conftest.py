"""
Task 01: Test conftest.py fixtures specifically.
"""
import pytest


@pytest.mark.unit
class TestConftestFixtures:
    """Test conftest.py fixtures."""

    def test_dummy_tech_fixture(self, dummy_tech):
        """dummy_tech fixture returns valid tech object."""
        # dummy_tech is a module, check it has expected attributes
        assert hasattr(dummy_tech, 'unit_cell_width')
        assert hasattr(dummy_tech, 'routing_grid_pitch_x')
        assert dummy_tech.db_unit == 1e-9

    def test_inverter_transistors_fixture(self, inverter_transistors):
        """inverter_transistors fixture returns 2 transistors."""
        assert len(inverter_transistors) == 2
        from lccommon.data_types import ChannelType
        # First should be NMOS
        assert inverter_transistors[0].channel_type == ChannelType.NMOS
        # Second should be PMOS
        assert inverter_transistors[1].channel_type == ChannelType.PMOS

    def test_project_root_fixture(self, project_root):
        """project_root fixture returns valid path."""
        assert str(project_root).endswith('librecell')

    def test_dummy_tech_path_fixture(self, dummy_tech_path):
        """dummy_tech_path fixture returns valid path."""
        assert dummy_tech_path.exists()
        assert dummy_tech_path.name == 'dummy_tech.py'

    def test_tech_config_fixture(self, tech_config):
        """tech_config fixture returns tech config object."""
        assert hasattr(tech_config, 'unit_cell_width')
        assert hasattr(tech_config, 'routing_grid_pitch_x')
        assert hasattr(tech_config, 'db_unit')
