"""
Example: Output layer post-processing — poly bias and metal fill.

Functions are called after layout is complete but before GDS/LEF output.
They modify shapes in-place.
"""


def bias_poly_layer(shapes, tech_config, layer_stack, bias_amount=5, **kwargs):
    """Apply OPC bias to poly layer (expand each edge by bias_amount).

    Args:
        shapes: Dict[str, pya.Shapes] — layer name to shapes mapping.
        tech_config: TechConfig instance.
        layer_stack: LayerStack instance.
        bias_amount: Expansion amount in db_unit.
    """
    # Example: expand poly shapes for OPC compensation
    # layer_name = 'poly'
    # if layer_name in shapes:
    #     region = pya.Region(shapes[layer_name])
    #     biased = region.sized(bias_amount)
    #     shapes[layer_name].clear()
    #     shapes[layer_name].insert(biased)
    pass


def add_fill_pattern(shapes, tech_config, layer_stack, fill_layer='metal1_fill', **kwargs):
    """Add metal fill patterns in empty areas.

    Args:
        shapes: Dict[str, pya.Shapes] — layer name to shapes mapping.
        tech_config: TechConfig instance.
        layer_stack: LayerStack instance.
        fill_layer: Name of the fill layer to create patterns on.
    """
    # Example: compute empty regions and insert fill rectangles
    # cell_box = pya.Box(0, 0, tech_config.unit_cell_width, tech_config.unit_cell_height)
    # cell_region = pya.Region(cell_box)
    # metal_region = pya.Region(shapes.get('metal1', pya.Shapes()))
    # empty = cell_region - metal_region
    # ... insert fill patterns into shapes[fill_layer] ...
    pass
