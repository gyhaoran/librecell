"""
Task 02: Test output format writers
"""
import pytest
import os
from pathlib import Path


@pytest.mark.unit
class TestWriterImports:
    """Test that writer modules can be imported."""

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


@pytest.mark.unit
class TestWriterInstantiation:
    """Test writer class instantiation with proper parameters."""

    def test_gds_writer_creates_instance(self, dummy_tech):
        """GdsWriter creates valid instance."""
        from lclayout.writer.gds_writer import GdsWriter

        writer = GdsWriter(
            db_unit=dummy_tech.db_unit,
            output_map=dummy_tech.output_map
        )

        assert writer is not None
        assert writer.db_unit == dummy_tech.db_unit
        assert writer.output_map is dummy_tech.output_map

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
class TestWriterMethods:
    """Test writer class methods exist and have correct signatures."""

    def test_gds_writer_has_write_layout(self, dummy_tech):
        """GdsWriter has write_layout method."""
        from lclayout.writer.gds_writer import GdsWriter

        writer = GdsWriter(
            db_unit=dummy_tech.db_unit,
            output_map=dummy_tech.output_map
        )

        assert hasattr(writer, 'write_layout')
        assert callable(writer.write_layout)

    def test_remap_layers_function_exists(self):
        """Writer module exports remap_layers function."""
        from lclayout.writer.writer import remap_layers
        assert callable(remap_layers)


@pytest.mark.unit
class TestRemapLayers:
    """Test layer remapping functionality."""

    def test_remap_layers_basic(self, dummy_tech):
        """Test basic layer remapping."""
        from klayout.db import Layout
        from lclayout.writer.writer import remap_layers

        # Create a simple layout with one layer
        layout = Layout()
        cell = layout.create_cell("TEST")
        layer_idx = layout.layer(1, 0)  # Create a layer
        cell.shapes(layer_idx).insert(layout.cell("TEST").bbox())

        # Remap layers
        remapped = remap_layers(layout, dummy_tech.output_map)

        assert remapped is not None
        assert isinstance(remapped, Layout)


@pytest.mark.integration
class TestWriterOutput:
    """End-to-end output format tests with real KLayout layouts."""

    def test_gds_writer_writes_file(self, dummy_tech, tmp_output_dir):
        """GdsWriter produces a GDS file."""
        from klayout.db import Layout
        from lclayout.writer.gds_writer import GdsWriter

        # Create a simple layout
        layout = Layout()
        layout.dbu = 0.001  # 1nm database unit
        cell = layout.create_cell("TEST_CELL")
        layer_idx = layout.layer(1, 0)

        # Add a simple rectangle
        from klayout.db import Box
        box = Box(0, 0, 100, 100)
        cell.shapes(layer_idx).insert(box)

        # Use writer to write
        writer = GdsWriter(
            db_unit=dummy_tech.db_unit,
            output_map=dummy_tech.output_map
        )

        output_dir = str(tmp_output_dir)
        writer.write_layout(
            layout=layout,
            pin_geometries={},
            top_cell=cell,
            output_dir=output_dir
        )

        # Verify output file was created
        expected_gds = Path(output_dir) / "TEST_CELL.gds"
        assert expected_gds.exists(), f"GDS file not created at {expected_gds}"

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

        # Writers preserve their configured db_unit
        assert gds_writer.db_unit == dummy_tech.db_unit
        assert lef_writer.db_unit == 1e-6

    def test_multiple_writers_use_same_output_map(self, dummy_tech):
        """Test that multiple writers can share the same output_map."""
        from lclayout.writer.gds_writer import GdsWriter
        from lclayout.writer.lef_writer import LefWriter
        from lclayout.writer.magic_writer import MagWriter

        shared_output_map = dummy_tech.output_map

        gds = GdsWriter(db_unit=dummy_tech.db_unit, output_map=shared_output_map)
        lef = LefWriter(db_unit=1e-6, output_map=shared_output_map, site="CORE")
        mag = MagWriter(tech_name='scmos', scale_factor=0.1, output_map=shared_output_map)

        # All writers should reference the same output_map
        assert gds.output_map is shared_output_map
        assert lef.output_map is shared_output_map
        assert mag.output_map is shared_output_map
