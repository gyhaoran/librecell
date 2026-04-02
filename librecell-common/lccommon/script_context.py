#
# Script Context — load and execute user Python scripts for process customization.
#
# Users write plain Python functions (no base class), configured via YAML.
# ScriptContext loads them dynamically and calls them at pipeline hook points.
#
from __future__ import annotations

import importlib.util
import logging
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class DrcViolation(BaseModel):
    """A single DRC violation reported by a custom DRC script."""
    rule_name: str
    layer: str
    severity: str = "error"  # "error" | "warning"
    message: str
    bbox: Optional[Tuple[int, int, int, int]] = None


class ScriptEntry(BaseModel):
    """One script function reference in the YAML config."""
    path: str
    function: str
    config: Dict[str, Any] = {}


class ScriptConfig(BaseModel):
    """All script hook configurations."""
    custom_drc: List[ScriptEntry] = []
    layer_postprocess: List[ScriptEntry] = []
    on_after_placement: List[ScriptEntry] = []
    on_after_routing: List[ScriptEntry] = []
    on_before_output: List[ScriptEntry] = []


# ---------------------------------------------------------------------------
# ScriptContext
# ---------------------------------------------------------------------------


class ScriptContext:
    """Loads and executes user scripts configured in TechConfig.scripts."""

    def __init__(self, script_config: ScriptConfig, base_dir: str = "."):
        self.config = script_config
        self.base_dir = os.path.abspath(base_dir)
        self._module_cache: Dict[str, Any] = {}

    def load_function(self, entry: ScriptEntry) -> Callable:
        """Load a Python function from a ScriptEntry."""
        # Resolve path relative to base_dir
        script_path = entry.path
        if not os.path.isabs(script_path):
            script_path = os.path.join(self.base_dir, script_path)
        script_path = os.path.normpath(script_path)

        if not os.path.isfile(script_path):
            raise FileNotFoundError(
                f"Script file not found: {script_path} "
                f"(resolved from '{entry.path}' with base_dir='{self.base_dir}')"
            )

        # Cache modules by absolute path
        if script_path not in self._module_cache:
            spec = importlib.util.spec_from_file_location(
                f"_user_script_{os.path.basename(script_path).replace('.', '_')}",
                script_path,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._module_cache[script_path] = module

        module = self._module_cache[script_path]
        func = getattr(module, entry.function, None)
        if func is None:
            raise AttributeError(
                f"Function '{entry.function}' not found in script '{script_path}'. "
                f"Available: {[n for n in dir(module) if not n.startswith('_')]}"
            )
        if not callable(func):
            raise TypeError(
                f"'{entry.function}' in '{script_path}' is not callable"
            )
        return func

    def run_custom_drc(self, shapes, tech_config, layer_stack) -> List[DrcViolation]:
        """Execute all custom_drc scripts, collect and return violations."""
        all_violations: List[DrcViolation] = []
        for entry in self.config.custom_drc:
            try:
                func = self.load_function(entry)
                result = func(shapes, tech_config, layer_stack, **entry.config)
                if result:
                    for v in result:
                        if isinstance(v, DrcViolation):
                            all_violations.append(v)
                        elif isinstance(v, dict):
                            all_violations.append(DrcViolation(**v))
                        else:
                            logger.warning(
                                "custom_drc '%s.%s' returned non-DrcViolation item: %s",
                                entry.path, entry.function, type(v).__name__,
                            )
            except Exception as e:
                logger.error(
                    "Error running custom_drc script '%s.%s': %s",
                    entry.path, entry.function, e,
                )
                all_violations.append(DrcViolation(
                    rule_name=f"SCRIPT_ERROR_{entry.function}",
                    layer="*",
                    severity="error",
                    message=f"Script error: {e}",
                ))
        return all_violations

    def run_layer_postprocess(self, shapes, tech_config, layer_stack) -> None:
        """Execute all layer_postprocess scripts (in-place modification of shapes)."""
        for entry in self.config.layer_postprocess:
            try:
                func = self.load_function(entry)
                func(shapes, tech_config, layer_stack, **entry.config)
            except Exception as e:
                logger.error(
                    "Error running layer_postprocess script '%s.%s': %s",
                    entry.path, entry.function, e,
                )

    def run_hook(self, hook_name: str, **kwargs) -> Any:
        """Execute all scripts for a named hook, chaining the first positional argument.

        For hooks like on_after_placement / on_after_routing, the first kwarg
        value is passed through and can be replaced by the return value of each
        script function.
        """
        entries = getattr(self.config, hook_name, [])
        if not entries:
            return None

        # Identify the "primary" argument (first kwarg) to chain through
        kwarg_keys = list(kwargs.keys())
        primary_key = kwarg_keys[0] if kwarg_keys else None
        result = kwargs.get(primary_key) if primary_key else None

        for entry in entries:
            try:
                func = self.load_function(entry)
                merged_kwargs = {**kwargs, **entry.config}
                if primary_key:
                    merged_kwargs[primary_key] = result
                ret = func(**merged_kwargs)
                if ret is not None and primary_key:
                    result = ret
            except Exception as e:
                logger.error(
                    "Error running hook '%s' script '%s.%s': %s",
                    hook_name, entry.path, entry.function, e,
                )

        return result
