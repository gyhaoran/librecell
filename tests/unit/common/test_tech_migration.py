"""
Task 07: Unit tests for tech migration engine.
"""
import pytest
from pathlib import Path

from lccommon.tech_migration import (
    MigrationRule, MigrationReport, TechMigrator,
    load_migration_rule, _resolve_dot_path, _set_dot_path,
)
from lccommon.tech_loader import load_tech_yaml
from lccommon.tech_config import TechConfig


@pytest.fixture
def cmos_180nm_path(project_root):
    return str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")


@pytest.fixture
def cmos_90nm_path(project_root):
    return str(project_root / "librecell-layout" / "examples" / "cmos_90nm.yaml")


@pytest.fixture
def dummy_7t_path(project_root):
    return str(project_root / "librecell-layout" / "examples" / "dummy_tech_7t.yaml")


@pytest.fixture
def dummy_9t_path(project_root):
    return str(project_root / "librecell-layout" / "examples" / "dummy_tech_9t.yaml")


@pytest.fixture
def dummy_10t_path(project_root):
    return str(project_root / "librecell-layout" / "examples" / "dummy_tech_10t.yaml")


@pytest.fixture
def migration_dir(project_root):
    return project_root / "librecell-layout" / "examples" / "migration"


# ---- Dot-path helpers ----

class TestDotPathHelpers:
    def test_resolve_simple(self):
        data = {"cell": {"gate_length": 50}}
        assert _resolve_dot_path(data, "cell.gate_length") == 50

    def test_resolve_top_level(self):
        data = {"name": "test"}
        assert _resolve_dot_path(data, "name") == "test"

    def test_resolve_deep(self):
        data = {"drc": {"min_spacing": {"metal1": {"metal1": 100}}}}
        assert _resolve_dot_path(data, "drc.min_spacing.metal1.metal1") == 100

    def test_resolve_missing_raises(self):
        data = {"cell": {"gate_length": 50}}
        with pytest.raises(ValueError, match="not found"):
            _resolve_dot_path(data, "cell.nonexistent")

    def test_set_simple(self):
        data = {"cell": {"gate_length": 50}}
        _set_dot_path(data, "cell.gate_length", 90)
        assert data["cell"]["gate_length"] == 90

    def test_set_creates_intermediate(self):
        data = {}
        _set_dot_path(data, "cell.num_tracks", 7)
        assert data["cell"]["num_tracks"] == 7


# ---- MigrationRule ----

class TestMigrationRule:
    def test_load_migration_rule(self, migration_dir):
        rule = load_migration_rule(str(migration_dir / "90nm_to_55nm.yaml"))
        assert rule.source_node == "90nm"
        assert rule.target_node == "55nm"
        assert abs(rule.scale_factor - 0.611) < 0.001

    def test_scale_factor_applied(self, cmos_90nm_path):
        source = load_tech_yaml(cmos_90nm_path)
        rule = MigrationRule(
            source_node="90nm", target_node="55nm",
            scale_factor=55 / 90
        )
        target = TechMigrator(rule).migrate(source)
        expected = round(source.cell.gate_length * 55 / 90)
        assert target.cell.gate_length == expected

    def test_overrides_precedence(self, cmos_90nm_path):
        """Override scale factor takes precedence over global."""
        source = load_tech_yaml(cmos_90nm_path)
        rule = MigrationRule(
            source_node="90nm", target_node="custom",
            scale_factor=0.5,
            overrides={"cell.gate_length": 0.8}
        )
        target = TechMigrator(rule).migrate(source)
        expected = round(source.cell.gate_length * 0.8)
        assert target.cell.gate_length == expected

    def test_fixed_values(self, cmos_90nm_path):
        """Fixed values override any scaling."""
        source = load_tech_yaml(cmos_90nm_path)
        rule = MigrationRule(
            source_node="90nm", target_node="custom",
            scale_factor=0.5,
            fixed_values={"cell.gate_length": 42}
        )
        target = TechMigrator(rule).migrate(source)
        assert target.cell.gate_length == 42

    def test_discrete_params_not_scaled(self, cmos_90nm_path):
        """Layer names, weights not accidentally scaled."""
        source = load_tech_yaml(cmos_90nm_path)
        rule = MigrationRule(
            source_node="90nm", target_node="55nm",
            scale_factor=0.5
        )
        target = TechMigrator(rule).migrate(source)
        assert target.cell.pin_layer == source.cell.pin_layer
        assert target.cell.power_layer == source.cell.power_layer
        assert target.routing.weights_horizontal == source.routing.weights_horizontal
        assert target.routing.routing_layers == source.routing.routing_layers

    def test_rounding_to_db_unit(self, cmos_90nm_path):
        """Scaled values are rounded to integers (db_unit granularity)."""
        source = load_tech_yaml(cmos_90nm_path)
        rule = MigrationRule(
            source_node="90nm", target_node="55nm",
            scale_factor=55 / 90  # irrational ratio
        )
        target = TechMigrator(rule).migrate(source)
        # All geometric values should be integers
        assert isinstance(target.cell.gate_length, (int, float))
        assert target.cell.gate_length == round(target.cell.gate_length)


