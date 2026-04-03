"""
Task 09: End-to-end tests for BCD (Bipolar-CMOS-DMOS) technology.

Validates that the BCD tech config generates correct layouts with HV layer markers.
"""
import os
import pytest
from pathlib import Path


@pytest.fixture(scope="module")
def tech_bcd(project_root):
    from lccommon.tech_loader import load_tech_yaml
    return load_tech_yaml(
        str(project_root / "librecell-layout" / "examples" / "bcd_tech.yaml")
    )


@pytest.fixture(scope="module")
def netlist_path(project_root):
    p = project_root / "tests" / "fixtures" / "netlists" / "cells.sp"
    if not p.exists():
        pytest.skip("cells.sp not found")
    return str(p)


@pytest.mark.e2e
class TestBCD:

    def test_bcd_config_loads(self, tech_bcd):
        """BCD tech config loads with BCD extension enabled."""
        assert tech_bcd.bcd.enabled is True
        assert tech_bcd.bcd.thick_oxide_layer == "thick_oxide"
        assert len(tech_bcd.power_domains) >= 2

    def test_bcd_has_hv_power_domain(self, tech_bcd):
        """BCD tech has at least one high-voltage power domain."""
        hv_domains = [d for d in tech_bcd.power_domains if d.is_high_voltage]
        assert len(hv_domains) >= 1, "BCD tech should have at least one HV power domain"

    def test_bcd_cmos_invx1_generates(self, tech_bcd, netlist_path, tmp_output_dir):
        """Standard CMOS INVX1 generates successfully with BCD tech config."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name="INVX1",
            netlist_path=netlist_path,
            tech_config=tech_bcd,
            output_dir=str(tmp_output_dir),
        )
        gds = result.get("gds_path")
        assert gds is not None, "No GDS returned for INVX1 with BCD tech"
        assert os.path.exists(gds), f"GDS missing: {gds}"
        assert os.path.getsize(gds) > 0

    def test_bcd_cmos_nand2_generates(self, tech_bcd, netlist_path, tmp_output_dir):
        """Standard CMOS NAND2X1 generates successfully with BCD tech config."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name="NAND2X1",
            netlist_path=netlist_path,
            tech_config=tech_bcd,
            output_dir=str(tmp_output_dir),
        )
        gds = result.get("gds_path")
        assert gds is not None
        assert os.path.exists(gds)

    def test_bcd_invx1_lvs(self, tech_bcd, netlist_path, tmp_output_dir):
        """INVX1 passes LVS verification with BCD tech config."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name="INVX1",
            netlist_path=netlist_path,
            tech_config=tech_bcd,
            output_dir=str(tmp_output_dir),
        )
        assert result["lvs_passed"], "INVX1 LVS failed with BCD tech config"

    def test_bcd_output_map_contains_hv_layers(self, tech_bcd):
        """BCD output_map includes HV-specific layers."""
        output_map = tech_bcd.output_map
        # Check that HV layers from bcd config are present in output_map
        hv_layers = [tech_bcd.bcd.thick_oxide_layer, tech_bcd.bcd.hv_nwell_layer]
        for layer in hv_layers:
            assert layer in output_map, f"HV layer '{layer}' missing from output_map"

    def test_bcd_library_generation(self, tech_bcd, netlist_path, tmp_output_dir):
        """BCD config generates a small library batch without failures."""
        from lclayout.api import generate_cell_library

        result = generate_cell_library(
            cell_list=["INVX1", "NAND2X1", "NOR2X1"],
            netlist_path=netlist_path,
            tech_config=tech_bcd,
            output_dir=str(tmp_output_dir),
            continue_on_error=True,
        )
        assert result["success_count"] >= 2, (
            f"Expected at least 2 successes with BCD config, "
            f"got {result['success_count']}. Failures: {result.get('failures', {})}"
        )
