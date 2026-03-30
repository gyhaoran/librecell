"""
Task 03: Unit tests for TechConfig Pydantic models and YAML loading.
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "librecell-layout" / "examples"


# ---------------------------------------------------------------------------
# Model creation & validation
# ---------------------------------------------------------------------------

class TestTechConfigModel:
    """Test TechConfig Pydantic v2 model creation and validation."""

    def test_create_from_minimal_dict(self):
        """TechConfig can be created from a minimal dict."""
        from lccommon.tech_config import TechConfig
        data = {
            "cell": {
                "unit_cell_width": 400,
                "unit_cell_height": 2400,
                "gate_length": 50,
                "gate_extension": 100,
                "transistor_offset_y": 125,
                "power_rail_width": 360,
                "minimum_gate_width_nfet": 200,
                "minimum_gate_width_pfet": 200,
                "minimum_pin_width": 50,
            },
            "routing": {
                "routing_grid_pitch_x": 200,
                "routing_grid_pitch_y": 300,
            },
        }
        config = TechConfig.model_validate(data)
        assert config.cell.unit_cell_width == 400
        assert config.db_unit == 1e-9  # default

    def test_validation_error_missing_required(self):
        """Missing required fields raise ValidationError."""
        from pydantic import ValidationError
        from lccommon.tech_config import TechConfig
        with pytest.raises(ValidationError):
            TechConfig.model_validate({"cell": {}})

    def test_validation_error_wrong_type(self):
        """Wrong field type raises ValidationError."""
        from pydantic import ValidationError
        from lccommon.tech_config import TechConfig
        with pytest.raises(ValidationError):
            TechConfig.model_validate({
                "cell": {
                    "unit_cell_width": "not_a_number",
                    "unit_cell_height": 2400,
                    "gate_length": 50,
                    "gate_extension": 100,
                    "transistor_offset_y": 125,
                    "power_rail_width": 360,
                    "minimum_gate_width_nfet": 200,
                    "minimum_gate_width_pfet": 200,
                    "minimum_pin_width": 50,
                },
                "routing": {"routing_grid_pitch_x": 200, "routing_grid_pitch_y": 300},
            })

    def test_default_values(self):
        """Optional fields use correct defaults."""
        from lccommon.tech_config import TechConfig
        data = {
            "cell": {
                "unit_cell_width": 400, "unit_cell_height": 2400,
                "gate_length": 50, "gate_extension": 100,
                "transistor_offset_y": 125, "power_rail_width": 360,
                "minimum_gate_width_nfet": 200, "minimum_gate_width_pfet": 200,
                "minimum_pin_width": 50,
            },
            "routing": {"routing_grid_pitch_x": 200, "routing_grid_pitch_y": 300},
        }
        config = TechConfig.model_validate(data)
        assert config.cell.transistor_channel_width_sizing == 1.0
        assert config.routing.orientation_change_penalty == 100
        assert config.db_unit == 1e-9
        assert config.name == "unnamed"


# ---------------------------------------------------------------------------
# Flat property delegation
# ---------------------------------------------------------------------------

class TestFlatProperties:
    """Flat @property accessors delegate to sub-models correctly."""

    @pytest.fixture
    def config(self):
        from lccommon.tech_config import TechConfig
        return TechConfig.model_validate({
            "db_unit": 1e-9,
            "cell": {
                "unit_cell_width": 400, "unit_cell_height": 2400,
                "gate_length": 50, "gate_extension": 100,
                "transistor_offset_y": 125, "power_rail_width": 360,
                "minimum_gate_width_nfet": 200, "minimum_gate_width_pfet": 200,
                "minimum_pin_width": 50, "pin_layer": "metal2",
                "power_layer": "metal2",
                "transistor_channel_width_sizing": 1.5,
            },
            "routing": {
                "routing_grid_pitch_x": 200, "routing_grid_pitch_y": 300,
                "grid_offset_x": 200, "grid_offset_y": 150,
                "orientation_change_penalty": 100,
                "wire_width": {"metal1": 100},
                "wire_width_horizontal": {"metal1": 100},
                "via_size": {"via1": 100},
                "weights_horizontal": {"metal1": 1},
                "weights_vertical": {"metal1": 1},
                "connectable_layers": ["nwell"],
                "routing_layers": {"metal1": "hv"},
            },
            "drc": {
                "minimum_width": {"metal1": 100},
                "minimum_notch": {"metal1": 50},
                "min_area": {"metal1": 10000},
                "min_spacing": {"ndiffusion": {"ndiffusion": 50}},
                "minimum_enclosure": {"metal1": {"via1": 20}},
            },
            "via": {
                "via_weights": {"metal1": {"metal2": 400}},
                "multi_via": {"metal1": {"metal2": 1}},
            },
        })

    # Cell properties
    def test_unit_cell_width(self, config):
        assert config.unit_cell_width == 400

    def test_unit_cell_height(self, config):
        assert config.unit_cell_height == 2400

    def test_gate_length(self, config):
        assert config.gate_length == 50

    def test_gate_extension(self, config):
        assert config.gate_extension == 100

    def test_transistor_offset_y(self, config):
        assert config.transistor_offset_y == 125

    def test_power_rail_width(self, config):
        assert config.power_rail_width == 360

    def test_minimum_gate_width_nfet(self, config):
        assert config.minimum_gate_width_nfet == 200

    def test_minimum_gate_width_pfet(self, config):
        assert config.minimum_gate_width_pfet == 200

    def test_minimum_pin_width(self, config):
        assert config.minimum_pin_width == 50

    def test_transistor_channel_width_sizing(self, config):
        assert config.transistor_channel_width_sizing == 1.5

    def test_pin_layer(self, config):
        assert config.pin_layer == "metal2"

    def test_power_layer(self, config):
        assert config.power_layer == "metal2"

    # Routing properties
    def test_routing_grid_pitch_x(self, config):
        assert config.routing_grid_pitch_x == 200

    def test_routing_grid_pitch_y(self, config):
        assert config.routing_grid_pitch_y == 300

    def test_grid_offset_x(self, config):
        assert config.grid_offset_x == 200

    def test_grid_offset_y(self, config):
        assert config.grid_offset_y == 150

    def test_orientation_change_penalty(self, config):
        assert config.orientation_change_penalty == 100

    def test_wire_width(self, config):
        assert config.wire_width == {"metal1": 100}

    def test_routing_layers(self, config):
        assert config.routing_layers == {"metal1": "hv"}

    def test_connectable_layers(self, config):
        assert config.connectable_layers == {"nwell"}
        assert isinstance(config.connectable_layers, set)

    # DRC properties
    def test_minimum_width(self, config):
        assert config.minimum_width == {"metal1": 100}

    def test_minimum_notch(self, config):
        assert config.minimum_notch == {"metal1": 50}

    def test_min_area(self, config):
        assert config.min_area == {"metal1": 10000}


# ---------------------------------------------------------------------------
# Tuple-key conversion
# ---------------------------------------------------------------------------

class TestTupleKeyConversion:
    """Nested dict ↔ tuple-key dict conversion."""

    @pytest.fixture
    def config(self):
        from lccommon.tech_config import TechConfig
        return TechConfig.model_validate({
            "cell": {
                "unit_cell_width": 400, "unit_cell_height": 2400,
                "gate_length": 50, "gate_extension": 100,
                "transistor_offset_y": 125, "power_rail_width": 360,
                "minimum_gate_width_nfet": 200, "minimum_gate_width_pfet": 200,
                "minimum_pin_width": 50,
            },
            "routing": {"routing_grid_pitch_x": 200, "routing_grid_pitch_y": 300},
            "drc": {
                "min_spacing": {
                    "ndiffusion": {"ndiffusion": 50, "poly_contact": 10},
                    "metal1": {"metal1": 50},
                },
                "minimum_enclosure": {
                    "metal1": {"via1": 20, "ndiff_contact": 10},
                    "nwell": {"pdiffusion": 100},
                },
            },
            "via": {
                "via_weights": {"metal1": {"ndiffusion": 500, "metal2": 400}},
                "multi_via": {"metal1": {"metal2": 1}},
            },
        })

    def test_min_spacing_returns_tuple_keys(self, config):
        ms = config.min_spacing
        assert isinstance(ms, dict)
        assert ("ndiffusion", "ndiffusion") in ms
        assert ms[("ndiffusion", "ndiffusion")] == 50
        assert ms[("ndiffusion", "poly_contact")] == 10
        assert ms[("metal1", "metal1")] == 50

    def test_minimum_enclosure_returns_tuple_keys(self, config):
        me = config.minimum_enclosure
        assert me[("metal1", "via1")] == 20
        assert me[("nwell", "pdiffusion")] == 100

    def test_via_weights_returns_tuple_keys(self, config):
        vw = config.via_weights
        assert vw[("metal1", "ndiffusion")] == 500
        assert vw[("metal1", "metal2")] == 400

    def test_multi_via_returns_tuple_keys(self, config):
        mv = config.multi_via
        assert mv[("metal1", "metal2")] == 1

    def test_nested_to_tuple_roundtrip(self):
        from lccommon.tech_config import TechConfig
        nested = {"a": {"b": 1, "c": 2}, "d": {"e": 3}}
        tuples = TechConfig._nested_to_tuple_keys(nested)
        back = TechConfig._tuple_keys_to_nested(tuples)
        assert back == nested

    def test_min_spacing_is_cached(self, config):
        """Second access returns same object (cached)."""
        ms1 = config.min_spacing
        ms2 = config.min_spacing
        assert ms1 is ms2


# ---------------------------------------------------------------------------
# Output map conversion
# ---------------------------------------------------------------------------

class TestOutputMap:
    """output_map list→tuple conversion."""

    def test_single_layer(self):
        from lccommon.tech_config import TechConfig
        resolved = TechConfig._resolve_output_map({"ndiffusion": [1, 0]})
        assert resolved["ndiffusion"] == (1, 0)

    def test_multi_layer(self):
        from lccommon.tech_config import TechConfig
        resolved = TechConfig._resolve_output_map({"nwell": [[2, 0], [2, 1]]})
        assert resolved["nwell"] == [(2, 0), (2, 1)]

    def test_output_map_resolved_property(self):
        from lccommon.tech_config import TechConfig
        config = TechConfig.model_validate({
            "cell": {
                "unit_cell_width": 400, "unit_cell_height": 2400,
                "gate_length": 50, "gate_extension": 100,
                "transistor_offset_y": 125, "power_rail_width": 360,
                "minimum_gate_width_nfet": 200, "minimum_gate_width_pfet": 200,
                "minimum_pin_width": 50,
            },
            "routing": {"routing_grid_pitch_x": 200, "routing_grid_pitch_y": 300},
            "output_map": {
                "ndiffusion": [1, 0],
                "nwell": [[2, 0], [2, 1]],
            },
        })
        om = config.output_map_resolved
        assert om["ndiffusion"] == (1, 0)
        assert om["nwell"] == [(2, 0), (2, 1)]


# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------

class TestYamlLoading:
    """Load YAML tech files."""

    def test_load_dummy_tech_yaml(self):
        """Load dummy_tech.yaml and verify key attributes."""
        from lccommon.tech_loader import load_tech_yaml
        path = str(EXAMPLES_DIR / "dummy_tech.yaml")
        config = load_tech_yaml(path)
        assert config.db_unit == 1e-9
        assert config.cell.unit_cell_width == 400
        assert config.cell.unit_cell_height == 2400
        assert config.cell.gate_length == 50

    def test_load_dummy_tech_layer_names(self):
        """Layer-keyed dicts contain expected keys."""
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        assert "metal1" in config.wire_width
        assert "metal2" in config.wire_width
        assert "poly" in config.routing_layers

    def test_load_dummy_tech_spacing(self):
        """min_spacing returns tuple-key format with correct values."""
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        ms = config.min_spacing
        assert ms[("ndiffusion", "ndiffusion")] == 50
        assert ms[("metal1", "metal1")] == 50
        assert ms[("metal2", "metal2")] == 100

    def test_load_dummy_tech_enclosure(self):
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        me = config.minimum_enclosure
        assert me[("metal1", "via1")] == 20
        assert me[("nwell", "pdiffusion")] == 100

    def test_load_dummy_tech_output_map(self):
        """output_map resolves correctly (single + multi layer)."""
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        om = config.output_map_resolved
        assert om["ndiffusion"] == (1, 0)
        assert om["nwell"] == [(2, 0), (2, 1)]
        assert om["metal1"] == (6, 0)

    def test_load_dummy_tech_power_domains(self):
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        assert len(config.power_domains) >= 1
        assert config.power_domains[0].supply_net == "VDD"

    def test_load_cmos_180nm(self):
        """cmos_180nm.yaml loads successfully."""
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "cmos_180nm.yaml"))
        assert config.node == "180nm"
        assert config.cell.gate_length == 180

    def test_load_dummy_tech_writers(self):
        """Writer configs are parsed (3 writers: mag, lef, gds)."""
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        assert len(config.writers) == 3

    def test_writer_lazy_instantiation(self):
        """output_writers property returns Writer instances."""
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        writers = config.output_writers
        assert len(writers) == 3
        # Check types
        from lclayout.writer.magic_writer import MagWriter
        from lclayout.writer.lef_writer import LefWriter
        from lclayout.writer.gds_writer import GdsWriter
        assert isinstance(writers[0], MagWriter)
        assert isinstance(writers[1], LefWriter)
        assert isinstance(writers[2], GdsWriter)

    def test_writer_cached(self):
        """Second output_writers access returns same list."""
        from lccommon.tech_loader import load_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        w1 = config.output_writers
        w2 = config.output_writers
        assert w1 is w2


# ---------------------------------------------------------------------------
# Python → TechConfig conversion
# ---------------------------------------------------------------------------

class TestPythonConversion:
    """python_tech_to_config() correctly converts Python tech modules."""

    @pytest.fixture
    def py_config(self):
        from lclayout.tech_util import load_tech_file_raw
        from lccommon.tech_loader import python_tech_to_config
        module = load_tech_file_raw(str(EXAMPLES_DIR / "dummy_tech.py"))
        return python_tech_to_config(module)

    def test_scalar_values(self, py_config):
        assert py_config.db_unit == 1e-9
        assert py_config.unit_cell_width == 400
        assert py_config.gate_length == 50

    def test_spacing_conversion(self, py_config):
        """Tuple-key min_spacing from Python module is accessible."""
        ms = py_config.min_spacing
        assert ms[("ndiffusion", "ndiffusion")] == 50
        assert ms[("pdiffusion", "ndiffusion")] == 50

    def test_enclosure_conversion(self, py_config):
        me = py_config.minimum_enclosure
        assert me[("metal1", "via1")] == 20

    def test_via_weights_conversion(self, py_config):
        vw = py_config.via_weights
        assert vw[("metal1", "ndiffusion")] == 500

    def test_output_map_conversion(self, py_config):
        om = py_config.output_map_resolved
        assert om["ndiffusion"] == (1, 0)
        assert om["nwell"] == [(2, 0), (2, 1)]

    def test_writers_conversion(self, py_config):
        """Python Writer instances reverse-engineered to WriterConfig."""
        assert len(py_config.writers) == 3

    def test_connectable_layers(self, py_config):
        assert py_config.connectable_layers == {"nwell"}

    def test_python_yaml_equivalence(self, py_config):
        """Python and YAML configs produce equivalent values."""
        from lccommon.tech_loader import load_tech_yaml
        yaml_config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))

        assert py_config.unit_cell_width == yaml_config.unit_cell_width
        assert py_config.unit_cell_height == yaml_config.unit_cell_height
        assert py_config.gate_length == yaml_config.gate_length
        assert py_config.routing_grid_pitch_x == yaml_config.routing_grid_pitch_x
        assert py_config.wire_width == yaml_config.wire_width
        assert py_config.min_spacing == yaml_config.min_spacing
        assert py_config.minimum_enclosure == yaml_config.minimum_enclosure
        assert py_config.via_weights == yaml_config.via_weights

    def test_flat_property_compat(self, py_config):
        """Flat property access works identically to sub-model access."""
        assert py_config.unit_cell_width == py_config.cell.unit_cell_width
        assert py_config.routing_grid_pitch_x == py_config.routing.routing_grid_pitch_x
        assert py_config.minimum_width == py_config.drc.minimum_width


# ---------------------------------------------------------------------------
# Save & reload roundtrip
# ---------------------------------------------------------------------------

class TestSaveReload:
    """TechConfig serialization roundtrip."""

    def test_save_and_reload(self, tmp_output_dir):
        from lccommon.tech_loader import load_tech_yaml, save_tech_yaml
        config = load_tech_yaml(str(EXAMPLES_DIR / "dummy_tech.yaml"))
        save_path = str(tmp_output_dir / "saved_tech.yaml")
        save_tech_yaml(config, save_path)
        reloaded = load_tech_yaml(save_path)
        assert reloaded.db_unit == config.db_unit
        assert reloaded.cell.unit_cell_width == config.cell.unit_cell_width
        assert reloaded.cell.gate_length == config.cell.gate_length
        assert reloaded.routing.routing_grid_pitch_x == config.routing.routing_grid_pitch_x
