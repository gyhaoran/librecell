"""
Unit tests for multi-track support (Task 05).
"""
import warnings

import pytest


# ---------------------------------------------------------------------------
# Helpers — minimal config dicts for TechConfig construction
# ---------------------------------------------------------------------------

def _base_routing():
    """Minimal routing config (explicit pitch_y and offset_y)."""
    return {
        "routing_grid_pitch_x": 200,
        "routing_grid_pitch_y": 300,
        "grid_offset_x": 200,
        "grid_offset_y": 150,
    }


def _base_cell(**overrides):
    """Minimal cell config with defaults, accepting overrides."""
    cell = {
        "unit_cell_width": 400,
        "unit_cell_height": 2400,
        "gate_length": 50,
        "gate_extension": 100,
        "transistor_offset_y": 125,
        "power_rail_width": 360,
        "minimum_gate_width_nfet": 200,
        "minimum_gate_width_pfet": 200,
        "minimum_pin_width": 50,
    }
    cell.update(overrides)
    # Remove keys set to None (so Pydantic uses default)
    return {k: v for k, v in cell.items() if v is not None}


def _base_drc():
    return {
        "min_spacing": {
            "ndiffusion": {"ndiffusion": 50},
            "poly": {"poly": 50},
        },
    }


def _make_config(cell_overrides=None, routing_overrides=None, drc=None):
    """Build a TechConfig from overrides."""
    from lccommon.tech_config import TechConfig
    cell = _base_cell(**(cell_overrides or {}))
    routing = _base_routing()
    if routing_overrides:
        routing.update(routing_overrides)
    # Remove keys set to None
    routing = {k: v for k, v in routing.items() if v is not None}
    data = {
        "cell": cell,
        "routing": routing,
        "drc": drc or _base_drc(),
    }
    return TechConfig.model_validate(data)


# ===========================================================================
# Tests
# ===========================================================================

class TestCellHeightAutoCalc:
    """Test 5.1: Parameterized cell height calculation."""

    def test_height_from_num_tracks_and_pitch(self):
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 8,
                "track_pitch": 300,
            },
        )
        assert config.unit_cell_height == 2400.0

    def test_6t_cell_height(self):
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 6,
                "track_pitch": 300,
            },
        )
        assert config.unit_cell_height == 1800.0

    def test_7t_cell_height(self):
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 7,
                "track_pitch": 300,
            },
        )
        assert config.unit_cell_height == 2100.0

    def test_9t_cell_height(self):
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 9,
                "track_pitch": 300,
            },
        )
        assert config.unit_cell_height == 2700.0

    def test_10t_cell_height(self):
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 10,
                "track_pitch": 300,
            },
        )
        assert config.unit_cell_height == 3000.0

    def test_12t_cell_height(self):
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 12,
                "track_pitch": 300,
            },
        )
        assert config.unit_cell_height == 3600.0

    def test_explicit_height_overrides(self):
        """Explicit unit_cell_height takes priority over auto-calc."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = _make_config(
                cell_overrides={
                    "unit_cell_height": 2400,
                    "num_tracks": 6,
                    "track_pitch": 300,
                },
            )
            assert config.unit_cell_height == 2400
            # Should warn about mismatch (2400 != 6*300=1800)
            assert any("differs from" in str(warning.message) for warning in w)

    def test_explicit_height_no_tracks(self):
        """Config with just unit_cell_height (no num_tracks) works."""
        config = _make_config(
            cell_overrides={"unit_cell_height": 2400},
        )
        assert config.unit_cell_height == 2400
        assert config.num_tracks is None

    def test_missing_height_and_tracks_raises(self):
        """Must provide unit_cell_height or (num_tracks + track_pitch)."""
        with pytest.raises(Exception):
            _make_config(
                cell_overrides={
                    "unit_cell_height": None,
                    "num_tracks": None,
                    "track_pitch": None,
                },
            )

    def test_num_tracks_below_range_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _make_config(
                cell_overrides={
                    "unit_cell_height": None,
                    "num_tracks": 3,
                    "track_pitch": 300,
                },
            )
            assert any("outside recommended range" in str(warning.message) for warning in w)

    def test_num_tracks_above_range_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _make_config(
                cell_overrides={
                    "unit_cell_height": None,
                    "num_tracks": 25,
                    "track_pitch": 300,
                },
            )
            assert any("outside recommended range" in str(warning.message) for warning in w)

    def test_backward_compat_explicit_height_only(self):
        """Existing configs with explicit height + no track params work."""
        config = _make_config()  # defaults: unit_cell_height=2400, no num_tracks
        assert config.unit_cell_height == 2400
        assert config.num_tracks is None
        assert config.track_pitch is None


class TestTransistorOffsetAutoCalc:
    """Test 5.2: Auto-calculation of transistor_offset_y."""

    def test_auto_calc_from_drc_rules(self):
        """Omitting transistor_offset_y auto-computes from DRC spacing."""
        config = _make_config(
            cell_overrides={"transistor_offset_y": None},
            drc={
                "min_spacing": {
                    "ndiffusion": {"ndiffusion": 50},
                    "poly": {"poly": 50},
                },
            },
        )
        # Expected: max(ceil(50/2), 100 + ceil(50/2)) = max(25, 125) = 125
        assert config.transistor_offset_y == 125.0

    def test_explicit_offset_preserved(self):
        """Explicit transistor_offset_y is not overwritten."""
        config = _make_config(
            cell_overrides={"transistor_offset_y": 200},
        )
        assert config.transistor_offset_y == 200


class TestRoutingGridSync:
    """Test 5.3: Routing grid synchronization with track_pitch."""

    def test_track_pitch_sets_routing_pitch_y(self):
        """track_pitch auto-derives routing_grid_pitch_y."""
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 9,
                "track_pitch": 300,
            },
            routing_overrides={
                "routing_grid_pitch_y": None,
                "grid_offset_y": None,
            },
        )
        assert config.routing_grid_pitch_y == 300.0
        assert config.grid_offset_y == 150.0

    def test_explicit_routing_pitch_preserved(self):
        """Explicit routing_grid_pitch_y is not overwritten."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = _make_config(
                cell_overrides={
                    "unit_cell_height": None,
                    "num_tracks": 9,
                    "track_pitch": 300,
                },
                routing_overrides={
                    "routing_grid_pitch_y": 250,
                },
            )
            assert config.routing_grid_pitch_y == 250
            # Should warn about mismatch
            assert any("routing_grid_pitch_y" in str(warning.message) for warning in w)

    def test_grid_offset_y_auto(self):
        """grid_offset_y defaults to track_pitch / 2."""
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 9,
                "track_pitch": 400,
            },
            routing_overrides={
                "routing_grid_pitch_y": None,
                "grid_offset_y": None,
            },
        )
        assert config.grid_offset_y == 200.0

    def test_grid_offset_y_from_routing_pitch(self):
        """Without track_pitch, grid_offset_y defaults from routing_grid_pitch_y / 2."""
        config = _make_config(
            routing_overrides={"grid_offset_y": None},
        )
        assert config.grid_offset_y == 150.0  # 300 / 2


