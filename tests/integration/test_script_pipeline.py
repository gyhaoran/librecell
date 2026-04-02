"""
Task 08: Integration tests for the script pipeline.
"""
import os
import pytest
from pathlib import Path

from lccommon.script_context import ScriptConfig, ScriptEntry, ScriptContext, DrcViolation


@pytest.fixture
def script_dir(tmp_path):
    """Create temp directory with real-ish scripts for integration tests."""
    # A DRC script that reports a violation based on shapes content
    drc_py = tmp_path / "drc.py"
    drc_py.write_text(
        'from lccommon.script_context import DrcViolation\n'
        '\n'
        'def check_metal1(shapes, tech_config, layer_stack, **kwargs):\n'
        '    violations = []\n'
        '    if "metal1" in shapes:\n'
        '        violations.append(DrcViolation(\n'
        '            rule_name="METAL1_CHECK",\n'
        '            layer="metal1",\n'
        '            severity="warning",\n'
        '            message="metal1 layer present",\n'
        '        ))\n'
        '    return violations\n',
        encoding='utf-8',
    )

    # A postprocess script that adds a marker to shapes
    post_py = tmp_path / "postprocess.py"
    post_py.write_text(
        'def mark_processed(shapes, tech_config, layer_stack, **kwargs):\n'
        '    shapes["_processed"] = True\n',
        encoding='utf-8',
    )

    # A hook script that modifies the cell
    hook_py = tmp_path / "hook.py"
    hook_py.write_text(
        'def tag_cell(cell, shapes, tech_config, **kwargs):\n'
        '    if hasattr(cell, "_script_tag"):\n'
        '        cell._script_tag = True\n'
        '    return cell\n',
        encoding='utf-8',
    )

    # A broken script
    bad_py = tmp_path / "bad_script.py"
    bad_py.write_text(
        'def crash(shapes, tech_config, layer_stack, **kwargs):\n'
        '    raise ValueError("Intentional crash for testing")\n',
        encoding='utf-8',
    )

    return tmp_path


@pytest.mark.integration
class TestScriptPipeline:
    def test_custom_drc_script_runs(self, script_dir):
        """Custom DRC script is called and violations collected."""
        cfg = ScriptConfig(
            custom_drc=[
                ScriptEntry(path="drc.py", function="check_metal1"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        shapes = {"metal1": "some_shapes"}
        violations = ctx.run_custom_drc(shapes, None, None)
        assert len(violations) == 1
        assert violations[0].rule_name == "METAL1_CHECK"
        assert violations[0].severity == "warning"

    def test_layer_postprocess_modifies_shapes(self, script_dir):
        """layer_postprocess script actually modifies the shapes dict."""
        cfg = ScriptConfig(
            layer_postprocess=[
                ScriptEntry(path="postprocess.py", function="mark_processed"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        shapes = {"metal1": "original"}
        ctx.run_layer_postprocess(shapes, None, None)
        assert shapes["_processed"] is True
        assert shapes["metal1"] == "original"  # original data preserved

    def test_no_scripts_regression(self, script_dir):
        """Empty script config causes zero side effects."""
        cfg = ScriptConfig()
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        shapes = {"metal1": "test"}
        original_shapes = dict(shapes)

        ctx.run_layer_postprocess(shapes, None, None)
        assert shapes == original_shapes

        violations = ctx.run_custom_drc(shapes, None, None)
        assert violations == []

    def test_script_error_reported_clearly(self, script_dir):
        """Script exception produces a clear error violation."""
        cfg = ScriptConfig(
            custom_drc=[
                ScriptEntry(path="bad_script.py", function="crash"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        violations = ctx.run_custom_drc({}, None, None)
        assert len(violations) == 1
        assert "SCRIPT_ERROR" in violations[0].rule_name
        assert "Intentional crash" in violations[0].message

    def test_multiple_hooks_chain_correctly(self, script_dir):
        """Multiple hook scripts chain their results."""
        # Create a two-step hook script
        chain_py = script_dir / "chain.py"
        chain_py.write_text(
            'def step1(routing_trees, shapes, tech_config, **kwargs):\n'
            '    routing_trees["step1"] = True\n'
            '    return routing_trees\n'
            '\n'
            'def step2(routing_trees, shapes, tech_config, **kwargs):\n'
            '    routing_trees["step2"] = True\n'
            '    return routing_trees\n',
            encoding='utf-8',
        )
        cfg = ScriptConfig(
            on_after_routing=[
                ScriptEntry(path="chain.py", function="step1"),
                ScriptEntry(path="chain.py", function="step2"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        trees = {}
        result = ctx.run_hook('on_after_routing', routing_trees=trees, shapes={}, tech_config=None)
        assert result["step1"] is True
        assert result["step2"] is True

    def test_tech_config_scripts_field_integration(self, script_dir):
        """TechConfig.scripts field works with ScriptContext."""
        from lccommon.tech_config import TechConfig, CellConfig, RoutingConfig

        tech = TechConfig(
            cell=CellConfig(
                unit_cell_width=400,
                gate_length=50,
                gate_extension=100,
                power_rail_width=200,
                minimum_gate_width_nfet=200,
                minimum_gate_width_pfet=200,
                minimum_pin_width=50,
                num_tracks=7,
                track_pitch=200,
            ),
            routing=RoutingConfig(
                routing_grid_pitch_x=200,
            ),
            scripts=ScriptConfig(
                custom_drc=[
                    ScriptEntry(path="drc.py", function="check_metal1"),
                ],
            ),
        )
        assert tech.has_scripts
        ctx = ScriptContext(tech.scripts, base_dir=str(script_dir))
        violations = ctx.run_custom_drc({"metal1": "data"}, tech, None)
        assert len(violations) == 1

    def test_example_scripts_loadable(self, project_root):
        """The 3 example scripts can be loaded without errors."""
        examples_dir = project_root / "librecell-layout" / "examples" / "scripts"
        if not examples_dir.exists():
            pytest.skip("examples/scripts not found")

        cfg = ScriptConfig()
        ctx = ScriptContext(cfg, base_dir=str(examples_dir))

        scripts_to_check = [
            ("custom_drc.py", "check_eol_spacing"),
            ("custom_drc.py", "check_density"),
            ("layer_postprocess.py", "bias_poly_layer"),
            ("layer_postprocess.py", "add_fill_pattern"),
            ("guard_ring.py", "insert_guard_ring"),
            ("guard_ring.py", "add_power_straps"),
        ]
        for path, func_name in scripts_to_check:
            entry = ScriptEntry(path=path, function=func_name)
            func = ctx.load_function(entry)
            assert callable(func), f"{path}:{func_name} is not callable"
