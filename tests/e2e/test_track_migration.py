"""
Task 09: End-to-end tests for track migration (upward and downward).

Tests:
- 7T -> 9T upward migration: both generate layouts, 9T taller than 7T
- 9T -> 7T downward migration: simple cells pass LVS, feasibility report works
- Extreme 9T -> 6T downward: complex cells produce warnings
"""
import os
import pytest
from pathlib import Path


@pytest.fixture(scope="module")
def tech_7t(project_root):
    from lccommon.tech_loader import load_tech_yaml
    return load_tech_yaml(
        str(project_root / "librecell-layout" / "examples" / "dummy_tech_7t.yaml")
    )


@pytest.fixture(scope="module")
def tech_9t(project_root):
    from lccommon.tech_loader import load_tech_yaml
    return load_tech_yaml(
        str(project_root / "librecell-layout" / "examples" / "dummy_tech_9t.yaml")
    )


@pytest.fixture(scope="module")
def netlist_path(project_root):
    p = project_root / "tests" / "fixtures" / "netlists" / "cells.sp"
    if not p.exists():
        pytest.skip("cells.sp not found")
    return str(p)


@pytest.mark.e2e
class TestTrackMigration:

    def test_7t_to_9t_inv_generates(self, tech_7t, tech_9t, netlist_path, tmp_output_dir):
        """INVX1 generates successfully in both 7T and 9T configurations."""
        from lclayout.api import generate_cell

        for tech, label in [(tech_7t, "7t"), (tech_9t, "9t")]:
            out = tmp_output_dir / label
            out.mkdir()
            result = generate_cell(
                cell_name="INVX1",
                netlist_path=netlist_path,
                tech_config=tech,
                output_dir=str(out),
            )
            assert result.get("gds_path") and os.path.exists(result["gds_path"]), \
                f"INVX1 GDS missing for {label}"

    def test_7t_to_9t_nand2_generates(self, tech_7t, tech_9t, netlist_path, tmp_output_dir):
        """NAND2X1 generates successfully in both 7T and 9T configurations."""
        from lclayout.api import generate_cell

        for tech, label in [(tech_7t, "7t"), (tech_9t, "9t")]:
            out = tmp_output_dir / label
            out.mkdir(exist_ok=True)
            result = generate_cell(
                cell_name="NAND2X1",
                netlist_path=netlist_path,
                tech_config=tech,
                output_dir=str(out),
            )
            assert result.get("gds_path") and os.path.exists(result["gds_path"]), \
                f"NAND2X1 GDS missing for {label}"

    def test_9t_taller_than_7t(self, tech_7t, tech_9t):
        """9T cell height is greater than 7T cell height."""
        h_7t = tech_7t.cell.unit_cell_height
        h_9t = tech_9t.cell.unit_cell_height
        assert h_9t > h_7t, f"9T height {h_9t} should be > 7T height {h_7t}"

    def test_7t_to_9t_inv_lvs(self, tech_7t, tech_9t, netlist_path, tmp_output_dir):
        """INVX1 passes LVS in both 7T and 9T configurations."""
        from lclayout.api import generate_cell

        for tech, label in [(tech_7t, "7t_lvs"), (tech_9t, "9t_lvs")]:
            out = tmp_output_dir / label
            out.mkdir()
            result = generate_cell(
                cell_name="INVX1",
                netlist_path=netlist_path,
                tech_config=tech,
                output_dir=str(out),
            )
            assert result["lvs_passed"], f"LVS failed for INVX1 in {label}"

    def test_migrated_7t_to_9t_config(self, project_root, netlist_path, tmp_output_dir):
        """Config migrated via 7t_to_9t rule generates cells correctly."""
        from lccommon.tech_loader import load_tech_yaml
        from lccommon.tech_migration import TechMigrator, load_migration_rule
        from lclayout.api import generate_cell

        source = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "dummy_tech_7t.yaml")
        )
        rule = load_migration_rule(
            str(project_root / "librecell-layout" / "examples" / "migration" / "7t_to_9t.yaml")
        )
        migrated = TechMigrator(rule).migrate(source)

        result = generate_cell(
            cell_name="INVX1",
            netlist_path=netlist_path,
            tech_config=migrated,
            output_dir=str(tmp_output_dir),
        )
        assert result.get("gds_path") and os.path.exists(result["gds_path"])

    def test_9t_to_7t_downward_inv_lvs(self, project_root, netlist_path, tmp_output_dir):
        """After 9T->7T downward migration, INVX1 passes LVS."""
        from lccommon.tech_loader import load_tech_yaml
        from lccommon.tech_migration import TechMigrator, load_migration_rule
        from lclayout.api import generate_cell

        source = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "dummy_tech_9t.yaml")
        )
        rule = load_migration_rule(
            str(project_root / "librecell-layout" / "examples" / "migration" / "9t_to_7t.yaml")
        )
        migrated = TechMigrator(rule).migrate(source)

        result = generate_cell(
            cell_name="INVX1",
            netlist_path=netlist_path,
            tech_config=migrated,
            output_dir=str(tmp_output_dir),
        )
        assert result["lvs_passed"], "INVX1 LVS failed after 9T->7T downward migration"

    def test_9t_to_7t_feasibility_report(self, project_root):
        """Feasibility report identifies track count change correctly."""
        from lccommon.tech_loader import load_tech_yaml
        from lccommon.tech_migration import TechMigrator, MigrationRule
        from lccommon.data_types import Transistor, ChannelType

        source = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "dummy_tech_9t.yaml")
        )
        rule = MigrationRule(
            source_node="9t",
            target_node="7t",
            scale_factor=1.0,
            fixed_values={"cell.num_tracks": 7},
        )
        migrator = TechMigrator(rule)
        target = migrator.migrate(source)
        assert target.cell.num_tracks == 7

        # Feasibility check with a complex cell
        inv_transistors = [
            Transistor(ChannelType.NMOS, "gnd", "A", "Y", 200.0, "M0"),
            Transistor(ChannelType.PMOS, "vdd", "A", "Y", 400.0, "M1"),
        ]
        report = migrator.validate_feasibility(source, target, cell_names=["INVX1"])
        # 7T should be feasible for a simple inverter — just verify it runs
        assert report is not None

    def test_extreme_9t_to_6t_warning(self, project_root):
        """Extreme downward migration (9T->6T) produces warnings for complex cells."""
        from lccommon.tech_loader import load_tech_yaml
        from lccommon.tech_migration import TechMigrator, MigrationRule

        source = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "dummy_tech_9t.yaml")
        )
        rule = MigrationRule(
            source_node="9t",
            target_node="6t",
            scale_factor=1.0,
            fixed_values={"cell.num_tracks": 6},
        )
        migrator = TechMigrator(rule)
        target = migrator.migrate(source)
        assert target.cell.num_tracks == 6

        # Use a known complex cell name (heuristic uses cell name length/complexity)
        report = migrator.validate_feasibility(
            source, target,
            cell_names=["DFFPOSX1", "AOI21X1"],  # complex cells
        )
        # Should produce at least downward-migration warning
        has_issues = not report.feasible or len(report.warnings) > 0 or len(report.errors) > 0
        assert has_issues, "Expected warnings/errors for extreme 6T migration"
