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
import networkx as nx
from typing import Any, Dict, Tuple
import logging
import importlib.machinery
import types

logger = logging.getLogger(__name__)


def spacing_graph(min_spacing: Dict[Tuple[Any, Any], int]) -> nx.Graph:
    """
    Build a spacing rule graph by mapping the minimal spacing between layer a and layer b to an edge
    a-b in the graph with weight=min_spacing.
    """
    g = nx.Graph()
    for (l1, l2), spacing in min_spacing.items():
        g.add_edge(l1, l2, min_spacing=spacing)
    return g


def load_tech_file_raw(path, module_name='tech'):
    """
    Load a python module containing technology information (raw module).

    Returns the untyped Python module object.  Use :func:`load_tech_file`
    for a unified ``TechConfig`` return type.
    """
    logger.info('Loading tech file (raw): %s', path)
    loader = importlib.machinery.SourceFileLoader('module_name', path)
    tech = types.ModuleType(loader.name)
    loader.exec_module(tech)
    return tech


def load_tech_file(path, module_name='tech'):
    """
    Load a technology file and return a :class:`~lccommon.tech_config.TechConfig`.

    Supports both ``.py`` (legacy Python module) and ``.yaml`` / ``.yml``
    (new YAML format) files.
    """
    logger.info('Loading tech file: %s', path)
    if path.endswith(('.yaml', '.yml')):
        from lccommon.tech_loader import load_tech_yaml
        return load_tech_yaml(path)
    else:
        from lccommon.tech_loader import python_tech_to_config
        module = load_tech_file_raw(path, module_name)
        return python_tech_to_config(module)
