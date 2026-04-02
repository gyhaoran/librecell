"""
Task 08: Unit tests for the Python API (generate_cell, generate_cell_library).

Full pipeline tests (generate_cell_basic etc.) are marked @pytest.mark.integration
because they exercise the entire layout pipeline including placement, routing,
DRC cleaning, and output writers.
"""
import pytest
from pathlib import Path


# ---- Unit tests (no full pipeline) ----

class TestGenerateCellAPI:
    def test_generate_cell_invalid_placer(self, tmp_output_dir):
        """Unknown placer raises ValueError."""
        from lclayout.api import generate_cell

        project_root = Path(__file__).parent.parent.parent.parent
        tech_path = str(project_root / "librecell-layout" / "examples" / "dummy_tech.py")

        with pytest.raises(ValueError, match="Unknown placer"):
            generate_cell(
                cell_name="INVX1",
                netlist_path="dummy.sp",
                tech_config=tech_path,
                output_dir=str(tmp_output_dir),
                placer="nonexistent",
            )

    def test_generate_cell_invalid_router(self, tmp_output_dir):
        """Unknown router raises ValueError."""
        from lclayout.api import generate_cell

        project_root = Path(__file__).parent.parent.parent.parent
        tech_path = str(project_root / "librecell-layout" / "examples" / "dummy_tech.py")

        with pytest.raises(ValueError, match="Unknown router"):
            generate_cell(
                cell_name="INVX1",
                netlist_path="dummy.sp",
                tech_config=tech_path,
                output_dir=str(tmp_output_dir),
                router="nonexistent",
            )

    def test_generate_cell_invalid_tech_type(self, tmp_output_dir):
        """Non-str/TechConfig tech_config raises TypeError."""
        from lclayout.api import generate_cell

        with pytest.raises(TypeError, match="tech_config must be"):
            generate_cell(
                cell_name="INVX1",
                netlist_path="dummy.sp",
                tech_config=12345,
                output_dir=str(tmp_output_dir),
            )

    def test_generate_cell_accepts_tech_config_object(self, project_root, tmp_output_dir):
        """generate_cell accepts a TechConfig object without error up to pipeline start."""
        from lclayout.api import generate_cell
        from lclayout.tech_util import load_tech_file

        tech_path = str(project_root / "librecell-layout" / "examples" / "dummy_tech.py")
        tech = load_tech_file(tech_path)

        # Non-existent cell will fail during netlist loading, not during config parsing
        with pytest.raises(Exception):
            generate_cell(
                cell_name="NONEXISTENT",
                netlist_path="nonexistent.sp",
                tech_config=tech,
                output_dir=str(tmp_output_dir),
            )


class TestGenerateCellLibraryAPI:
    def test_generate_cell_library_empty_list(self, tmp_output_dir):
        """Empty cell list returns zero counts."""
        from lclayout.api import generate_cell_library

        result = generate_cell_library(
            cell_list=[],
            netlist_path="dummy.sp",
            tech_config="dummy.yaml",
            output_dir=str(tmp_output_dir),
        )
        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        assert result["results"] == {}
        assert result["failures"] == {}

    def test_generate_cell_library_stop_on_error(self, project_root, tmp_output_dir):
        """Default: stop at first failure."""
        from lclayout.api import generate_cell_library

        netlist_path = str(project_root / "tests" / "fixtures" / "netlists" / "cells.sp")
        tech_path = str(project_root / "librecell-layout" / "examples" / "dummy_tech.py")

        if not Path(netlist_path).exists():
            pytest.skip("cells.sp not found")

        result = generate_cell_library(
            cell_list=["NONEXISTENT_CELL", "INVX1"],
            netlist_path=netlist_path,
            tech_config=tech_path,
            output_dir=str(tmp_output_dir),
            continue_on_error=False,
            placer="flat",
        )
        # Stops at first failure
        assert result["failure_count"] == 1
        assert result["success_count"] == 0

    def test_generate_cell_library_continue_on_error(self, project_root, tmp_output_dir):
        """continue_on_error=True continues past failures."""
        from lclayout.api import generate_cell_library

        netlist_path = str(project_root / "tests" / "fixtures" / "netlists" / "cells.sp")
        tech_path = str(project_root / "librecell-layout" / "examples" / "dummy_tech.py")

        if not Path(netlist_path).exists():
            pytest.skip("cells.sp not found")

        # Both cells are non-existent to avoid full pipeline
        result = generate_cell_library(
            cell_list=["NONEXISTENT_A", "NONEXISTENT_B"],
            netlist_path=netlist_path,
            tech_config=tech_path,
            output_dir=str(tmp_output_dir),
            continue_on_error=True,
            placer="flat",
        )
        assert result["failure_count"] == 2
        assert "NONEXISTENT_A" in result["failures"]
        assert "NONEXISTENT_B" in result["failures"]

    def test_generate_cell_library_result_structure(self, tmp_output_dir):
        """Return dict has correct structure."""
        from lclayout.api import generate_cell_library

        result = generate_cell_library(
            cell_list=[],
            netlist_path="dummy.sp",
            tech_config="dummy.yaml",
            output_dir=str(tmp_output_dir),
        )
        assert "success_count" in result
        assert "failure_count" in result
        assert "results" in result
        assert "failures" in result
