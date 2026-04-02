"""
Example: Custom DRC rules — EOL spacing and density checks.

These are plain Python functions called by ScriptContext.
No base class needed — just follow the function signature convention.
"""


def check_eol_spacing(shapes, tech_config, layer_stack, min_eol_spacing=100, **kwargs):
    """Check End-of-Line spacing on metal1 layer.

    Args:
        shapes: Dict[str, pya.Shapes] — layer name to shapes mapping.
        tech_config: TechConfig instance.
        layer_stack: LayerStack instance.
        min_eol_spacing: Minimum EOL spacing in db_unit.

    Returns:
        List[DrcViolation] — violations found.
    """
    from lccommon.script_context import DrcViolation

    violations = []
    layer_name = 'metal1'
    if layer_name not in shapes:
        return violations

    # Example: iterate shapes and check line-end proximity
    # In a real implementation, you would use pya.Region operations
    # to find EOL spacing violations.
    #
    # region = pya.Region(shapes[layer_name])
    # edges = region.edges()
    # ... check short edges (line ends) against nearby geometry ...

    return violations


def check_density(shapes, tech_config, layer_stack, max_density=0.8, **kwargs):
    """Check metal layer density.

    Args:
        shapes: Dict[str, pya.Shapes] — layer name to shapes mapping.
        tech_config: TechConfig instance.
        layer_stack: LayerStack instance.
        max_density: Maximum allowed density (0.0 to 1.0).

    Returns:
        List[DrcViolation] — violations found.
    """
    from lccommon.script_context import DrcViolation

    violations = []

    # Example: compute area ratio per metal layer
    # cell_area = tech_config.unit_cell_width * tech_config.unit_cell_height
    # for layer_name in tech_config.routing.routing_layers:
    #     if layer_name in shapes:
    #         region = pya.Region(shapes[layer_name])
    #         layer_area = region.area()
    #         density = layer_area / cell_area if cell_area > 0 else 0
    #         if density > max_density:
    #             violations.append(DrcViolation(
    #                 rule_name=f"DENSITY_{layer_name.upper()}",
    #                 layer=layer_name,
    #                 severity="warning",
    #                 message=f"{layer_name} density {density:.2%} exceeds max {max_density:.2%}",
    #             ))

    return violations