# ---- Track migration ----

class TestTrackMigration:
    def test_7t_to_9t_height_change(self, dummy_7t_path, migration_dir):
        source = load_tech_yaml(dummy_7t_path)
        rule = load_migration_rule(str(migration_dir / "7t_to_9t.yaml"))
        target = TechMigrator(rule).migrate(source)
        assert target.cell.num_tracks == 9
        # Height should increase
        assert target.cell.unit_cell_height > source.cell.unit_cell_height

    def test_7t_to_9t_x_params_unchanged(self, dummy_7t_path, migration_dir):
        """Upward track migration does not affect X-direction params."""
        source = load_tech_yaml(dummy_7t_path)
        rule = load_migration_rule(str(migration_dir / "7t_to_9t.yaml"))
        target = TechMigrator(rule).migrate(source)
        assert target.cell.gate_length == source.cell.gate_length
        assert target.cell.unit_cell_width == source.cell.unit_cell_width
        assert target.routing.routing_grid_pitch_x == source.routing.routing_grid_pitch_x

    def test_9t_to_7t_downward(self, dummy_9t_path, migration_dir):
        source = load_tech_yaml(dummy_9t_path)
        rule = load_migration_rule(str(migration_dir / "9t_to_7t.yaml"))
        target = TechMigrator(rule).migrate(source)
        assert target.cell.num_tracks == 7
        assert target.cell.unit_cell_height < source.cell.unit_cell_height

    def test_10t_to_7t_downward(self, dummy_10t_path, migration_dir):
        source = load_tech_yaml(dummy_10t_path)
        rule = load_migration_rule(str(migration_dir / "10t_to_7t.yaml"))
        target = TechMigrator(rule).migrate(source)
        assert target.cell.num_tracks == 7
        assert target.cell.unit_cell_height < source.cell.unit_cell_height

    def test_downward_feasibility_warning(self, dummy_9t_path, migration_dir):
        """Downward migration warns for complex cells."""
        source = load_tech_yaml(dummy_9t_path)
        rule = load_migration_rule(str(migration_dir / "9t_to_7t.yaml"))
        migrator = TechMigrator(rule)
        target = migrator.migrate(source)
        report = migrator.validate_feasibility(
            source, target, cell_names=["DFFPOSX1"]
        )
        # DFF needs >= 9 tracks, so should warn or fail
        assert len(report.warnings) > 0 or not report.feasible

    def test_extreme_downward_7t_to_6t(self, dummy_7t_path, migration_dir):
        """7T -> 6T extreme: complex cells should be infeasible."""
        source = load_tech_yaml(dummy_7t_path)
        rule = load_migration_rule(str(migration_dir / "7t_to_6t.yaml"))
        migrator = TechMigrator(rule)
        target = migrator.migrate(source)
        report = migrator.validate_feasibility(
            source, target, cell_names=["DFFPOSX1", "AOI21X1"]
        )
        # At least DFF should be flagged
        assert len(report.errors) > 0 or len(report.warnings) > 0


# ---- Cross-node migration ----

class TestCrossNodeMigration:
    def test_90nm_to_55nm(self, cmos_90nm_path, migration_dir):
        source = load_tech_yaml(cmos_90nm_path)
        rule = load_migration_rule(str(migration_dir / "90nm_to_55nm.yaml"))
        target = TechMigrator(rule).migrate(source)
        assert target.node == "55nm"
        assert target.cell.gate_length < source.cell.gate_length

    def test_migration_report(self, cmos_90nm_path, migration_dir):
        source = load_tech_yaml(cmos_90nm_path)
        rule = load_migration_rule(str(migration_dir / "90nm_to_55nm.yaml"))
        migrator = TechMigrator(rule)
        target = migrator.migrate(source)
        report_text = migrator.generate_migration_report(source, target)
        assert "90nm" in report_text
        assert "55nm" in report_text
        assert "Scale factor" in report_text

    def test_migrated_config_validates(self, cmos_90nm_path, migration_dir):
        """Migrated config passes Pydantic schema validation."""
        source = load_tech_yaml(cmos_90nm_path)
        rule = load_migration_rule(str(migration_dir / "90nm_to_55nm.yaml"))
        target = TechMigrator(rule).migrate(source)
        # Should not raise — target is already a TechConfig
        assert isinstance(target, TechConfig)
        # Round-trip through model_dump -> model_validate
        reloaded = TechConfig.model_validate(target.model_dump())
        assert reloaded.cell.gate_length == target.cell.gate_length

    def test_180nm_to_90nm(self, cmos_180nm_path, migration_dir):
        source = load_tech_yaml(cmos_180nm_path)
        rule = load_migration_rule(str(migration_dir / "180nm_to_90nm.yaml"))
        target = TechMigrator(rule).migrate(source)
        assert target.node == "90nm"
        assert target.cell.gate_length == round(source.cell.gate_length * 0.5)
