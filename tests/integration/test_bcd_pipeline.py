"""
Task 06: Integration tests for BCD pipeline.
"""
import pytest
from pathlib import Path


@pytest.fixture
def bcd_tech_path(project_root):
    return project_root / "librecell-layout" / "examples" / "bcd_tech.yaml"


@pytest.fixture
def bcd_netlist_path(project_root):
    return project_root / "librecell-layout" / "examples" / "bcd_cells.sp"


@pytest.fixture
def bcd_config(bcd_tech_path):
    from lclayout.tech_util import load_tech_file
    return load_tech_file(str(bcd_tech_path))


@pytest.mark.integration
class TestBCDPipeline:
    def test_bcd_tech_loads(self, bcd_config):
        """BCD tech YAML loads successfully."""
        assert bcd_config is not None
        assert bcd_config.bcd_enabled is True
        assert len(bcd_config.power_domains) == 2

    def test_bcd_layer_stack(self, bcd_config):
        """LayerStack from BCD config includes HV layers."""
        from lccommon.layer_stack import LayerStack
        ls = LayerStack(bcd_config)
        assert 'hv_nwell' in ls.layermap
        assert 'thick_oxide' in ls.layermap

    def test_single_domain_regression(self, dummy_tech, shared_netlist_path):
        """Single power domain config still works (regression)."""
        import klayout.db as db
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter

        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")

        layout = db.Layout()
        lc = LcLayout(
            tech=dummy_tech,
            layout=layout,
            placer=EulerPlacer(),
            router=GraphRouter()
        )
        lc._01_load_netlist(str(shared_netlist_path), 'INVX1')
        assert lc.SUPPLY_VOLTAGE_NET is not None
        assert lc.GND_NET is not None
        assert len(lc.supply_nets) >= 1
        assert len(lc.ground_nets) >= 1

    def test_bcd_netlist_loads_multi_domain(self, bcd_config, bcd_netlist_path):
        """BCD netlist with VDDH/VSS loads correctly with multi-domain config."""
        import klayout.db as db
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter

        if not bcd_netlist_path.exists():
            pytest.skip("BCD netlist file not found")

        layout = db.Layout()
        lc = LcLayout(
            tech=bcd_config,
            layout=layout,
            placer=EulerPlacer(),
            router=GraphRouter()
        )
        lc._01_load_netlist(str(bcd_netlist_path), 'HV_INVX1')
        assert 'VDDH' in lc.supply_nets
        assert 'VSS' in lc.ground_nets
        # Primary power domain backward compat
        assert lc.SUPPLY_VOLTAGE_NET is not None
        assert lc.GND_NET is not None

    def test_bcd_standard_cell_netlist(self, bcd_config, bcd_netlist_path):
        """Standard cell (INVX1_BCD) in BCD config loads with VDD domain."""
        import klayout.db as db
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter

        if not bcd_netlist_path.exists():
            pytest.skip("BCD netlist file not found")

        layout = db.Layout()
        lc = LcLayout(
            tech=bcd_config,
            layout=layout,
            placer=EulerPlacer(),
            router=GraphRouter()
        )
        lc._01_load_netlist(str(bcd_netlist_path), 'INVX1_BCD')
        assert 'VDD' in lc.supply_nets
        assert 'VSS' in lc.ground_nets

    def test_gds_contains_hv_layers(self, bcd_config):
        """GDS output_map contains HV layer definitions."""
        assert 'hv_nwell' in bcd_config.output_map
        assert 'thick_oxide' in bcd_config.output_map
        # Verify GDS layer numbers
        hv_nwell_gds = bcd_config.output_map['hv_nwell']
        assert hv_nwell_gds == [13, 0]
        thick_oxide_gds = bcd_config.output_map['thick_oxide']
        assert thick_oxide_gds == [14, 0]

    def test_generate_cmos_with_bcd_config(self, bcd_config, shared_netlist_path):
        """BCD config can still load standard CMOS cells."""
        import klayout.db as db
        from lclayout.standalone import LcLayout
        from lclayout.place.euler_placer import EulerPlacer
        from lclayout.graphrouter.graphrouter import GraphRouter

        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")

        layout = db.Layout()
        lc = LcLayout(
            tech=bcd_config,
            layout=layout,
            placer=EulerPlacer(),
            router=GraphRouter()
        )
        # Standard cells.sp has VDD/gnd — VDD matches core domain
        lc._01_load_netlist(str(shared_netlist_path), 'INVX1')
        assert len(lc.supply_nets) >= 1
        assert len(lc.ground_nets) >= 1
