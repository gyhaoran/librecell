# Scripting Guide

## Overview

LibreCell supports custom scripts that hook into the cell generation pipeline. Scripts can implement custom DRC checks, post-process layers, and modify placement/routing results.

## Script Types

| Hook | When It Runs | Input | Output |
|------|-------------|-------|--------|
| `custom_drc` | After layout generation | shapes, tech_config, layer_stack | List of `DrcViolation` |
| `layer_postprocess` | After routing, before output | shapes, tech_config, layer_stack | Modified shapes (in-place) |
| `on_after_placement` | After transistor placement | cell, shapes, tech_config | Optional modified cell |
| `on_after_routing` | After signal routing | routing_trees, shapes, tech_config | Optional modified routing |

## Writing a Custom DRC Script

### 1. Create the script file

```python
# my_drc.py
from lccommon.script_context import DrcViolation

def check_my_rules(shapes, tech_config, layer_stack, **kwargs):
    """Custom DRC check function.

    Args:
        shapes: Dict[str, pya.Shapes] — layer name to shapes mapping
        tech_config: TechConfig instance
        layer_stack: LayerStack instance

    Returns:
        List of DrcViolation objects (empty = all checks passed)
    """
    violations = []

    # Example: check that metal1 shapes are wider than 200nm
    min_width = 200
    if 'metal1' in shapes:
        for shape in shapes['metal1'].each():
            box = shape.bbox()
            if box.width() < min_width:
                violations.append(DrcViolation(
                    rule_name="metal1_min_width",
                    message=f"Metal1 width {box.width()} < {min_width}",
                    severity="warning",
                    layer="metal1",
                ))

    return violations
```

### 2. Attach to tech config

In your YAML tech config:

```yaml
scripts:
  custom_drc:
    - path: my_drc.py
      function: check_my_rules
```

Or via Python API:

```python
from lccommon.script_context import ScriptEntry, ScriptConfig

tech.scripts = ScriptConfig(
    custom_drc=[
        ScriptEntry(path="my_drc.py", function="check_my_rules"),
    ]
)
tech._config_dir = "/path/to/script/directory"
```

### 3. Run and check results

```python
from lclayout.api import generate_cell

result = generate_cell(
    cell_name="INVX1",
    netlist_path="cells.sp",
    tech_config=tech,
    output_dir="output/",
)
for v in result["drc_violations"]:
    print(f"[{v['severity']}] {v['rule_name']}: {v['message']}")
```

## Writing a Layer Post-Process Script

```python
# my_postprocess.py
import klayout.db as pya

def smooth_metal1(shapes, tech_config, layer_stack, **kwargs):
    """Post-process metal1 shapes to merge overlapping regions."""
    if 'metal1' in shapes:
        region = pya.Region(shapes['metal1'])
        merged = region.merged()
        shapes['metal1'].clear()
        shapes['metal1'].insert(merged)
```

Attach in YAML:

```yaml
scripts:
  layer_postprocess:
    - path: my_postprocess.py
      function: smooth_metal1
```

## DrcViolation Model

```python
class DrcViolation(BaseModel):
    rule_name: str          # Name of the violated rule
    message: str            # Human-readable description
    severity: str = "error" # "error" or "warning"
    layer: str = ""         # Affected layer (optional)
    bbox: Optional[list] = None  # Bounding box [x1, y1, x2, y2]
```

## Script Resolution

Scripts are resolved relative to the tech config file's directory (`_config_dir`). If the script path is absolute, it's used directly.

## Error Handling

- If a script file is not found: `FileNotFoundError` is raised
- If the function doesn't exist in the module: `AttributeError` is raised
- If the callable is not actually callable: `TypeError` is raised
- Script exceptions during generation are logged but don't halt the pipeline (unless severity is "error")
