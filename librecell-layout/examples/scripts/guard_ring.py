"""
Example: Guard ring insertion around a standard cell.

Called as an on_after_placement hook.
"""


def insert_guard_ring(cell, shapes, tech_config, ring_width=200, **kwargs):
    """Insert a guard ring around the cell boundary.

    Args:
        cell: Abstract cell placement object.
        shapes: Dict[str, pya.Shapes] — layer name to shapes mapping.
        tech_config: TechConfig instance.
        ring_width: Width of the guard ring in db_unit.

    Returns:
        The (possibly modified) cell object.
    """
    # Example: draw guard ring structures
    # cell_w = tech_config.unit_cell_width * (cell.width + 1)
    # cell_h = tech_config.unit_cell_height
    #
    # # Outer boundary of guard ring
    # outer = pya.Box(pya.Point(-ring_width, -ring_width),
    #                 pya.Point(cell_w + ring_width, cell_h + ring_width))
    # inner = pya.Box(pya.Point(0, 0), pya.Point(cell_w, cell_h))
    #
    # ring_region = pya.Region(outer) - pya.Region(inner)
    # if 'ndiffusion' in shapes:
    #     shapes['ndiffusion'].insert(ring_region)
    # if 'pdiff_contact' in shapes:
    #     shapes['pdiff_contact'].insert(ring_region)

    return cell


def add_power_straps(routing_trees, shapes, tech_config, strap_layer='metal2', **kwargs):
    """Add vertical power straps after routing.

    Args:
        routing_trees: Dict of routing trees from the router.
        shapes: Dict[str, pya.Shapes] — layer name to shapes mapping.
        tech_config: TechConfig instance.
        strap_layer: Metal layer for power straps.

    Returns:
        The routing_trees (unmodified in this example).
    """
    # Example: add vertical VDD/VSS straps
    # strap_width = tech_config.routing.wire_width.get(strap_layer, 100)
    # cell_h = tech_config.unit_cell_height
    # ... insert vertical paths at regular intervals ...

    return routing_trees
