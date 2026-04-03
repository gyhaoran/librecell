# Technology Configuration Guide

## Overview

LibreCell uses YAML-based technology configuration files to describe process design rules, layer definitions, and layout parameters. The configuration is validated by a Pydantic v2 model (`TechConfig`).

## File Structure

A tech config YAML has these top-level sections:

```yaml
name: my_process           # Human-readable name
node: "180nm"              # Process node identifier
db_unit: 1.0e-09           # Database unit in meters (1nm)

cell:                      # Cell geometry parameters
  ...
routing:                   # Routing grid and wire parameters
  ...
drc:                       # Design rule check constraints
  ...
layers:                    # Layer definitions
  ...
vias:                      # Via definitions
  ...
via_connectivity:          # Which layers connect through which vias
  ...
output_map:                # Layer name → GDS (layer, purpose) mapping
  ...
writers:                   # Output format configuration
  ...
```

## Cell Configuration (`cell:`)

```yaml
cell:
  unit_cell_width: 400.0        # Width of one placement grid unit (nm)
  unit_cell_height: 2400.0      # Total cell height (nm)
  gate_length: 180.0            # Transistor gate length (nm)
  gate_extension: 100.0         # Gate poly extension beyond active (nm)
  transistor_offset_y: 125.0    # Transistor Y offset from cell edge (nm)
  power_rail_width: 360.0       # VDD/GND rail width (nm)
  minimum_gate_width_nfet: 200.0  # Min NMOS channel width (nm)
  minimum_gate_width_pfet: 200.0  # Min PMOS channel width (nm)
  minimum_pin_width: 50.0       # Min pin geometry width (nm)
  transistor_channel_width_sizing: 1.0  # Width scaling factor
  pin_layer: metal2             # Layer for pin markers
  power_layer: metal2           # Layer for power labels

  # Multi-track support (optional — alternative to explicit unit_cell_height)
  num_tracks: 7                 # Number of routing tracks
  track_pitch: 200.0            # Pitch between tracks (nm)
  # unit_cell_height = num_tracks * track_pitch (auto-computed if omitted)
```

## Routing Configuration (`routing:`)

```yaml
routing:
  routing_grid_pitch_x: 200.0   # Horizontal grid pitch (nm)
  routing_grid_pitch_y: 200.0   # Vertical grid pitch (nm)
  grid_offset_x: 0              # Grid X offset
  grid_offset_y: 0              # Grid Y offset
  orientation_change_penalty: 100  # Cost penalty for via layer changes

  routing_layers:               # Available routing layers with direction
    metal1: h                   # horizontal
    metal2: v                   # vertical

  wire_width:                   # Default wire width per layer (nm)
    metal1: 100
    metal2: 100

  via_size:                     # Via cut size per via type (nm)
    ndiff_contact: 100
    pdiff_contact: 100
    poly_contact: 100
    metal1_metal2: 100

  connectable_layers:           # Layer pairs that can connect
    - [metal1, ndiffusion]
    - [metal1, pdiffusion]
    - [metal1, poly]
    - [metal1, metal2]
```

## DRC Configuration (`drc:`)

```yaml
drc:
  minimum_width:                # Minimum width per layer (nm)
    ndiffusion: 100
    poly: 100
    metal1: 100

  min_spacing:                  # Minimum spacing between layers (nm)
    ndiffusion:
      ndiffusion: 50
    poly:
      poly: 50
      ndiffusion: 50
    metal1:
      metal1: 50

  minimum_enclosure:            # Enclosure rules (nm)
    ndiffusion:
      ndiff_contact: 30
    poly:
      poly_contact: 30

  minimum_notch: {}             # Minimum notch width per layer
  min_area: {}                  # Minimum area per layer
```

## Layer Definitions (`layers:`)

```yaml
layers:
  - {name: ndiffusion, gds_layer: 1, gds_purpose: 0}
  - {name: pdiffusion, gds_layer: 2, gds_purpose: 0}
  - {name: nwell, gds_layer: 3, gds_purpose: 0}
  - {name: poly, gds_layer: 5, gds_purpose: 0}
  - {name: metal1, gds_layer: 6, gds_purpose: 0}
  - {name: metal2, gds_layer: 7, gds_purpose: 0}
```

## Via Connectivity (`via_connectivity:`)

```yaml
via_connectivity:
  - {via: ndiff_contact, bottom: ndiffusion, top: metal1}
  - {via: pdiff_contact, bottom: pdiffusion, top: metal1}
  - {via: poly_contact, bottom: poly, top: metal1}
  - {via: metal1_metal2, bottom: metal1, top: metal2}
```

## Output Map (`output_map:`)

Maps internal layer names to GDS layer/purpose pairs:

```yaml
output_map:
  ndiffusion: [1, 0]
  pdiffusion: [2, 0]
  nwell: [3, 0]
  poly: [5, 0]
  metal1: [6, 0]
  metal2: [7, 0]
  metal2_label: [7, 5]
  metal2_pin: [7, 6]
```

## Writers (`writers:`)

```yaml
writers:
  - type: lef
    db_unit: 1.0e-06    # LEF uses microns
    site: CORE
  - type: gds
```

## Process Type (FinFET Extension)

```yaml
process_type: planar    # "planar" (default) or "finfet" (reserved)
# FinFET parameters (reserved, not yet processed):
# fin_pitch: 28.0
# fin_width: 7.0
# num_fins_per_device: 2
```

## BCD Extension

For Bipolar-CMOS-DMOS processes:

```yaml
bcd:
  enabled: true
  thick_oxide_layer: thick_oxide
  hv_nwell_layer: hv_nwell
  hv_threshold_voltage: 5.0

power_domains:
  - name: core
    supply_voltage: 1.8
    ground_net: gnd
    supply_net: vdd
  - name: io
    supply_voltage: 3.3
    is_high_voltage: true
    ground_net: gnd
    supply_net: vddio
```

## Validation

Load and validate a tech config:

```python
from lccommon.tech_loader import load_tech_yaml

tech = load_tech_yaml("my_tech.yaml")
print(f"Node: {tech.node}")
print(f"Cell height: {tech.cell.unit_cell_height} nm")
print(f"Gate length: {tech.cell.gate_length} nm")
```

Validation errors raise `TechConfigError` with a description of the missing/invalid field.
