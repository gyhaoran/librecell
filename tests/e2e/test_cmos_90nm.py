"""
Task 09: End-to-end tests for CMOS 90nm process node.

Validates the full pipeline with 90nm technology configuration.
"""
import os
import pytest
from pathlib import Path


CORE_CELLS_90NM = ["INVX1", "INVX2", "NAND2X1", "NOR2X1", "BUFX2"]


@pytest.fixture(scope="module")
def tech_90nm(project_root):
    from lccommon.tech_loader import load_tech_yaml
    return load_tech_yaml(
        str(project_root / "librecell-layout" / "examples" / "cmos_90nm.yaml")
    )


@pytest.fixture(scope="module")
def netlist_path(project_root):
    p = project_root / "tests" / "fixtures" / "netlists" / "cells.sp"
    if not p.exists():
        pytest.skip("cells.sp not found")
    return str(p)


@pytest.mark.e2e
class TestCMOS90nm:

    @pytest.mark.parametrize("cell_name", CORE_CELLS_90NM)
    def test_generate_cell_gds(self, cell_name, tech_90nm, netlist_path, tmp_output_dir):
        """Each cell generates a valid GDS file at 90nm."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name=cell_name,
            netlist_path=netlist_path,
            tech_config=tech_90nm,
            output_dir=str(tmp_output_dir),
        )
        gds = result.get("gds_path")
        assert gds is not None
        assert os.path.exists(gds), f"GDS file missing: {gds}"
        assert os.path.getsize(gds) > 0

    @pytest.mark.parametrize("cell_name", CORE_CELLS_90NM)
    def test_generate_cell_lef(self, cell_name, tech_90nm, netlist_path, tmp_output_dir):
        """Each cell generates a valid LEF file at 90nm."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name=cell_name,
            netlist_path=netlist_path,
            tech_config=tech_90nm,
            output_dir=str(tmp_output_dir),
        )
        lef = result.get("lef_path")
        assert lef is not None
        assert os.path.exists(lef)
        assert "MACRO" in Path(lef).read_text()

    @pytest.mark.parametrize("cell_name", CORE_CELLS_90NM)
    def test_lvs_pass(self, cell_name, tech_90nm, netlist_path, tmp_output_dir):
        """Each cell passes LVS verification at 90nm."""
        from lclayout.api import generate_cell

        result = generate_cell(
            cell_name=cell_name,
            netlist_path=netlist_path,
            tech_config=tech_90nm,
            output_dir=str(tmp_output_dir),
        )
        assert result["lvs_passed"], f"LVS failed for {cell_name} at 90nm"

    def test_cell_height_smaller_than_180nm(self, tech_90nm, project_root):
        """90nm cell height is approximately half of 180nm."""
        from lccommon.tech_loader import load_tech_yaml

        tech_180nm = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")
        )
        h_180 = tech_180nm.cell.unit_cell_height
        h_90 = tech_90nm.cell.unit_cell_height
        assert h_90 < h_180, f"90nm height {h_90} should be less than 180nm height {h_180}"
        # Should be roughly 0.5x (allow 20% tolerance)
        ratio = h_90 / h_180
        assert 0.4 <= ratio <= 0.6, f"Height ratio {ratio:.2f} outside expected 0.4-0.6 range"
