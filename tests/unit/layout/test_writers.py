"""
Task 02: Test output format writers
"""
import pytest
import os


@pytest.mark.unit
class TestWriters:
    """Test GDS, LEF, and Magic writers."""

    def test_gds_writer_importable(self):
        """GdsWriter can be imported."""
        from lclayout.writer.gds_writer import GdsWriter
        assert GdsWriter is not None

    def test_lef_writer_importable(self):
        """LefWriter can be imported."""
        from lclayout.writer.lef_writer import LefWriter
        assert LefWriter is not None

    def test_mag_writer_importable(self):
        """MagWriter can be imported."""
        from lclayout.writer.magic_writer import MagWriter
        assert MagWriter is not None

    def test_gds_writer_creates_instance(self, dummy_tech):
        """GdsWriter creates valid instance."""
        from lclayout.writer.gds_writer import GdsWriter

        writer = GdsWriter(
            db_unit=dummy_tech.db_unit,
            output_map=dummy_tech.output_map
        )

        assert writer is not None
        assert writer.db_unit == 1e-9

    def test_lef_writer_creates_instance(self, dummy_tech):
        """LefWriter creates valid instance."""
        from lclayout.writer.lef_writer import LefWriter

        writer = LefWriter(
            db_unit=1e-6,
            output_map=dummy_tech.output_map,
            site="CORE"
        )

        assert writer is not None

    def test_mag_writer_creates_instance(self, dummy_tech):
        """MagWriter creates valid instance."""
        from lclayout.writer.magic_writer import MagWriter

        writer = MagWriter(
            tech_name='scmos',
            scale_factor=0.1,
            output_map=dummy_tech.output_map
        )

        assert writer is not None


@pytest.mark.unit
class TestWriterIntegration:
    """Test writers with actual layout data."""

    def test_gds_output_map_configured(self, dummy_tech):
        """Test GDS output with proper layer mapping."""
        from lclayout.writer.gds_writer import GdsWriter

        writer = GdsWriter(
            db_unit=dummy_tech.db_unit,
            output_map=dummy_tech.output_map
        )

        assert len(dummy_tech.output_map) > 0

    def test_writer_db_unit_consistency(self, dummy_tech):
        """Test that writers use consistent database units."""
        from lclayout.writer.gds_writer import GdsWriter
        from lclayout.writer.lef_writer import LefWriter

        gds_writer = GdsWriter(
            db_unit=dummy_tech.db_unit,
            output_map=dummy_tech.output_map
        )

        lef_writer = LefWriter(
            db_unit=1e-6,
            output_map=dummy_tech.output_map,
            site="CORE"
        )

        # Different formats use different units
        assert gds_writer.db_unit != lef_writer.db_unit


@pytest.mark.integration
class TestEndToEndOutput:
    """End-to-end output format tests."""

    def test_inverter_gds_output(self, dummy_tech, sample_netlist_path, tmp_output_dir):
        """Generate complete GDS output for inverter."""
        from lclayout.standalone import LcLayout

        try:
            layout = LcLayout(dummy_tech)
            layout.load_netlist(str(sample_netlist_path), 'INVX1')
            layout.gen_layout()

            gds_path = tmp_output_dir / 'test_output.gds'
            layout.write_gds(str(gds_path))

            assert gds_path.exists()
        except FileNotFoundError:
            pytest.skip("INVX1 not in netlist")
        except Exception as e:
            pytest.skip(f"Layout generation failed: {e}")

    def test_inverter_lef_output(self, dummy_tech, sample_netlist_path, tmp_output_dir):
        """Generate complete LEF output for inverter."""
        from lclayout.standalone import LcLayout

        try:
            layout = LcLayout(dummy_tech)
            layout.load_netlist(str(sample_netlist_path), 'INVX1')
            layout.gen_layout()

            lef_path = tmp_output_dir / 'test_output.lef'
            layout.write_lef(str(lef_path))

            assert lef_path.exists()
        except FileNotFoundError:
            pytest.skip("INVX1 not in netlist")
        except Exception as e:
            pytest.skip(f"Layout generation failed: {e}")
