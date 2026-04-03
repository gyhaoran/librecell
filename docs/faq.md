# Frequently Asked Questions

## Installation

### Q: KLayout Python module not found?

Install the KLayout standalone Python module:

```bash
pip install klayout
```

If you're using KLayout's built-in Python, add its path to `PYTHONPATH`.

### Q: Which Python versions are supported?

Python 3.10 and above. Pydantic v2 requires Python 3.8+, but LibreCell uses features from 3.10+.

## Technology Configuration

### Q: How do I create a config for a new process node?

The easiest approach is to use `TechMigrator` to scale from an existing config:

```python
from lccommon.tech_loader import load_tech_yaml, save_tech_yaml
from lccommon.tech_migration import TechMigrator, MigrationRule

source = load_tech_yaml("examples/cmos_90nm.yaml")
rule = MigrationRule(
    source_node="90nm",
    target_node="65nm",
    scale_factor=65.0 / 90.0,
    fixed_values={"node": "65nm"},
)
target = TechMigrator(rule).migrate(source)
save_tech_yaml(target, "my_65nm.yaml")
```

Then manually tune parameters like `transistor_offset_y` to satisfy DRC.

### Q: What's the difference between `unit_cell_height` and `num_tracks * track_pitch`?

They're equivalent. You can specify either:
- `unit_cell_height` directly, OR
- `num_tracks` + `track_pitch` (height is auto-computed)

If all three are given, a warning is emitted if they disagree.

### Q: Can I use Python tech files instead of YAML?

Yes. The CLI `--tech` flag accepts both `.yaml` and `.py` files. Python tech modules are auto-converted to `TechConfig` internally. YAML is recommended for new projects.

## Cell Generation

### Q: LVS fails — how do I debug?

Run with `--verbose` to see the extracted vs. reference netlists:

```bash
lclayout --cell INVX1 --netlist cells.sp --tech my_tech.yaml -v
```

Common causes:
- **Net mismatch**: A signal was routed to the wrong terminal
- **Missing device**: Transistor not placed or connected
- **Channel width**: Layout engine resized a transistor to meet DRC

Note: L (gate length) and W (channel width) parameters are excluded from LVS comparison since the layout engine determines these from the technology configuration.

### Q: A cell fails with "spacing rules violated"?

The `transistor_offset_y` is too small for the DRC rules. It must satisfy:

```
transistor_offset_y >= max(
    ceil(active_spacing / 2),
    gate_extension + ceil(poly_spacing / 2)
)
```

Increase `transistor_offset_y` in your tech config.

### Q: How do I generate cells in parallel?

```python
result = generate_cell_library(
    cell_list=["INVX1", "NAND2X1", "NOR2X1"],
    netlist_path="cells.sp",
    tech_config="my_tech.yaml",  # Must be a path for parallel
    output_dir="output/",
    num_workers=4,
    continue_on_error=True,
)
```

Note: `num_workers > 1` requires `tech_config` to be a file path (not a `TechConfig` object) for serialization across processes.

### Q: What cells can LibreCell generate?

Any combinational or sequential standard cell defined in a SPICE netlist with NMOS/PMOS transistors. Tested cells include: INVX1, INVX2, NAND2X1, NOR2X1, AND2X1, OR2X1, BUFX2, DFFPOSX1, AOI21X1.

## Errors

### Q: What do the custom exceptions mean?

| Exception | Meaning |
|-----------|---------|
| `TechConfigError` | Your tech YAML has a missing or invalid field |
| `PlacementError` | The placer couldn't find a valid transistor arrangement |
| `RoutingError` | The router couldn't connect all signals |
| `NetlistError` | The cell name wasn't found in the SPICE netlist |
| `LVSError` | Layout doesn't match the schematic |
| `DRCError` | Layout violates design rules |

### Q: "Placement problem not satisfiable"?

The SMT placer couldn't find a valid arrangement. Try:
1. Use the default `meta` placer instead of `smt`
2. Check that transistor count isn't too large for the cell width
3. Verify `unit_cell_width` is large enough

## FinFET Support

### Q: Does LibreCell support FinFET?

Not yet. The `TechConfig` has reserved fields (`process_type`, `fin_pitch`, `fin_width`, `num_fins_per_device`) for future FinFET support. Currently only `process_type: planar` is functional.
