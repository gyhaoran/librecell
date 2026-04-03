"""
Task 10: Tests for custom exception classes and error handling.
"""
import pytest


@pytest.mark.unit
class TestExceptionHierarchy:

    def test_base_exception_exists(self):
        from lccommon.exceptions import LibreCellError
        assert issubclass(LibreCellError, Exception)

    def test_tech_config_error(self):
        from lccommon.exceptions import TechConfigError, LibreCellError
        assert issubclass(TechConfigError, LibreCellError)

    def test_placement_error(self):
        from lccommon.exceptions import PlacementError, LibreCellError
        assert issubclass(PlacementError, LibreCellError)

    def test_routing_error(self):
        from lccommon.exceptions import RoutingError, LibreCellError
        assert issubclass(RoutingError, LibreCellError)

    def test_lvs_error(self):
        from lccommon.exceptions import LVSError, LibreCellError
        assert issubclass(LVSError, LibreCellError)

    def test_drc_error(self):
        from lccommon.exceptions import DRCError, LibreCellError
        assert issubclass(DRCError, LibreCellError)

    def test_netlist_error(self):
        from lccommon.exceptions import NetlistError, LibreCellError
        assert issubclass(NetlistError, LibreCellError)


@pytest.mark.unit
class TestErrorMessages:

    def test_invalid_tech_yaml_raises_tech_config_error(self, tmp_path):
        """Empty YAML file raises TechConfigError with clear message."""
        from lccommon.exceptions import TechConfigError
        from lccommon.tech_loader import load_tech_yaml

        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.write_text("")
        with pytest.raises(TechConfigError, match="Empty YAML file"):
            load_tech_yaml(str(empty_yaml))

    def test_missing_cell_height_raises_tech_config_error(self):
        """Missing unit_cell_height (without track params) raises TechConfigError."""
        from lccommon.exceptions import TechConfigError
        from lccommon.tech_config import TechConfig, CellConfig, RoutingConfig

        with pytest.raises(TechConfigError, match="Must provide unit_cell_height"):
            TechConfig(
                cell=CellConfig(
                    unit_cell_width=400,
                    gate_length=180,
                    gate_extension=100,
                    transistor_offset_y=125,
                    power_rail_width=360,
                    minimum_gate_width_nfet=200,
                    minimum_gate_width_pfet=200,
                    minimum_pin_width=50,
                ),
                routing=RoutingConfig(
                    routing_grid_pitch_x=200,
                    routing_grid_pitch_y=200,
                    routing_layers={"metal1": "h"},
                ),
            )

    def test_netlist_error_for_missing_circuit(self, shared_netlist_path):
        """Looking up a nonexistent circuit raises NetlistError."""
        from lccommon.exceptions import NetlistError
        from lccommon.net_util import load_transistor_netlist

        with pytest.raises(NetlistError, match="No such circuit"):
            load_transistor_netlist(str(shared_netlist_path), "NONEXISTENT_CELL_XYZ")

    def test_continue_on_error_skips_failures(self, project_root, tmp_path):
        """generate_cell_library with continue_on_error does not stop on failure."""
        from lclayout.api import generate_cell_library

        netlist = project_root / "tests" / "fixtures" / "netlists" / "cells.sp"
        if not netlist.exists():
            pytest.skip("cells.sp not found")

        result = generate_cell_library(
            cell_list=["NONEXISTENT_CELL", "ALSO_NONEXISTENT"],
            netlist_path=str(netlist),
            tech_config=str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml"),
            output_dir=str(tmp_path),
            continue_on_error=True,
        )
        assert result["failure_count"] == 2
        assert result["success_count"] == 0