class TestMultiTrackYamlLoading:
    """Test loading multi-track YAML config files."""

    @pytest.mark.parametrize("num_tracks", [6, 7, 9, 10, 12])
    def test_load_track_yaml(self, project_root, num_tracks):
        from lclayout.tech_util import load_tech_file
        path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{num_tracks}t.yaml"
        config = load_tech_file(str(path))
        assert config.cell.num_tracks == num_tracks
        assert config.unit_cell_height == num_tracks * 300

    @pytest.mark.parametrize("num_tracks", [6, 7, 9, 10, 12])
    def test_routing_grid_derived(self, project_root, num_tracks):
        from lclayout.tech_util import load_tech_file
        path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{num_tracks}t.yaml"
        config = load_tech_file(str(path))
        assert config.routing_grid_pitch_y == 300
        assert config.grid_offset_y == 150

    @pytest.mark.parametrize("num_tracks", [6, 7, 9, 10, 12])
    def test_transistor_offset_auto(self, project_root, num_tracks):
        from lclayout.tech_util import load_tech_file
        path = project_root / "librecell-layout" / "examples" / f"dummy_tech_{num_tracks}t.yaml"
        config = load_tech_file(str(path))
        assert config.transistor_offset_y > 0

    def test_12t_taller_than_6t(self, project_root):
        from lclayout.tech_util import load_tech_file
        t6 = load_tech_file(str(project_root / "librecell-layout" / "examples" / "dummy_tech_6t.yaml"))
        t12 = load_tech_file(str(project_root / "librecell-layout" / "examples" / "dummy_tech_12t.yaml"))
        assert t12.unit_cell_height > t6.unit_cell_height


class TestEstimateMinTracks:
    """Test estimate_min_tracks() heuristic."""

    def test_inverter_estimate(self, inverter_transistors):
        from lclayout.routing_graph import estimate_min_tracks
        result = estimate_min_tracks("INV", inverter_transistors, ["in", "out"])
        assert 4 <= result <= 6

    def test_nand2_estimate(self, nand2_transistors):
        from lclayout.routing_graph import estimate_min_tracks
        result = estimate_min_tracks("NAND2", nand2_transistors, ["A", "B", "Y"])
        assert result >= 4

    def test_result_clamped_to_range(self, inverter_transistors):
        from lclayout.routing_graph import estimate_min_tracks
        result = estimate_min_tracks("INV", inverter_transistors, ["in", "out"])
        assert 4 <= result <= 20

    def test_nand2_needs_more_than_inverter(self, inverter_transistors, nand2_transistors):
        from lclayout.routing_graph import estimate_min_tracks
        inv = estimate_min_tracks("INV", inverter_transistors, ["in", "out"])
        nand = estimate_min_tracks("NAND2", nand2_transistors, ["A", "B", "Y"])
        assert nand >= inv


class TestFlatProperties:
    """Test flat property accessors for new fields."""

    def test_num_tracks_property(self):
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 9,
                "track_pitch": 300,
            },
        )
        assert config.num_tracks == 9

    def test_track_pitch_property(self):
        config = _make_config(
            cell_overrides={
                "unit_cell_height": None,
                "num_tracks": 9,
                "track_pitch": 300,
            },
        )
        assert config.track_pitch == 300

    def test_num_tracks_none_when_not_set(self):
        config = _make_config()
        assert config.num_tracks is None
        assert config.track_pitch is None
