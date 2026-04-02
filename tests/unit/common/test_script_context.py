"""
Task 08: Unit tests for script context (script loading, DRC, hooks).
"""
import os
import pytest
import tempfile
from pathlib import Path

from lccommon.script_context import (
    DrcViolation, ScriptEntry, ScriptConfig, ScriptContext,
)
from lccommon.tech_config import TechConfig


# ---- Helper: write temp script files ----

@pytest.fixture
def script_dir(tmp_path):
    """Create a temp directory with sample script files."""
    # custom_drc.py — returns violations
    drc_script = tmp_path / "custom_drc.py"
    drc_script.write_text(
        'from lccommon.script_context import DrcViolation\n'
        '\n'
        'def check_spacing(shapes, tech_config, layer_stack, min_spacing=100, **kwargs):\n'
        '    return [\n'
        '        DrcViolation(\n'
        '            rule_name="TEST_SPACING",\n'
        '            layer="metal1",\n'
        '            severity="error",\n'
        '            message=f"Spacing violation, min={min_spacing}",\n'
        '        )\n'
        '    ]\n'
        '\n'
        'def check_ok(shapes, tech_config, layer_stack, **kwargs):\n'
        '    return []\n',
        encoding='utf-8',
    )

    # postprocess.py — modifies shapes dict in place
    post_script = tmp_path / "postprocess.py"
    post_script.write_text(
        'def add_marker(shapes, tech_config, layer_stack, marker="done", **kwargs):\n'
        '    shapes["_marker"] = marker\n',
        encoding='utf-8',
    )

    # hook.py — chain functions
    hook_script = tmp_path / "hook.py"
    hook_script.write_text(
        'def double_value(cell, shapes, tech_config, **kwargs):\n'
        '    return cell * 2\n'
        '\n'
        'def add_one(cell, shapes, tech_config, **kwargs):\n'
        '    return cell + 1\n',
        encoding='utf-8',
    )

    # error_script.py — raises exception
    error_script = tmp_path / "error_script.py"
    error_script.write_text(
        'def bad_func(shapes, tech_config, layer_stack, **kwargs):\n'
        '    raise RuntimeError("Intentional test error")\n',
        encoding='utf-8',
    )

    return tmp_path


# ---- ScriptConfig tests ----

class TestScriptConfig:
    def test_empty_scripts_default(self):
        """Empty ScriptConfig has all lists empty."""
        cfg = ScriptConfig()
        assert cfg.custom_drc == []
        assert cfg.layer_postprocess == []
        assert cfg.on_after_placement == []
        assert cfg.on_after_routing == []
        assert cfg.on_before_output == []

    def test_has_scripts_false_by_default(self):
        """Default TechConfig has no scripts."""
        from lccommon.tech_loader import load_tech_yaml
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        tech_path = project_root / "librecell-layout" / "examples" / "dummy_tech.yaml"
        if tech_path.exists():
            tech = load_tech_yaml(str(tech_path))
            assert not tech.has_scripts

    def test_load_scripts_from_yaml(self, tmp_path, script_dir):
        """ScriptConfig can be populated from YAML-like data."""
        cfg = ScriptConfig(
            custom_drc=[
                ScriptEntry(path="custom_drc.py", function="check_spacing"),
            ],
            layer_postprocess=[
                ScriptEntry(path="postprocess.py", function="add_marker"),
            ],
        )
        assert len(cfg.custom_drc) == 1
        assert cfg.custom_drc[0].function == "check_spacing"
        assert len(cfg.layer_postprocess) == 1

    def test_script_entry_with_config(self):
        """ScriptEntry can carry extra config dict."""
        entry = ScriptEntry(
            path="foo.py", function="bar",
            config={"threshold": 42, "layer": "metal1"},
        )
        assert entry.config["threshold"] == 42


# ---- ScriptContext tests ----

