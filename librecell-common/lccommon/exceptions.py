"""
Custom exception classes for LibreCell.

Provides domain-specific exceptions that replace generic Exception/ValueError
raises, making it possible to distinguish and handle different failure modes.
"""


class LibreCellError(Exception):
    """Base exception for all LibreCell errors."""
    pass


class TechConfigError(LibreCellError):
    """Error in technology configuration (missing fields, invalid values)."""
    pass


class PlacementError(LibreCellError):
    """Transistor placement failed (SMT unsatisfiable, no valid arrangement)."""
    pass


class RoutingError(LibreCellError):
    """Signal routing failed (LP infeasible, pathfinder exceeded iterations)."""
    pass


class LVSError(LibreCellError):
    """Layout-vs-schematic verification failed."""
    pass


class DRCError(LibreCellError):
    """Design rule check violation."""
    pass


class NetlistError(LibreCellError):
    """Netlist parsing or circuit lookup error."""
    pass
