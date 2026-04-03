"""
Task 10: Tests for performance optimizations.
"""
import time
import pytest


@pytest.mark.unit
class TestConfigCaching:

    def test_config_loading_cached(self, project_root):
        """Second load of same file is faster due to caching."""
        from lccommon.tech_loader import load_tech_yaml, _tech_yaml_cache

        yaml_path = str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")

        # Clear cache
        _tech_yaml_cache.clear()

        t1 = time.perf_counter()
        cfg1 = load_tech_yaml(yaml_path)
        t2 = time.perf_counter()
        cfg2 = load_tech_yaml(yaml_path)
        t3 = time.perf_counter()

        first_load = t2 - t1
        second_load = t3 - t2

        # Cached load should be significantly faster
        assert second_load < first_load * 0.8, (
            f"Cached load ({second_load:.4f}s) not faster than "
            f"first load ({first_load:.4f}s)"
        )

    def test_cached_config_is_independent_copy(self, project_root):
        """Cached loads return independent copies (mutation-safe)."""
        from lccommon.tech_loader import load_tech_yaml, _tech_yaml_cache

        yaml_path = str(project_root / "librecell-layout" / "examples" / "cmos_180nm.yaml")
        _tech_yaml_cache.clear()

        cfg1 = load_tech_yaml(yaml_path)
        cfg2 = load_tech_yaml(yaml_path)

        # Mutating one should not affect the other
        original_name = cfg1.name
        cfg1.name = "mutated"
        assert cfg2.name == original_name


@pytest.mark.unit
class TestParallelGeneration:

    def test_generate_cell_library_accepts_num_workers(self):
        """generate_cell_library function signature accepts num_workers."""
        import inspect
        from lclayout.api import generate_cell_library

        sig = inspect.signature(generate_cell_library)
        assert "num_workers" in sig.parameters
        assert sig.parameters["num_workers"].default == 1

    def test_parallel_fallback_to_sequential(self, tmp_path):
        """Parallel generation with TechConfig object falls back to sequential."""
        import logging
        from unittest.mock import patch, MagicMock
        from lclayout.api import generate_cell_library

        mock_tech = MagicMock()
        mock_tech.__class__.__name__ = "TechConfig"

        # Patch isinstance check to make mock pass as TechConfig
        # When num_workers>1 and tech_config is not a str, it should fall back
        with patch("lclayout.api.generate_cell") as mock_gen:
            mock_gen.return_value = {"cell_name": "INVX1"}
            result = generate_cell_library(
                cell_list=["INVX1"],
                netlist_path="/fake/path.sp",
                tech_config=mock_tech,
                output_dir=str(tmp_path),
                num_workers=4,
            )
        # Should have fallen back to sequential (called generate_cell once)
        assert mock_gen.call_count == 1
        assert result["success_count"] == 1
