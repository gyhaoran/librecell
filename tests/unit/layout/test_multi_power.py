"""
Task 06: Tests for multi-power-domain configuration.
"""
import pytest
from pathlib import Path

from lccommon.tech_config import TechConfig, PowerDomain, BcdConfig
from lccommon.net_util import is_ground_net, is_supply_net, is_power_net, get_io_pins


@pytest.fixture
def bcd_tech_path(project_root):
    return project_root / "librecell-layout" / "examples" / "bcd_tech.yaml"


@pytest.fixture
def bcd_config(bcd_tech_path):
    from lclayout.tech_util import load_tech_file
    return load_tech_file(str(bcd_tech_path))


class TestMultiPower:
    def test_single_power_domain_default(self, dummy_tech):
        """Default single power domain behaviour is unchanged."""
        assert len(dummy_tech.power_domains) == 1
        pd = dummy_tech.power_domains[0]
        assert pd.supply_net == "VDD"
        assert pd.ground_net == "VSS"

    def test_dual_power_domain(self, bcd_config):
        """Dual power domain configuration loads correctly."""
        assert len(bcd_config.power_domains) == 2
        names = {pd.name for pd in bcd_config.power_domains}
        assert 'core' in names
        assert 'io_hv' in names

    def test_custom_power_net_names(self, bcd_config):
        """Custom power net names are recognised via config."""
        assert is_supply_net("VDDH", config=bcd_config) is True
        assert is_supply_net("VDD", config=bcd_config) is True
        assert is_ground_net("VSS", config=bcd_config) is True

    def test_power_net_with_config(self, bcd_config):
        """is_power_net forwards config correctly."""
        assert is_power_net("VDDH", config=bcd_config) is True
        assert is_power_net("Y", config=bcd_config) is False

    def test_get_io_pins_excludes_power(self, bcd_config):
        """get_io_pins excludes all power nets when config is provided."""
        pins = {"A", "Y", "VDD", "VSS", "VDDH"}
        io = get_io_pins(pins, config=bcd_config)
        assert io == {"A", "Y"}

    def test_all_supply_nets_property(self, bcd_config):
        """TechConfig.all_supply_nets returns all supply nets."""
        assert bcd_config.all_supply_nets == {"VDD", "VDDH"}

    def test_all_ground_nets_property(self, bcd_config):
        """TechConfig.all_ground_nets returns all ground nets."""
        assert bcd_config.all_ground_nets == {"VSS"}

    def test_primary_power_domain(self, bcd_config):
        """Primary power domain is the first one in the list."""
        pd = bcd_config.primary_power_domain
        assert pd.name == "core"
        assert pd.supply_net == "VDD"

    def test_bcd_enabled(self, bcd_config):
        """BCD configuration is enabled."""
        assert bcd_config.bcd_enabled is True

    def test_bcd_disabled_default(self, dummy_tech):
        """BCD is disabled by default."""
        assert dummy_tech.bcd_enabled is False

    def test_power_domain_is_high_voltage(self, bcd_config):
        """High voltage power domain flag is set correctly."""
        hv_domains = [pd for pd in bcd_config.power_domains if pd.is_high_voltage]
        assert len(hv_domains) == 1
        assert hv_domains[0].name == "io_hv"

    def test_default_power_net_detection_without_config(self):
        """Without config, hardcoded default set is used."""
        assert is_supply_net("vdd") is True
        assert is_supply_net("vcc") is True
        assert is_supply_net("VDDH") is False  # not in default set
        assert is_ground_net("gnd") is True
        assert is_ground_net("vss") is True
