"""
Task 07: Integration tests for migration pipeline.
"""
import subprocess
import sys
import pytest
from pathlib import Path

from lccommon.tech_config import TechConfig
from lccommon.tech_loader import load_tech_yaml
from lccommon.tech_migration import load_migration_rule, TechMigrator


@pytest.fixture
def cmos_90nm_path(project_root):
    return str(project_root / "librecell-layout" / "examples" / "cmos_90nm.yaml")


@pytest.fixture
def migration_dir(project_root):
    return project_root / "librecell-layout" / "examples" / "migration"


@pytest.fixture
def dummy_9t_path(project_root):
    return str(project_root / "librecell-layout" / "examples" / "dummy_tech_9t.yaml")


@pytest.mark.integration
class TestMigrationPipeline:
    def test_migrated_config_generates_layout(self, dummy_9t_path, migration_dir):
        """Migrated config (9T->7T) can initialize LcLayout."""
        import klayout.db as db
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter

        source = load_tech_yaml(dummy_9t_path)
        rule = load_migration_rule(str(migration_dir / "9t_to_7t.yaml"))
        target = TechMigrator(rule).migrate(source)

        layout = db.Layout()
        lc = LcLayout(
            tech=target,
            layout=layout,
            placer=EulerPlacer(),
            router=GraphRouter()
        )
        assert lc.tech.cell.num_tracks == 7

    def test_cross_node_migrated_config_generates_layout(self, cmos_90nm_path, migration_dir):
        """Cross-node migrated config (90nm->55nm) can initialize LcLayout."""
        import klayout.db as db
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter

        source = load_tech_yaml(cmos_90nm_path)
        rule = load_migration_rule(str(migration_dir / "90nm_to_55nm.yaml"))
        target = TechMigrator(rule).migrate(source)

        layout = db.Layout()
        lc = LcLayout(
            tech=target,
            layout=layout,
            placer=EulerPlacer(),
            router=GraphRouter()
        )
        assert lc.tech.node == "55nm"

    def test_cli_migration_command(self, cmos_90nm_path, migration_dir, tmp_output_dir):
        """CLI migration command produces output file."""
        output_path = str(tmp_output_dir / "cmos_55nm_generated.yaml")
        rule_path = str(migration_dir / "90nm_to_55nm.yaml")

        # Use a script file to avoid Windows path escaping issues
        script = (
            "from lclayout.standalone import migrate_main\n"
            "import sys\n"
            f"sys.argv = ['lclayout-migrate', '--source', r'{cmos_90nm_path}', "
            f"'--rule', r'{rule_path}', '--output', r'{output_path}']\n"
            "migrate_main()\n"
        )
        script_path = tmp_output_dir / "run_migrate.py"
        script_path.write_text(script, encoding='utf-8')

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert Path(output_path).exists()

        # Verify the generated file is valid
        generated = load_tech_yaml(output_path)
        assert generated.node == "55nm"
        assert isinstance(generated, TechConfig)
