#
# Copyright 2019-2020 Thomas Kramer.
#
# This source describes Open Hardware and is licensed under the CERN-OHL-S v2.
#
# You may redistribute and modify this documentation and make products using it
# under the terms of the CERN-OHL-S v2 (https:/cern.ch/cern-ohl).
# This documentation is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
# INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE.
# Please see the CERN-OHL-S v2 for applicable conditions.
#
# Source location: https://codeberg.org/tok/librecell
#
from klayout import db
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class MOS4To3NetlistSpiceReader(db.NetlistSpiceReaderDelegate):
    """
    Read SPICE netlists and convert 4-terminal MOS into 3-terminal MOS by dropping the body net.
    This is required for the LVS step when the standard cells are lacking well taps and therefore
    the body terminal of the transistors is unconnected.
    """

    def element(self, circuit: db.Circuit, el: str, name: str, model: str, value, nets: List[db.Net],
                params: Dict[str, float]):
        """
        Process a SPICE element. All elements except 4-terminal MOS transistors are left unchanged.
        :return: True iff the device has not been ignored and put into the netlist.
        """
        if el != 'M' or len(nets) != 4:
            # All other elements are left to the standard implementation.
            return super().element(circuit, el, name, model, value, nets, params)
        else:
            # Provide a device class.
            cls = circuit.netlist().device_class_by_name(model)
            if not cls:
                # Create MOS3Transistor device class if it does not yet exist.
                cls = db.DeviceClassMOS3Transistor()
                cls.name = model
                circuit.netlist().add(cls)

            # Create MOS3 device.
            device: db.Device = circuit.create_device(cls, name)
            # Configure the MOS3 device.
            for terminal_name, net in zip(['S', 'G', 'D'], nets):
                device.connect_terminal(terminal_name, net)

            # Parameters in the model are given in micrometer units, so
            # we need to translate the parameter values from SI to um values.
            device.set_parameter('W', params.get('W', 0) * 1e6)
            device.set_parameter('L', params.get('L', 0) * 1e6)

            return True


