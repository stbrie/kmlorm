"""
Spatial calculation exceptions.

This module defines exceptions specific to spatial calculations and operations.
These exceptions provide detailed context for spatial calculation failures.
"""


class SpatialCalculationError(Exception):
    """
    Base exception for spatial calculations.

    Raised when spatial calculations encounter errors that cannot be handled
    gracefully, such as mathematical errors or invalid geometric configurations.
    """


class InvalidCoordinateError(SpatialCalculationError):
    """
    Raised when coordinates are invalid or out of bounds.

    This includes:
    - Longitude not in range [-180, 180]
    - Latitude not in range [-90, 90]
    - Non-numeric coordinate values
    - NaN or infinite coordinate values

    Examples:
        >>> from kmlorm.models.point import Coordinate
        >>> try:
        ...     coord = Coordinate(longitude=200, latitude=45)  # Invalid longitude
        ... except InvalidCoordinateError as e:
        ...     print(f"Invalid coordinate: {e}")
    """


class InsufficientDataError(SpatialCalculationError):
    """
    Raised when not enough data is available for spatial calculation.

    This occurs when:
    - Objects don't have coordinate information
    - Required coordinate components are missing
    - Input data is incomplete for the requested calculation

    Examples:
        >>> from kmlorm.spatial.calculations import SpatialCalculations
        >>> from kmlorm.models.placemark import Placemark
        >>> placemark_no_coords = Placemark(name="No coordinates")
        >>> coord = Coordinate(longitude=0, latitude=0)
        >>> try:
        ...     distance = SpatialCalculations.distance_between(placemark_no_coords, coord)
        ... except InsufficientDataError as e:
        ...     print(f"Cannot calculate: {e}")
    """
