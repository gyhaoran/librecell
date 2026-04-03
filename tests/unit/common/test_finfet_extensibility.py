"""
Task 10: Tests for FinFET extensibility fields in TechConfig.
"""
import pytest


@pytest.mark.unit
class TestFinFETExtensibility:

    def test_process_type_default_is_planar(self, project_root):
        """TechConfig defaults to process_type='planar'."""
        from lccommon.tech_loader import load_tech_yaml

        config = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")
        )
        assert config.process_type == "planar"

    def test_finfet_params_optional(self, project_root):
        """FinFET parameters are None by default."""
        from lccommon.tech_loader import load_tech_yaml

        config = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")
        )
        assert config.fin_pitch is None
        assert config.fin_width is None
        assert config.num_fins_per_device is None

    def test_finfet_config_validates(self):
        """TechConfig can be created with FinFET parameters set."""
        from lccommon.tech_config import TechConfig, CellConfig, RoutingConfig

        config = TechConfig(
            process_type="finfet",
            fin_pitch=28.0,
            fin_width=7.0,
            num_fins_per_device=2,
            cell=CellConfig(
                unit_cell_width=400,
                unit_cell_height=2400,
                gate_length=14,
                gate_extension=50,
                transistor_offset_y=60,
                power_rail_width=180,
                minimum_gate_width_nfet=100,
                minimum_gate_width_pfet=100,
                minimum_pin_width=25,
            ),
            routing=RoutingConfig(
                routing_grid_pitch_x=100,
                routing_grid_pitch_y=100,
                routing_layers={"metal1": "h"},
            ),
        )
        assert config.process_type == "finfet"
        assert config.fin_pitch == 28.0
        assert config.fin_width == 7.0
        assert config.num_fins_per_device == 2

    def test_planar_config_roundtrip_with_finfet_fields(self, project_root, tmp_path):
        """Saving and reloading a config preserves FinFET fields."""
        from lccommon.tech_loader import load_tech_yaml, save_tech_yaml

        config = load_tech_yaml(
            str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")
        )
        assert config.process_type == "planar"

        out = tmp_path / "roundtrip.yaml"
        save_tech_yaml(config, str(out))

        reloaded = load_tech_yaml(str(out))
        assert reloaded.process_type == "planar"
        assert reloaded.fin_pitch is None
