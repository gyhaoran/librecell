#
# Python API for programmatic standard cell generation.
#
# Provides generate_cell() and generate_cell_library() for batch scripting.
#
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def generate_cell(
    cell_name: str,
    netlist_path: str,
    tech_config: Union[str, "TechConfig"],
    output_dir: str,
    placer: str = "meta",
    router: str = "dijkstra",
    placement_file: Optional[str] = None,
) -> dict:
    """Generate a single standard cell layout.

    Args:
        cell_name: Name of the cell in the SPICE netlist.
        netlist_path: Path to the SPICE netlist file.
        tech_config: Path to tech YAML or a TechConfig instance.
        output_dir: Directory for output files.
        placer: Placement algorithm name.
        router: Signal routing algorithm name.
        placement_file: Optional path to store/load transistor placement.

    Returns:
        Dictionary with generation results::

            {
                "cell_name": str,
                "gds_path": str or None,
                "lef_path": str or None,
                "lvs_passed": bool,
                "drc_violations": list,
            }
    """
    import klayout.db as pya
    from lccommon.tech_config import TechConfig

    from .standalone import LcLayout
    from .place.euler_placer import EulerPlacer, HierarchicalPlacer
    from .place.anneal_placer import RandomPlacer, HillClimbPlacer, ThresholdAcceptancePlacer
    from .place.smt_placer import SMTPlacer
    from .place import meta_placer
    from .graphrouter.graphrouter import GraphRouter
    from .graphrouter.hv_router import HVGraphRouter
    from .graphrouter.pathfinder import PathFinderGraphRouter
    from .graphrouter.signal_router import DijkstraRouter, ApproxSteinerTreeRouter
    from .lvs import lvs
    from .writer.writer import Writer

    # Resolve tech config
    if isinstance(tech_config, str):
        from .tech_util import load_tech_file
        tech = load_tech_file(tech_config)
    elif isinstance(tech_config, TechConfig):
        tech = tech_config
    else:
        raise TypeError(f"tech_config must be str or TechConfig, got {type(tech_config)}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Setup placer
    placers = {
        'meta': meta_placer.MetaTransistorPlacer,
        'flat': EulerPlacer,
        'hierarchical': HierarchicalPlacer,
        'smt': SMTPlacer,
        'random': RandomPlacer,
        'hillclimb': HillClimbPlacer,
        'ta': ThresholdAcceptancePlacer,
    }
    if placer not in placers:
        raise ValueError(f"Unknown placer '{placer}'. Available: {list(placers.keys())}")
    placer_inst = placers[placer]()

    # Setup router
    signal_routers = {
        'dijkstra': DijkstraRouter,
        'steiner': ApproxSteinerTreeRouter,
    }
    if router not in signal_routers:
        raise ValueError(f"Unknown router '{router}'. Available: {list(signal_routers.keys())}")
    signal_router = signal_routers[router]()
    router_inst = HVGraphRouter(
        PathFinderGraphRouter(signal_router),
        orientation_change_penalty=tech.orientation_change_penalty,
    )

    # Create layout
    layout = pya.Layout()
    layouter = LcLayout(tech=tech, layout=layout, placer=placer_inst, router=router_inst)
    cell, pin_geometries = layouter.create_cell_layout(cell_name, netlist_path, placement_file)

    # LVS check
    lvs_passed = False
    try:
        reference_netlist = lvs.read_netlist_mos4_to_mos3(netlist_path)
        circuits_to_delete = {c for c in reference_netlist.each_circuit() if c.name != cell_name}
        for c in circuits_to_delete:
            reference_netlist.remove(c)
        extracted_netlist = lvs.extract_netlist(layout, cell, layouter.layer_stack)
        lvs_passed = lvs.compare_netlist(extracted_netlist, reference_netlist)
    except Exception as e:
        logger.warning("LVS check failed with error: %s", e)

    # Collect DRC violations from script context
    drc_violations = []
    if hasattr(layouter, '_drc_violations') and layouter._drc_violations:
        drc_violations = [v.model_dump() for v in layouter._drc_violations]

    # Write output using configured writers
    gds_path = None
    lef_path = None
    for writer in tech.output_writers:
        assert isinstance(writer, Writer)
        writer.write_layout(
            layout=layout,
            pin_geometries=pin_geometries,
            top_cell=cell,
            output_dir=output_dir,
        )
        # Track output paths
        writer_type = type(writer).__name__
        if 'Gds' in writer_type:
            gds_path = str(Path(output_dir) / f"{cell_name}.gds")
        elif 'Lef' in writer_type:
            lef_path = str(Path(output_dir) / f"{cell_name}.lef")

    return {
        "cell_name": cell_name,
        "gds_path": gds_path,
        "lef_path": lef_path,
        "lvs_passed": lvs_passed,
        "drc_violations": drc_violations,
    }


def generate_cell_library(
    cell_list: List[str],
    netlist_path: str,
    tech_config: Union[str, "TechConfig"],
    output_dir: str,
    continue_on_error: bool = False,
    num_workers: int = 1,
    **kwargs,
) -> dict:
    """Generate multiple standard cells.

    Args:
        cell_list: List of cell names to generate.
        netlist_path: Path to SPICE netlist containing all cells.
        tech_config: Path to tech YAML or TechConfig instance.
        output_dir: Directory for output files.
        continue_on_error: If True, continue on individual cell failures.
        num_workers: Number of parallel workers (1 = sequential).
        **kwargs: Additional arguments passed to generate_cell().

    Returns:
        Dictionary with library generation results::

            {
                "success_count": int,
                "failure_count": int,
                "results": {cell_name: result_dict, ...},
                "failures": {cell_name: error_message, ...},
            }
    """
    results: Dict[str, dict] = {}
    failures: Dict[str, str] = {}

    if num_workers > 1 and len(cell_list) > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed

        # For multiprocessing, tech_config must be a path string
        if not isinstance(tech_config, str):
            logger.warning("Parallel generation requires tech_config as path; falling back to sequential")
            num_workers = 1

    if num_workers <= 1 or len(cell_list) <= 1:
        # Sequential generation
        for cell_name in cell_list:
            try:
                logger.info("Generating cell: %s", cell_name)
                result = generate_cell(
                    cell_name=cell_name,
                    netlist_path=netlist_path,
                    tech_config=tech_config,
                    output_dir=output_dir,
                    **kwargs,
                )
                results[cell_name] = result
            except Exception as e:
                logger.error("Failed to generate cell '%s': %s", cell_name, e)
                failures[cell_name] = str(e)
                if not continue_on_error:
                    break
    else:
        # Parallel generation using ProcessPoolExecutor
        from concurrent.futures import ProcessPoolExecutor, as_completed

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_cell = {
                executor.submit(
                    generate_cell,
                    cell_name=cell_name,
                    netlist_path=netlist_path,
                    tech_config=tech_config,
                    output_dir=output_dir,
                    **kwargs,
                ): cell_name
                for cell_name in cell_list
            }
            for future in as_completed(future_to_cell):
                cell_name = future_to_cell[future]
                try:
                    result = future.result()
                    results[cell_name] = result
                except Exception as e:
                    logger.error("Failed to generate cell '%s': %s", cell_name, e)
                    failures[cell_name] = str(e)

    return {
        "success_count": len(results),
        "failure_count": len(failures),
        "results": results,
        "failures": failures,
    }
