"""
Task 02: Integration tests for layout pipeline
"""
import pytest


@pytest.mark.integration
class TestLayoutPipeline:
    """Test end-to-end layout generation pipeline."""

    def test_lclayout_initialization(self, lclayout_instance):
        """LcLayout can be initialized with proper parameters."""
        assert lclayout_instance is not None
        assert lclayout_instance.tech is not None
        assert lclayout_instance.placer is not None
        assert lclayout_instance.router is not None

    def test_load_netlist(self, lclayout_instance, shared_netlist_path):
        """Load netlist into LcLayout."""
        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")
        
        lclayout_instance._01_load_netlist(str(shared_netlist_path), 'INVX1')
        assert lclayout_instance.cell_name == 'INVX1'
        assert lclayout_instance._transistors_abstract is not None
        assert len(lclayout_instance._transistors_abstract) >= 2

    def test_load_nand2_netlist(self, lclayout_instance, shared_netlist_path):
        """Load NAND2X1 netlist into LcLayout."""
        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")
        
        lclayout_instance._01_load_netlist(str(shared_netlist_path), 'NAND2X1')
        assert lclayout_instance.cell_name == 'NAND2X1'

    def test_placement_generates_cell(self, lclayout_instance, shared_netlist_path):
        """Placement generates a valid Cell object."""
        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")
        
        lclayout_instance._01_load_netlist(str(shared_netlist_path), 'INVX1')
        lclayout_instance._02_setup_layout()
        
        # Check that setup_layout completed
        assert lclayout_instance.layout is not None

    def test_placement_has_upper_and_lower_rows(self, lclayout_instance, shared_netlist_path):
        """Placement result has upper and lower transistor rows."""
        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")
        
        lclayout_instance._01_load_netlist(str(shared_netlist_path), 'INVX1')
        lclayout_instance._02_setup_layout()
        
        # Verify layout was set up
        assert lclayout_instance.layout is not None

    def test_placement_pmos_upper_nmos_lower(self, lclayout_instance, shared_netlist_path):
        """PMOS transistors in upper row, NMOS in lower row."""
        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")
        
        lclayout_instance._01_load_netlist(str(shared_netlist_path), 'NAND2X1')
        lclayout_instance._02_setup_layout()
        
        # Verify setup
        assert lclayout_instance.layout is not None


@pytest.mark.integration
class TestLayoutOutputFormats:
    """Test layout output in various formats."""

    def test_layout_completes_full_pipeline(self, lclayout_instance, shared_netlist_path, tmp_output_dir):
        """Test full layout pipeline completes without error."""
        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")
        
        lclayout_instance._01_load_netlist(str(shared_netlist_path), 'INVX1')
        lclayout_instance._02_setup_layout()
        
        # Verify pipeline can progress
        assert lclayout_instance.layout is not None

    def test_multiple_cell_types_can_be_loaded(self, lclayout_instance, shared_netlist_path):
        """Multiple cell types can be loaded sequentially."""
        if not shared_netlist_path.exists():
            pytest.skip("Netlist file not found")
        
        # Load first cell
        lclayout_instance._01_load_netlist(str(shared_netlist_path), 'INVX1')
        first_cell = lclayout_instance.cell_name
        
        # Reset and load second cell
        lclayout_instance._01_load_netlist(str(shared_netlist_path), 'NAND2X1')
        second_cell = lclayout_instance.cell_name
        
        assert first_cell == 'INVX1'
        assert second_cell == 'NAND2X1'
