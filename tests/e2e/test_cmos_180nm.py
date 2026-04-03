"""
Task 09: End-to-end tests for CMOS 180nm process node.

Validates the full pipeline: tech config -> cell layout -> GDS output -> LEF output -> LVS pass.
"""
import os
import pytest
from pathlib import Path


# Minimum cell set that must pass for 180nm
CORE_CELLS = ["INVX1", "INVX2", "NAND2X1", "NOR2X1", "AND2X1",
               "OR2X1", "BUFX2", "DFFPOSX1", "AOI21X1"]


@pytest.fixture(scope="module")
def tech_180nm(project_root):
    from lccommon.tech_loader import load_tech_yaml
    return load_tech_yaml(
        str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")
    )


@pytest.fixture(scope="module")
def netlist_path(project_root):
    p = project_root / "tests" / "fixtures" / "netlists" / "cells.sp"
    if not p.exists():
        pytest.skip("cells.sp not found")
    return str(p)


@pytest.mark.e2e
class TestCMOS180nm:

    @pytest.mark.parametrize("cell_name", CORE_CELLS)
    def test_generate_cell_gds(self, cell_name, tech_180nm, netlist_path, tmp_output_dir):
        """Each cell generates a valid GDS file."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name=cell_name,
            netlist_path=netlist_path,
            tech_config=tech_180nm,
            output_dir=str(tmp_output_dir),
        )
        gds = result.get("gds_path")
        assert gds is not None, f"No GDS path returned for {cell_name}"
        assert os.path.exists(gds), f"GDS file missing: {gds}"
        assert os.path.getsize(gds) > 0, f"GDS file is empty: {gds}"

    @pytest.mark.parametrize("cell_name", CORE_CELLS)
    def test_generate_cell_lef(self, cell_name, tech_180nm, netlist_path, tmp_output_dir):
        """Each cell generates a LEF file with MACRO definition."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name=cell_name,
            netlist_path=netlist_path,
            tech_config=tech_180nm,
            output_dir=str(tmp_output_dir),
        )
        lef = result.get("lef_path")
        assert lef is not None, f"No LEF path returned for {cell_name}"
        assert os.path.exists(lef), f"LEF file missing: {lef}"
        content = Path(lef).read_text()
        assert "MACRO" in content, f"LEF does not contain MACRO definition for {cell_name}"
        assert cell_name in content, f"LEF does not reference cell name {cell_name}"

    @pytest.mark.parametrize("cell_name", CORE_CELLS)
    def test_lvs_pass(self, cell_name, tech_180nm, netlist_path, tmp_output_dir):
        """Each cell passes LVS verification."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name=cell_name,
            netlist_path=netlist_path,
            tech_config=tech_180nm,
            output_dir=str(tmp_output_dir),
        )
        assert result["lvs_passed"], (
            f"LVS failed for {cell_name}. "
            f"DRC violations: {result.get('drc_violations', [])}"
        )

    def test_library_generation(self, tech_180nm, netlist_path, tmp_output_dir):
        """Batch generation of the full 180nm cell set succeeds."""
        from lclayout.api import generate_cell_library

        result = generate_cell_library(
            cell_list=CORE_CELLS,
            netlist_path=netlist_path,
            tech_config=tech_180nm,
            output_dir=str(tmp_output_dir),
            continue_on_error=True,
        )
        failures = result.get("failures", {})
        assert result["success_count"] == len(CORE_CELLS), (
            f"Expected {len(CORE_CELLS)} successes, got {result['success_count']}. "
            f"Failures: {failures}"
        )
        assert result["failure_count"] == 0, f"Unexpected failures: {failures}"