class TestScriptContext:
    def test_load_function_from_file(self, script_dir):
        """Can load a function from a Python file."""
        entry = ScriptEntry(path="custom_drc.py", function="check_spacing")
        ctx = ScriptContext(ScriptConfig(), base_dir=str(script_dir))
        func = ctx.load_function(entry)
        assert callable(func)

    def test_load_function_not_found_raises(self, script_dir):
        """Missing function raises AttributeError."""
        entry = ScriptEntry(path="custom_drc.py", function="nonexistent")
        ctx = ScriptContext(ScriptConfig(), base_dir=str(script_dir))
        with pytest.raises(AttributeError, match="nonexistent"):
            ctx.load_function(entry)

    def test_load_file_not_found_raises(self, script_dir):
        """Missing script file raises FileNotFoundError."""
        entry = ScriptEntry(path="no_such_file.py", function="foo")
        ctx = ScriptContext(ScriptConfig(), base_dir=str(script_dir))
        with pytest.raises(FileNotFoundError, match="no_such_file.py"):
            ctx.load_function(entry)

    def test_run_custom_drc_empty(self, script_dir):
        """No DRC scripts → empty violation list."""
        cfg = ScriptConfig()
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        violations = ctx.run_custom_drc({}, None, None)
        assert violations == []

    def test_run_custom_drc_collects_violations(self, script_dir):
        """DRC script violations are collected."""
        cfg = ScriptConfig(
            custom_drc=[
                ScriptEntry(path="custom_drc.py", function="check_spacing"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        violations = ctx.run_custom_drc({}, None, None)
        assert len(violations) == 1
        assert violations[0].rule_name == "TEST_SPACING"
        assert violations[0].severity == "error"

    def test_run_custom_drc_multiple_scripts(self, script_dir):
        """Multiple DRC scripts are all executed."""
        cfg = ScriptConfig(
            custom_drc=[
                ScriptEntry(path="custom_drc.py", function="check_spacing"),
                ScriptEntry(path="custom_drc.py", function="check_ok"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        violations = ctx.run_custom_drc({}, None, None)
        # Only 1 violation from check_spacing; check_ok returns empty
        assert len(violations) == 1

    def test_run_layer_postprocess(self, script_dir):
        """layer_postprocess script modifies shapes in-place."""
        cfg = ScriptConfig(
            layer_postprocess=[
                ScriptEntry(path="postprocess.py", function="add_marker"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        shapes = {}
        ctx.run_layer_postprocess(shapes, None, None)
        assert shapes["_marker"] == "done"

    def test_run_hook_chain(self, script_dir):
        """Multiple hooks are chained — each receives the previous result."""
        cfg = ScriptConfig(
            on_after_placement=[
                ScriptEntry(path="hook.py", function="double_value"),
                ScriptEntry(path="hook.py", function="add_one"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        # Start with cell=5: double → 10, add_one → 11
        result = ctx.run_hook('on_after_placement', cell=5, shapes={}, tech_config=None)
        assert result == 11

    def test_config_passed_to_function(self, script_dir):
        """ScriptEntry.config is passed as kwargs to the function."""
        cfg = ScriptConfig(
            custom_drc=[
                ScriptEntry(
                    path="custom_drc.py", function="check_spacing",
                    config={"min_spacing": 200},
                ),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        violations = ctx.run_custom_drc({}, None, None)
        assert "min=200" in violations[0].message

    def test_no_scripts_no_effect(self, script_dir):
        """Empty ScriptConfig causes no side effects."""
        cfg = ScriptConfig()
        ctx = ScriptContext(cfg, base_dir=str(script_dir))

        shapes = {"metal1": "original"}
        ctx.run_layer_postprocess(shapes, None, None)
        assert shapes == {"metal1": "original"}

        violations = ctx.run_custom_drc(shapes, None, None)
        assert violations == []

        result = ctx.run_hook('on_after_placement', cell="unchanged", shapes={}, tech_config=None)
        assert result is None

    def test_script_error_reported_as_violation(self, script_dir):
        """Script error is captured as a DRC violation with severity=error."""
        cfg = ScriptConfig(
            custom_drc=[
                ScriptEntry(path="error_script.py", function="bad_func"),
            ]
        )
        ctx = ScriptContext(cfg, base_dir=str(script_dir))
        violations = ctx.run_custom_drc({}, None, None)
        assert len(violations) == 1
        assert violations[0].rule_name.startswith("SCRIPT_ERROR")
        assert "Intentional test error" in violations[0].message

    def test_module_caching(self, script_dir):
        """Same script file is loaded only once (module cache)."""
        cfg = ScriptConfig()
        ctx = ScriptContext(cfg, base_dir=str(script_dir))

        entry1 = ScriptEntry(path="custom_drc.py", function="check_spacing")
        entry2 = ScriptEntry(path="custom_drc.py", function="check_ok")

        ctx.load_function(entry1)
        ctx.load_function(entry2)

        # Both should come from the same cached module
        assert len(ctx._module_cache) == 1

    def test_absolute_path_script(self, script_dir):
        """Absolute path to script works regardless of base_dir."""
        abs_path = str(script_dir / "custom_drc.py")
        entry = ScriptEntry(path=abs_path, function="check_spacing")
        ctx = ScriptContext(ScriptConfig(), base_dir="/nonexistent")
        func = ctx.load_function(entry)
        assert callable(func)