def extract_netlist(layout: db.Layout, top_cell: db.Cell, layer_stack) -> db.Netlist:
    """
    Extract a device level netlist of 3-terminal MOSFETs from the cell `top_cell` of layout `layout`.
    :param layout: Layout object.
    :param top_cell: The top cell of the circuit.
    :param layer_stack: LayerStack providing layermap and via connectivity.
    :return: Netlist as a `klayout.db.Circuit` object.
    """

    # Without netlist comparision capabilities.
    l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(layout, top_cell, []))

    lm = layer_stack.layermap

    def make_layer(layer_name: str):
        return l2n.make_layer(layout.layer(*lm[layer_name]), layer_name)

    rnwell = make_layer('nwell')
    rpwell = make_layer('pwell')
    rndiff = make_layer('ndiffusion')
    rpdiff = make_layer('pdiffusion')
    rpoly = make_layer('poly')
    rndiff_cont = make_layer('ndiff_contact')
    rpdiff_cont = make_layer('pdiff_contact')
    rpoly_cont = make_layer('poly_contact')

    # Build metal and via regions dynamically
    metal_regions = {}
    for metal_name in layer_stack.get_metal_layers():
        metal_regions[metal_name] = make_layer(metal_name)

    metal_label_regions = {}
    for metal_name in layer_stack.get_metal_layers():
        label_name = layer_stack.get_label_layer(metal_name)
        if label_name and label_name in lm:
            metal_label_regions[metal_name] = make_layer(label_name)

    via_regions = {}
    for l1, l2, data in layer_stack.via_layers.edges(data=True):
        via_name = data['layer']
        if via_name not in via_regions and via_name in lm:
            via_regions[via_name] = make_layer(via_name)

    rdiff_cont = rndiff_cont + rpdiff_cont
    rpactive = rpdiff & rnwell
    rpgate = rpactive & rpoly
    rpsd = rpactive - rpgate

    rnactive = rndiff - rnwell
    rngate = rnactive & rpoly
    rnsd = rnactive - rngate

    l2n.register(rpactive, 'pactive')
    l2n.register(rpgate, 'pgate')
    l2n.register(rpsd, 'psd')

    l2n.register(rnactive, 'nactive')
    l2n.register(rngate, 'ngate')
    l2n.register(rnsd, 'nsd')

    # 3 terminal PMOS transistor device extraction
    pmos_ex = db.DeviceExtractorMOS3Transistor("PMOS")
    l2n.extract_devices(pmos_ex, {
        "SD": rpsd, "G": rpgate, "W": rnwell,
        "tS": rpsd, "tD": rpsd, "tG": rpoly,
    })

    # 3 terminal NMOS transistor device extraction
    nmos_ex = db.DeviceExtractorMOS3Transistor("NMOS")
    l2n.extract_devices(nmos_ex, {
        "SD": rnsd, "G": rngate, "W": rpwell,
        "tS": rnsd, "tD": rnsd, "tG": rpoly,
    })

    # Define connectivity for netlist extraction

    # Intra-layer
    for via_name, via_region in via_regions.items():
        l2n.connect(via_region)
    l2n.connect(rpsd)
    l2n.connect(rnsd)
    l2n.connect(rpoly)
    l2n.connect(rdiff_cont)
    l2n.connect(rpoly_cont)
    for metal_region in metal_regions.values():
        l2n.connect(metal_region)

    # Inter-layer: diffusion contacts
    l2n.connect(rpsd, rdiff_cont)
    l2n.connect(rnsd, rdiff_cont)
    l2n.connect(rpoly, rpoly_cont)
    l2n.connect(rpoly_cont, metal_regions[layer_stack.get_metal_layers()[0]])
    l2n.connect(rdiff_cont, metal_regions[layer_stack.get_metal_layers()[0]])

    # Inter-layer: via connectivity (dynamic for any number of metals)
    for l1, l2, data in layer_stack.via_layers.edges(data=True):
        via_name = data['layer']
        # Only connect metal-to-metal vias (not contacts already handled above)
        if via_name in via_regions and l1 in metal_regions and l2 in metal_regions:
            l2n.connect(metal_regions[l1], via_regions[via_name])
            l2n.connect(via_regions[via_name], metal_regions[l2])

    # Label connectivity (dynamic)
    for metal_name, label_region in metal_label_regions.items():
        l2n.connect(metal_regions[metal_name], label_region)

    # Perform netlist extraction
    logger.debug("Extracting netlist from layout")
    l2n.extract_netlist()

    netlist = l2n.netlist()
    netlist.make_top_level_pins()
    netlist.purge()
    netlist.combine_devices()
    netlist.purge_nets()

    assert netlist.top_circuit_count() == 1, "A well formed netlist should have exactly one top circuit."

    return netlist.dup()


def compare_netlist(extracted: db.Netlist, reference: db.Netlist) -> bool:
    """
    Check if two netlists are equal.
    Both netlists must contain only the circuit of the cell.
    Note: It is not possible to copy a circuit from one netlist into another. This makes `simplify()` fail. Better just
    delete all non-used circuits from the netlist.
    :param extracted:
    :param reference:
    :return: Returns True iff the two netlists are equivalent.
    """
    assert extracted.top_circuit_count() == 1, "Expected to get exactly one top level circuit."
    assert reference.top_circuit_count() == 1, "Expected to get exactly one top level circuit."

    # Make sure that combined/fingered transistors are compared correctly.
    # Bring transistors into a unique representation.
    reference.simplify()
    extracted.simplify()

    cmp = db.NetlistComparer()
    compare_result = cmp.compare(extracted, reference)
    logger.debug("Netlist comparision result: {}".format(compare_result))

    if not compare_result:
        logger.warning("Netlists don't match (use --verbose to display the netlists).")

        # Print the both netlists.
        logger.debug(f'''LVS netlists

LVS extracted netlist:
{extracted}

LVS reference netlist:
{reference}
''')

    return compare_result


def read_netlist_mos4_to_mos3(netlist_path: str) -> db.Netlist:
    """
    Read a SPICE netlist and convert all MOS4 transistors to MOS3 transistors.
    :param netlist_path:
    :return:
    """
    logger.debug("Loading netlist (convert MOS4 to MOS3): {}".format(netlist_path))
    netlist = db.Netlist()
    netlist.read(netlist_path, db.NetlistSpiceReader(MOS4To3NetlistSpiceReader()))
    return netlist
