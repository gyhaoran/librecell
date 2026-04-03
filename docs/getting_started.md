# Getting Started with LibreCell

## Overview

LibreCell is an open-source standard cell layout generator. It takes SPICE netlists and technology configuration files as input and produces GDSII layout and LEF abstract files.

## Installation

```bash
# Clone the repository
git clone https://github.com/librecell/librecell.git
cd librecell

# Install all packages in development mode
pip install -e librecell-common
pip install -e librecell-layout
pip install -e librecell-lib

# Install development dependencies
pip install -r requirements-dev.txt
```

### Dependencies

- Python 3.10+
- KLayout (Python module: `klayout`)
- NetworkX
- NumPy
- PyYAML
- Pydantic v2

## Quick Start

### 1. Generate a single cell (CLI)

```bash
lclayout --cell INVX1 \
         --netlist examples/cells.sp \
         --tech librecell-layout/examples/cmos_180nm.yaml \
         --output-dir output/
```

### 2. Generate a single cell (Python API)

```python
from lclayout.api import generate_cell

result = generate_cell(
    cell_name="INVX1",
    netlist_path="examples/cells.sp",
    tech_config="librecell-layout/examples/cmos_180nm.yaml",
    output_dir="output/",
)
print(f"GDS: {result['gds_path']}")
print(f"LVS passed: {result['lvs_passed']}")
```

### 3. Generate a cell library (Python API)

```python
from lclayout.api import generate_cell_library

result = generate_cell_library(
    cell_list=["INVX1", "NAND2X1", "NOR2X1", "BUFX2"],
    netlist_path="examples/cells.sp",
    tech_config="librecell-layout/examples/cmos_180nm.yaml",
    output_dir="output/",
    continue_on_error=True,
)
print(f"Generated {result['success_count']} cells")
```

## Project Structure

```
librecell/
  librecell-common/   # Shared data types, tech config, utilities
    lccommon/
      tech_config.py     # Pydantic TechConfig model
      tech_loader.py     # YAML load/save
      tech_migration.py  # Process node migration engine
      data_types.py      # Transistor, Cell, ChannelType
      exceptions.py      # Custom exception classes
  librecell-layout/   # Layout generation engine
    lclayout/
      api.py             # Python API (generate_cell, generate_cell_library)
      standalone.py      # CLI entry point + LcLayout engine
      place/             # Placement algorithms
      graphrouter/       # Routing algorithms
      lvs/               # Layout vs. Schematic verification
      writer/            # GDS, LEF, MAG output writers
  librecell-lib/      # Cell characterization (timing, power)
```

## Supported Technology Nodes

LibreCell ships with example configurations for:

- **180nm** CMOS (`cmos_180nm.yaml`)
- **90nm** CMOS (`cmos_90nm.yaml`)
- **55nm** CMOS (`cmos_55nm.yaml`) — generated via migration from 90nm
- **BCD** (Bipolar-CMOS-DMOS) (`bcd_tech.yaml`)
- **Multi-track** (7T, 9T, 10T) dummy configurations

## Next Steps

- [Tech Config Guide](tech_config_guide.md) — how to write technology configurations
- [Migration Guide](migration_guide.md) — migrating between process nodes
- [Scripting Guide](scripting_guide.md) — custom DRC scripts and hooks
- [API Reference](api_reference.md) — full Python API documentation
- [FAQ](faq.md) — common questions and troubleshooting
