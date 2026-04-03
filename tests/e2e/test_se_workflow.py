"""
Task 09: End-to-end tests for SE (Silicon Engineering) workflow.

Validates the full SE engineer workflow:
1. Copy and modify a tech config
2. Write a custom script and attach to config
3. Use Python API to generate cells
4. Verify results
"""
import os
import shutil
import pytest
from pathlib import Path


@pytest.fixture(scope="module")
def netlist_path(project_root):
    p = project_root / "tests" / "fixtures" / "netlists" / "cells.sp"
    if not p.exists():
        pytest.skip("cells.sp not found")
    return str(p)


@pytest.mark.e2e
class TestSEWorkflow:

    def test_copy_and_load_config(self, project_root, tmp_path):
        """SE engineer can copy a config and load it."""
        from lccommon.tech_loader import load_tech_yaml

        src = project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml"
        dst = tmp_path / "my_tech.yaml"
        shutil.copy(str(src), str(dst))

        tech = load_tech_yaml(str(dst))
        assert tech is not None
        assert tech.node == "180nm"

    def test_modify_and_save_config(self, project_root, tmp_path):
        """SE engineer can modify tech parameters and save back to YAML."""
        from lccommon.tech_loader import load_tech_yaml, save_tech_yaml

        src = project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml"
        dst = tmp_path / "my_tech_modified.yaml"
        shutil.copy(str(src), str(dst))

        tech = load_tech_yaml(str(dst))
        original_gate_length = tech.cell.gate_length
        tech.cell.gate_length = original_gate_length * 0.9  # tweak by 10%
        save_tech_yaml(tech, str(dst))

        # Reload and verify
        reloaded = load_tech_yaml(str(dst))
        assert abs(reloaded.cell.gate_length - original_gate_length * 0.9) < 1.0

    def test_modified_config_generates_cell(self, project_root, netlist_path, tmp_path):
        """Modified tech config can generate a cell layout."""
        from lccommon.tech_loader import load_tech_yaml, save_tech_yaml
        from lclayout.api import generate_cell

        src = project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml"
        dst = tmp_path / "my_tech.yaml"
        shutil.copy(str(src), str(dst))

        tech = load_tech_yaml(str(dst))
        # Minor tweak: add 5% to wire width
        for layer in tech.routing.wire_width:
            tech.routing.wire_width[layer] *= 1.05
        save_tech_yaml(tech, str(dst))

        out_dir = tmp_path / "output"
        out_dir.mkdir()
        result = generate_cell(
            cell_name="INVX1",
            netlist_path=netlist_path,
            tech_config=str(dst),
            output_dir=str(out_dir),
        )
        assert result.get("gds_path") and os.path.exists(result["gds_path"])

    def test_script_based_drc_customization(self, project_root, netlist_path, tmp_path):
        """SE engineer can attach a custom DRC script that runs post-generation."""
        from lccommon.tech_loader import load_tech_yaml, save_tech_yaml
        from lccommon.script_context import ScriptEntry, ScriptConfig
        from lclayout.api import generate_cell

        # Write a custom DRC script
        script_dir = tmp_path / "scripts"
        script_dir.mkdir()
        drc_script = script_dir / "my_drc.py"
        drc_script.write_text(
            "from lccommon.script_context import DrcViolation\n"
            "\n"
            "def check_my_rules(shapes, tech_config, layer_stack, **kwargs):\n"
            "    # Always passes — just demonstrates the hook runs\n"
            "    return []\n",
            encoding="utf-8",
        )

        src = project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml"
        tech = load_tech_yaml(str(src))
        tech.scripts = ScriptConfig(
            custom_drc=[
                ScriptEntry(path="my_drc.py", function="check_my_rules"),
            ]
        )
        tech._config_dir = str(script_dir)

        out_dir = tmp_path / "output"
        out_dir.mkdir()
        result = generate_cell(
            cell_name="INVX1",
            netlist_path=netlist_path,
            tech_config=tech,
            output_dir=str(out_dir),
        )
        assert result.get("gds_path") and os.path.exists(result["gds_path"])

    def test_python_api_batch_workflow(self, project_root, netlist_path, tmp_path):
        """SE engineer uses generate_cell_library() for batch generation."""
        from lccommon.tech_loader import load_tech_yaml
        from lclayout.api import generate_cell_library

        tech = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")
        )
        out_dir = tmp_path / "batch_output"
        out_dir.mkdir()

        result = generate_cell_library(
            cell_list=["INVX1", "NAND2X1", "NOR2X1"],
            netlist_path=netlist_path,
            tech_config=tech,
            output_dir=str(out_dir),
            continue_on_error=True,
        )
        # All three simple cells should succeed
        assert result["success_count"] == 3, (
            f"Expected 3 successes, got {result['success_count']}. "
            f"Failures: {result.get('failures', {})}"
        )
        # Verify output files exist
        for cell_name in ["INVX1", "NAND2X1", "NOR2X1"]:
            gds = out_dir / f"{cell_name}.gds"
            assert gds.exists(), f"GDS missing for {cell_name}: {gds}"

    def test_lvs_passes_for_customized_config(self, project_root, netlist_path, tmp_path):
        """Customized tech config generates cells that pass LVS."""
        from lccommon.tech_loader import load_tech_yaml, save_tech_yaml
        from lclayout.api import generate_cell

        src = project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml"
        dst = tmp_path / "my_cmos.yaml"
        shutil.copy(str(src), str(dst))

        # Simple customization: change the config name only
        tech = load_tech_yaml(str(dst))
        tech.name = "my_custom_180nm"
        save_tech_yaml(tech, str(dst))

        out_dir = tmp_path / "output"
        out_dir.mkdir()
        result = generate_cell(
            cell_name="INVX1",
            netlist_path=netlist_path,
            tech_config=str(dst),
            output_dir=str(out_dir),
        )
        assert result["lvs_passed"], "LVS failed for customized 180nm config"
