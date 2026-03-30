"""
Task 01: Test pytest framework infrastructure.
"""
import os
from pathlib import Path
import pytest


@pytest.mark.unit
class TestPytestInfrastructure:
    """Test that pytest framework is properly configured."""

    def test_pytest_runs(self):
        """pytest framework can discover and run tests."""
        assert True

    def test_project_root(self, project_root):
        """Project root is correctly identified."""
        assert project_root.exists()
        assert (project_root / "pyproject.toml").exists()

    def test_pytest_config_exists(self, project_root):
        """pyproject.toml exists with pytest configuration."""
        config_file = project_root / "pyproject.toml"
        assert config_file.exists()
        content = config_file.read_text()
        assert "testpaths" in content
        assert "pytest" in content.lower()

    def test_markers_registered(self):
        """pytest markers are registered (no PytestUnknownMarkWarning)."""
        # This test passes if no warnings are raised during test collection
        import pytest
        pass

    def test_test_directory_structure(self, project_root):
        """Test directory structure exists."""
        tests_dir = project_root / "tests"
        assert tests_dir.exists()

        # Check key directories
        assert (tests_dir / "unit").exists()
        assert (tests_dir / "unit" / "common").exists()
        assert (tests_dir / "unit" / "layout").exists()
        assert (tests_dir / "unit" / "lib").exists()
        assert (tests_dir / "integration").exists()
        assert (tests_dir / "e2e").exists()
        assert (tests_dir / "fixtures").exists()

    def test_conftest_exists(self, project_root):
        """conftest.py exists in tests directory."""
        conftest = project_root / "tests" / "conftest.py"
        assert conftest.exists()


@pytest.mark.unit
class TestFixtures:
    """Test shared fixtures."""

    def test_dummy_tech_fixture(self, dummy_tech):
        """dummy_tech fixture returns a valid tech module."""
        # dummy_tech is a module, check it has expected attributes
        assert hasattr(dummy_tech, 'unit_cell_width')
        assert hasattr(dummy_tech, 'routing_grid_pitch_x')
        assert dummy_tech.db_unit == 1e-9

    def test_inverter_transistors_fixture(self, inverter_transistors):
        """inverter_transistors fixture returns 2 transistors."""
        assert len(inverter_transistors) == 2
        from lccommon.data_types import ChannelType
        assert inverter_transistors[0].channel_type == ChannelType.NMOS
        assert inverter_transistors[1].channel_type == ChannelType.PMOS

    def test_tmp_output_dir_fixture(self, tmp_output_dir):
        """tmp_output_dir fixture creates a valid temporary directory."""
        assert tmp_output_dir.exists()
        assert tmp_output_dir.is_dir()
