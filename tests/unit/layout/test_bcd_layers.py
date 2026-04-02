"""
Task 06: Tests for BCD layers in LayerStack and HV transistor markers.
"""
import pytest

from lccommon.layer_stack import LayerStack
from lclayout.place.place import Transistor, ChannelType


@pytest.fixture
def bcd_tech_path(project_root):
    return project_root / "librecell-layout" / "examples" / "bcd_tech.yaml"


@pytest.fixture
def bcd_config(bcd_tech_path):
    from lclayout.tech_util import load_tech_file
    return load_tech_file(str(bcd_tech_path))


@pytest.fixture
def bcd_layer_stack(bcd_config):
    return LayerStack(bcd_config)


class TestBCDLayers:
    def test_hv_nwell_layer_constant(self):
        """LayerStack has l_hv_nwell class constant."""
        assert LayerStack.l_hv_nwell == 'hv_nwell'

    def test_hv_pwell_layer_constant(self):
        """LayerStack has l_hv_pwell class constant."""
        assert LayerStack.l_hv_pwell == 'hv_pwell'

    def test_thick_oxide_layer_constant(self):
        """LayerStack has l_thick_oxide class constant."""
        assert LayerStack.l_thick_oxide == 'thick_oxide'

    def test_deep_nwell_layer_constant(self):
        """LayerStack has l_deep_nwell class constant."""
        assert LayerStack.l_deep_nwell == 'deep_nwell'

    def test_hv_nwell_in_layermap(self, bcd_layer_stack):
        """hv_nwell layer exists in BCD layermap."""
        assert 'hv_nwell' in bcd_layer_stack.layermap
        assert bcd_layer_stack.layermap['hv_nwell'] == (13, 0)

    def test_thick_oxide_in_layermap(self, bcd_layer_stack):
        """thick_oxide layer exists in BCD layermap."""
        assert 'thick_oxide' in bcd_layer_stack.layermap
        assert bcd_layer_stack.layermap['thick_oxide'] == (14, 0)

    def test_standard_layers_still_present(self, bcd_layer_stack):
        """Standard CMOS layers are still present in BCD config."""
        assert 'ndiffusion' in bcd_layer_stack.layermap
        assert 'metal1' in bcd_layer_stack.layermap
        assert 'nwell' in bcd_layer_stack.layermap


class TestHVTransistorMarkers:
    def test_hv_transistor_has_markers(self, bcd_config):
        """HV transistor layout has _hv_markers populated."""
        from lclayout.layout.transistor import DefaultTransistorLayout

        t = Transistor(
            ChannelType.NMOS, 'vss', 'in', 'out',
            channel_width=200, name='M1',
            is_high_voltage=True
        )
        layout = DefaultTransistorLayout(t, location=(0, 0), tech=bcd_config)
        assert len(layout._hv_markers) == 2
        layer_names = [name for name, _ in layout._hv_markers]
        assert 'thick_oxide' in layer_names
        assert 'hv_pwell' in layer_names  # NMOS -> pwell

    def test_hv_pmos_gets_hv_nwell(self, bcd_config):
        """HV PMOS transistor gets hv_nwell marker."""
        from lclayout.layout.transistor import DefaultTransistorLayout

        t = Transistor(
            ChannelType.PMOS, 'vddh', 'in', 'out',
            channel_width=200, name='M2',
            is_high_voltage=True
        )
        layout = DefaultTransistorLayout(t, location=(0, 1), tech=bcd_config)
        layer_names = [name for name, _ in layout._hv_markers]
        assert 'hv_nwell' in layer_names

    def test_normal_transistor_no_markers(self, bcd_config):
        """Normal (non-HV) transistor has no HV markers."""
        from lclayout.layout.transistor import DefaultTransistorLayout

        t = Transistor(
            ChannelType.NMOS, 'vss', 'in', 'out',
            channel_width=200, name='M3',
            is_high_voltage=False
        )
        layout = DefaultTransistorLayout(t, location=(0, 0), tech=bcd_config)
        assert len(layout._hv_markers) == 0

    def test_hv_transistor_no_markers_when_bcd_disabled(self, dummy_tech):
        """HV transistor has no markers when BCD is disabled."""
        from lclayout.layout.transistor import DefaultTransistorLayout

        t = Transistor(
            ChannelType.NMOS, 'gnd', 'in', 'out',
            channel_width=200, name='M4',
            is_high_voltage=True
        )
        layout = DefaultTransistorLayout(t, location=(0, 0), tech=dummy_tech)
        assert len(layout._hv_markers) == 0

    def test_hv_marker_draw(self, bcd_config):
        """HV markers are drawn into shapes dict."""
        import klayout.db as db
        from lclayout.layout.transistor import DefaultTransistorLayout

        t = Transistor(
            ChannelType.NMOS, 'vss', 'in', 'out',
            channel_width=200, name='M5',
            is_high_voltage=True
        )
        layout_obj = DefaultTransistorLayout(t, location=(0, 0), tech=bcd_config)

        # Build shapes dict with all needed layers
        kl = db.Layout()
        cell = kl.create_cell("test")
        shapes = {}
        for layer_name in ['ndiffusion', 'pdiffusion', 'nwell', 'pwell', 'poly',
                           'thick_oxide', 'hv_nwell', 'hv_pwell']:
            li = kl.layer(0, 0)  # dummy layer index
            shapes[layer_name] = cell.shapes(li)
            li = kl.layer(0, 0)

        layout_obj.draw(shapes)

        # Verify thick_oxide and hv_pwell shapes were inserted
        assert shapes['thick_oxide'].size() > 0
        assert shapes['hv_pwell'].size() > 0
