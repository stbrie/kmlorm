"""
Spatial calculations package for KML ORM.

This package provides spatial calculations and utilities for geometric operations
on KML elements including distance, bearing, and coordinate transformations.

Key Components:
    - calculations: Core spatial calculation functions
    - exceptions: Spatial-specific exceptions
    - strategies: Distance calculation strategies
    - constants: WGS84 and other spatial constants

Examples:
    >>> from kmlorm.spatial.calculations import SpatialCalculations, DistanceUnit
    >>> from kmlorm.models.point import Coordinate
    >>>
    >>> # Calculate distance between two coordinates
    >>> coord1 = Coordinate(longitude=-74.006, latitude=40.7128)  # NYC
    >>> coord2 = Coordinate(longitude=-0.1276, latitude=51.5074)  # London
    >>> distance = SpatialCalculations.distance_between(coord1, coord2)
    >>> print(f"Distance: {distance:.1f} km")
"""

from .calculations import SpatialCalculations, DistanceUnit, HasCoordinates
from .exceptions import (
    SpatialCalculationError,
    InvalidCoordinateError,
    InsufficientDataError,
)

__all__ = [
    "SpatialCalculations",
    "DistanceUnit",
    "HasCoordinates",
    "SpatialCalculationError",
    "InvalidCoordinateError",
    "InsufficientDataError",
]