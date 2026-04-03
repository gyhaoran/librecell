# Python API Reference

## Module: `lclayout.api`

### `generate_cell()`

Generate a single standard cell layout.

```python
def generate_cell(
    cell_name: str,
    netlist_path: str,
    tech_config: Union[str, TechConfig],
    output_dir: str,
    placer: str = "meta",
    router: str = "dijkstra",
    placement_file: Optional[str] = None,
) -> dict:
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `cell_name` | `str` | Name of the cell in the SPICE netlist |
| `netlist_path` | `str` | Path to SPICE netlist file |
| `tech_config` | `str` or `TechConfig` | Path to YAML tech file or TechConfig instance |
| `output_dir` | `str` | Output directory for GDS/LEF files |
| `placer` | `str` | Placement algorithm: `meta`, `flat`, `hierarchical`, `smt`, `random`, `hillclimb`, `ta` |
| `router` | `str` | Routing algorithm: `dijkstra`, `steiner` |
| `placement_file` | `str` | Optional JSON file for placement store/load |

**Returns:** `dict` with keys:

```python
{
    "cell_name": str,
    "gds_path": str or None,
    "lef_path": str or None,
    "lvs_passed": bool,
    "drc_violations": list,
}
```

**Exceptions:**

- `TypeError` — invalid `tech_config` type
- `ValueError` — unknown placer or router name
- `PlacementError` — placement algorithm failed
- `RoutingError` — routing algorithm failed

---

### `generate_cell_library()`

Generate multiple standard cells in batch.

```python
def generate_cell_library(
    cell_list: List[str],
    netlist_path: str,
    tech_config: Union[str, TechConfig],
    output_dir: str,
    continue_on_error: bool = False,
    num_workers: int = 1,
    **kwargs,
) -> dict:
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `cell_list` | `List[str]` | List of cell names to generate |
| `netlist_path` | `str` | Path to SPICE netlist |
| `tech_config` | `str` or `TechConfig` | Tech config (path string required for parallel) |
| `output_dir` | `str` | Output directory |
| `continue_on_error` | `bool` | If True, skip failed cells instead of stopping |
| `num_workers` | `int` | Number of parallel workers (1 = sequential) |

**Returns:** `dict` with keys:

```python
{
    "success_count": int,
    "failure_count": int,
    "results": {cell_name: result_dict, ...},
    "failures": {cell_name: error_message, ...},
}
```

---

## Module: `lccommon.tech_loader`

### `load_tech_yaml()`

Load a technology configuration from YAML. Results are cached by (path, mtime).

```python
def load_tech_yaml(path: str) -> TechConfig:
```

### `save_tech_yaml()`

Save a TechConfig to YAML.

```python
def save_tech_yaml(config: TechConfig, path: str) -> None:
```

---

## Module: `lccommon.tech_migration`

### `TechMigrator`

```python
class TechMigrator:
    def __init__(self, rule: MigrationRule): ...
    def migrate(self, source: TechConfig) -> TechConfig: ...
    def validate_feasibility(self, source, target, cell_names=None) -> MigrationReport: ...
```

### `MigrationRule`

```python
class MigrationRule(BaseModel):
    source_node: str
    target_node: str
    scale_factor: float = 1.0
    overrides: Dict[str, float] = {}
    fixed_values: Dict[str, Any] = {}
```

### `MigrationReport`

```python
class MigrationReport(BaseModel):
    feasible: bool = True
    warnings: List[str] = []
    errors: List[str] = []
    param_changes: Dict[str, Any] = {}
```

### `load_migration_rule()`

```python
def load_migration_rule(path: str) -> MigrationRule:
```

---

## Module: `lccommon.exceptions`

| Exception | Use Case |
|-----------|----------|
| `LibreCellError` | Base class for all LibreCell exceptions |
| `TechConfigError` | Invalid technology configuration |
| `PlacementError` | Transistor placement failure |
| `RoutingError` | Signal routing failure |
| `LVSError` | LVS verification failure |
| `DRCError` | Design rule violation |
| `NetlistError` | Netlist parsing or circuit lookup error |

---

## Module: `lccommon.logging_config`

### `setup_logging()`

Configure logging for all LibreCell modules.

```python
def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = False,
) -> None:
```

---

## Module: `lccommon.data_types`

### `Transistor`

```python
class Transistor:
    channel_type: ChannelType   # NMOS or PMOS
    source_net: str
    gate_net: str
    drain_net: str
    channel_width: float
    name: str
```

### `ChannelType`

```python
class ChannelType(Enum):
    NMOS = 'nmos'
    PMOS = 'pmos'
```
