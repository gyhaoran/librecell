# Process Migration Guide

## Overview

LibreCell's `TechMigrator` enables migrating technology configurations between process nodes or track heights. It scales geometric parameters, applies overrides, and validates feasibility.

## Concepts

- **MigrationRule**: Defines source→target transformation (scale factor, overrides, fixed values)
- **TechMigrator**: Applies a rule to a source TechConfig, producing a target TechConfig
- **MigrationReport**: Feasibility analysis with warnings/errors

## Migration Rules (YAML)

### Cross-Node Migration (90nm → 55nm)

```yaml
# migration/90nm_to_55nm.yaml
source_node: "90nm"
target_node: "55nm"
scale_factor: 0.611     # 55/90 ≈ 0.611
overrides: {}           # Optional per-path scale overrides
fixed_values:
  node: "55nm"
```

### Track Migration (7T → 9T)

```yaml
# migration/7t_to_9t.yaml
source_node: "7t"
target_node: "9t"
scale_factor: 1.0       # No geometric scaling
fixed_values:
  cell.num_tracks: 9     # Override track count
```

### Downward Track Migration (9T → 7T)

```yaml
source_node: "9t"
target_node: "7t"
scale_factor: 1.0
fixed_values:
  cell.num_tracks: 7
```

## Scaling Rules

| Value Type | Behavior |
|-----------|----------|
| `float` (geometric) | Multiplied by `scale_factor`, rounded to integer |
| `int` (track count, etc.) | Not scaled |
| `str` (layer names) | Not scaled |
| `list` / `dict` | Recursively processed |
| `overrides` path | Uses override factor instead of `scale_factor` |
| `fixed_values` path | Set to exact value |

**Fields NOT scaled**: `name`, `node`, `db_unit`, `layers`, `vias`, `via_connectivity`, `power_domains`, `bcd`, `output_map`, `writers`, `extensions`.

## Python API

### Basic Migration

```python
from lccommon.tech_loader import load_tech_yaml
from lccommon.tech_migration import TechMigrator, load_migration_rule

# Load source config and migration rule
source = load_tech_yaml("examples/cmos_90nm.yaml")
rule = load_migration_rule("examples/migration/90nm_to_55nm.yaml")

# Migrate
migrator = TechMigrator(rule)
target = migrator.migrate(source)

print(f"Gate length: {source.cell.gate_length} → {target.cell.gate_length}")
# Gate length: 90.0 → 55.0
```

### Programmatic Rule

```python
from lccommon.tech_migration import MigrationRule, TechMigrator

rule = MigrationRule(
    source_node="9t",
    target_node="7t",
    scale_factor=1.0,
    fixed_values={"cell.num_tracks": 7},
)
migrator = TechMigrator(rule)
target = migrator.migrate(source)
```

### Feasibility Check

```python
report = migrator.validate_feasibility(
    source, target,
    cell_names=["INVX1", "NAND2X1", "DFFPOSX1"],
)
print(f"Feasible: {report.feasible}")
for w in report.warnings:
    print(f"  WARNING: {w}")
for e in report.errors:
    print(f"  ERROR: {e}")
```

### Save Migrated Config

```python
from lccommon.tech_loader import save_tech_yaml

save_tech_yaml(target, "output/cmos_55nm.yaml")
```

## CLI

```bash
lclayout-migrate \
    --source examples/cmos_90nm.yaml \
    --rule examples/migration/90nm_to_55nm.yaml \
    --output output/cmos_55nm.yaml \
    --validate \
    --cells INVX1 NAND2X1
```

## Available Migration Rules

| Rule File | Direction | Scale |
|-----------|-----------|-------|
| `90nm_to_55nm.yaml` | Cross-node | 0.611 |
| `180nm_to_90nm.yaml` | Cross-node | 0.5 |
| `7t_to_9t.yaml` | Track up | 1.0 |
| `9t_to_7t.yaml` | Track down | 1.0 |
| `10t_to_7t.yaml` | Track down | 1.0 |
| `7t_to_6t.yaml` | Track down | 1.0 |

## Caveats

- Downward track migration may make complex cells infeasible — always run `validate_feasibility()`
- Multi-stage cells (BUFX2, INVX2) may have routing conflicts at very small nodes
- After migration, verify with `generate_cell()` that cells actually produce valid layouts
