"""
Core spatial calculations for KML ORM.

This module provides spatial calculation utilities following WGS84 datum standards.
All calculations assume coordinates in decimal degrees with longitude in range
[-180, 180] and latitude in range [-90, 90].

Key Features:
    - Protocol-based design for type safety
    - Multiple distance calculation strategies
    - Unit conversion support
    - Comprehensive error handling
    - Performance optimizations with caching

Examples:
    >>> from kmlorm.models.point import Coordinate
    >>> coord1 = Coordinate(longitude=-74.006, latitude=40.7128)  # NYC
    >>> coord2 = Coordinate(longitude=-0.1276, latitude=51.5074)  # London
    >>>
    >>> distance = SpatialCalculations.distance_between(coord1, coord2)
    >>> print(f"Distance: {distance:.1f} km")
    >>>
    >>> bearing = SpatialCalculations.bearing_between(coord1, coord2)
    >>> print(f"Bearing: {bearing:.1f} degrees")
"""

import logging
import math
import time
from enum import Enum
from functools import lru_cache, wraps
from typing import Optional, Protocol, Tuple, Union, List, TYPE_CHECKING

from .constants import (
    EARTH_RADIUS_MEAN_KM,
    DEGREES_TO_RADIANS,
    RADIANS_TO_DEGREES,
    FULL_CIRCLE_DEGREES,
    LRU_CACHE_SIZE,
)
from .exceptions import SpatialCalculationError, InvalidCoordinateError

if TYPE_CHECKING:
    from ..models.point import Coordinate

logger = logging.getLogger(__name__)


class DistanceUnit(Enum):
    """
    Units for distance measurements with conversion factors relative to kilometers.

    The values represent the number of units per kilometer.
    For example, METERS = 1000 means 1 km = 1000 meters.
    """
    METERS = 1000.0
    KILOMETERS = 1.0
    MILES = 0.621371
    NAUTICAL_MILES = 0.539957
    FEET = 3280.84
    YARDS = 1093.61


class HasCoordinates(Protocol):
    """
    Protocol for objects that can provide coordinates.

    This protocol enables duck typing for any object that can return
    a Coordinate representation of itself.
    """

    def get_coordinates(self) -> Optional['Coordinate']:
        """
        Return the coordinate representation of this object.

        Returns:
            Coordinate object if available, None if no coordinates exist
        """


def log_spatial_operation(func):
    """
    Decorator to log spatial operations for monitoring and debugging.

    Logs slow operations (>0.1s) and operations that return None.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time

            if elapsed > 0.1:  # Log slow operations
                logger.warning(
                    "Slow spatial operation: %s took %.3fs", func.__name__, elapsed
                )

            if result is None:
                logger.debug("Spatial operation returned None: %s", func.__name__)

            return result

        except Exception as e:
            logger.error("Spatial operation failed: %s: %s", func.__name__, e)
            raise

    return wrapper


class SpatialCalculations:
    """
    Spatial calculation utilities following WGS84 datum.

    All calculations assume:
    - WGS84 ellipsoid (a=6378137.0m, f=1/298.257223563)
    - Coordinates in decimal degrees
    - Longitude: -180 to 180
    - Latitude: -90 to 90

    Mathematical Accuracy:
    - Haversine formula: ±0.5% for most distances
    - Good for distances up to ~20,000 km
    - Assumes spherical Earth (mean radius 6371.0088 km)
    """

    @classmethod
    def _extract_coordinates(
        cls,
        obj: Union[HasCoordinates, Tuple[float, float], List[float]]
    ) -> Optional['Coordinate']:
        """
        Extract coordinates from various spatial input types.

        Args:
            obj: Object that may contain coordinates

        Returns:
            Coordinate object if extraction successful, None otherwise

        Raises:
            InvalidCoordinateError: If coordinate format is invalid
        """
        # Import here to avoid circular imports
        from ..models.point import Coordinate

        if hasattr(obj, 'get_coordinates'):
            # Object implements HasCoordinates protocol
            return obj.get_coordinates()
        elif isinstance(obj, (tuple, list)) and len(obj) >= 2:
            # Tuple/list format: (longitude, latitude[, altitude])
            try:
                longitude = float(obj[0])
                latitude = float(obj[1])
                altitude = float(obj[2]) if len(obj) > 2 else 0.0
                return Coordinate(longitude=longitude, latitude=latitude, altitude=altitude)
            except (ValueError, TypeError, IndexError) as e:
                raise InvalidCoordinateError(
                    f"Invalid coordinate tuple/list: {obj}. Expected (lon, lat[, alt])"
                ) from e
        else:
            return None

    @classmethod
    @lru_cache(maxsize=LRU_CACHE_SIZE)
    def _haversine_distance(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance using Haversine formula.

        Formula:
        a = sin²(Δφ/2) + cos(φ1) * cos(φ2) * sin²(Δλ/2)
        c = 2 * atan2(√a, √(1−a))
        d = R * c

        Where φ is latitude, λ is longitude, R is Earth's radius

        Args:
            lat1, lon1: First point coordinates in decimal degrees
            lat2, lon2: Second point coordinates in decimal degrees

        Returns:
            Distance in kilometers

        Time Complexity: O(1)
        Space Complexity: O(1)

        Accuracy: ±0.5% for most distances on Earth
        """
        # Convert to radians
        lat1_r, lon1_r, lat2_r, lon2_r = map(
            lambda x: x * DEGREES_TO_RADIANS,
            [lat1, lon1, lat2, lon2]
        )

        # Haversine formula
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        return EARTH_RADIUS_MEAN_KM * c

    @classmethod
    @lru_cache(maxsize=LRU_CACHE_SIZE)
    def _calculate_bearing(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the initial bearing from one point to another.

        Formula:
        θ = atan2(sin(Δlong).cos(lat2), cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))

        Args:
            lat1, lon1: Starting point coordinates in decimal degrees
            lat2, lon2: Destination point coordinates in decimal degrees

        Returns:
            Initial bearing in degrees (0-360)

        Notes:
            - 0° = North, 90° = East, 180° = South, 270° = West
            - This is the initial bearing; the actual bearing changes along the great circle path
        """
        # Convert to radians
        lat1_r, lon1_r, lat2_r, lon2_r = map(
            lambda x: x * DEGREES_TO_RADIANS,
            [lat1, lon1, lat2, lon2]
        )

        # Calculate bearing
        dlon = lon2_r - lon1_r
        y = math.sin(dlon) * math.cos(lat2_r)
        x = (math.cos(lat1_r) * math.sin(lat2_r) -
             math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon))

        bearing = math.atan2(y, x)

        # Convert to degrees and normalize to 0-360
        bearing = bearing * RADIANS_TO_DEGREES
        bearing = (bearing + FULL_CIRCLE_DEGREES) % FULL_CIRCLE_DEGREES

        return bearing

    @classmethod
    def _calculate_midpoint(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
        """
        Calculate the geographic midpoint between two coordinates.

        Uses the spherical midpoint formula for great circle paths.

        Args:
            lat1, lon1: First point coordinates in decimal degrees
            lat2, lon2: Second point coordinates in decimal degrees

        Returns:
            Tuple of (longitude, latitude) for midpoint in decimal degrees
        """
        # Convert to radians
        lat1_r, lon1_r, lat2_r, lon2_r = map(
            lambda x: x * DEGREES_TO_RADIANS,
            [lat1, lon1, lat2, lon2]
        )

        # Calculate midpoint using spherical geometry
        dlon = lon2_r - lon1_r

        bx = math.cos(lat2_r) * math.cos(dlon)
        by = math.cos(lat2_r) * math.sin(dlon)

        lat_mid = math.atan2(
            math.sin(lat1_r) + math.sin(lat2_r),
            math.sqrt((math.cos(lat1_r) + bx) ** 2 + by ** 2)
        )

        lon_mid = lon1_r + math.atan2(by, math.cos(lat1_r) + bx)

        # Convert back to degrees
        lat_mid = lat_mid * RADIANS_TO_DEGREES
        lon_mid = lon_mid * RADIANS_TO_DEGREES

        # Normalize longitude to [-180, 180]
        lon_mid = ((lon_mid + 180) % 360) - 180

        return lon_mid, lat_mid

    @classmethod
    @log_spatial_operation
    def distance_between(
        cls,
        from_obj: Union[HasCoordinates, Tuple[float, float], List[float]],
        to_obj: Union[HasCoordinates, Tuple[float, float], List[float]],
        unit: DistanceUnit = DistanceUnit.KILOMETERS
    ) -> Optional[float]:
        """
        Calculate distance between two objects with coordinates.

        Args:
            from_obj: Object with source coordinates
            to_obj: Object with destination coordinates
            unit: Unit for distance measurement

        Returns:
            Distance in specified units, or None if coordinates unavailable

        Raises:
            SpatialCalculationError: If calculation fails
            InvalidCoordinateError: If coordinates are invalid

        Examples:
            >>> from kmlorm.models.point import Coordinate
            >>> coord1 = Coordinate(longitude=0, latitude=0)
            >>> coord2 = Coordinate(longitude=1, latitude=1)
            >>> distance = SpatialCalculations.distance_between(coord1, coord2)
            >>> print(f"Distance: {distance:.2f} km")

            >>> # Using tuples
            >>> distance = SpatialCalculations.distance_between((0, 0), (1, 1))

            >>> # Different units
            >>> distance_miles = SpatialCalculations.distance_between(
            ...     coord1, coord2, unit=DistanceUnit.MILES
            ... )
        """
        try:
            from_coords = cls._extract_coordinates(from_obj)
            to_coords = cls._extract_coordinates(to_obj)

            if not from_coords or not to_coords:
                logger.debug("Cannot calculate distance: missing coordinates")
                return None

            # Calculate distance using Haversine formula
            km = cls._haversine_distance(
                from_coords.latitude, from_coords.longitude,
                to_coords.latitude, to_coords.longitude
            )

            # Convert to requested units
            return km * unit.value

        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            raise SpatialCalculationError(f"Failed to calculate distance: {e}") from e

    @classmethod
    @log_spatial_operation
    def bearing_between(
        cls,
        from_obj: Union[HasCoordinates, Tuple[float, float], List[float]],
        to_obj: Union[HasCoordinates, Tuple[float, float], List[float]]
    ) -> Optional[float]:
        """
        Calculate the initial bearing from one object to another.

        Args:
            from_obj: Object with source coordinates
            to_obj: Object with destination coordinates

        Returns:
            Initial bearing in degrees (0-360), or None if coordinates unavailable
            0° = North, 90° = East, 180° = South, 270° = West

        Raises:
            SpatialCalculationError: If calculation fails

        Examples:
            >>> coord1 = Coordinate(longitude=0, latitude=0)
            >>> coord2 = Coordinate(longitude=1, latitude=0)  # Due east
            >>> bearing = SpatialCalculations.bearing_between(coord1, coord2)
            >>> print(f"Bearing: {bearing:.1f}°")  # Should be ~90°
        """
        try:
            from_coords = cls._extract_coordinates(from_obj)
            to_coords = cls._extract_coordinates(to_obj)

            if not from_coords or not to_coords:
                logger.debug("Cannot calculate bearing: missing coordinates")
                return None

            return cls._calculate_bearing(
                from_coords.latitude, from_coords.longitude,
                to_coords.latitude, to_coords.longitude
            )

        except Exception as e:
            logger.error(f"Bearing calculation failed: {e}")
            raise SpatialCalculationError(f"Failed to calculate bearing: {e}") from e

    @classmethod
    @log_spatial_operation
    def midpoint(
        cls,
        obj1: Union[HasCoordinates, Tuple[float, float], List[float]],
        obj2: Union[HasCoordinates, Tuple[float, float], List[float]]
    ) -> Optional['Coordinate']:
        """
        Find the geographic midpoint between two objects.

        Args:
            obj1: First object with coordinates
            obj2: Second object with coordinates

        Returns:
            Coordinate at the midpoint, or None if coordinates unavailable

        Examples:
            >>> coord1 = Coordinate(longitude=0, latitude=0)
            >>> coord2 = Coordinate(longitude=2, latitude=2)
            >>> midpoint = SpatialCalculations.midpoint(coord1, coord2)
            >>> print(f"Midpoint: {midpoint.longitude}, {midpoint.latitude}")
        """
        try:
            from ..models.point import Coordinate

            coords1 = cls._extract_coordinates(obj1)
            coords2 = cls._extract_coordinates(obj2)

            if not coords1 or not coords2:
                logger.debug("Cannot calculate midpoint: missing coordinates")
                return None

            lon_mid, lat_mid = cls._calculate_midpoint(
                coords1.latitude, coords1.longitude,
                coords2.latitude, coords2.longitude
            )

            return Coordinate(longitude=lon_mid, latitude=lat_mid)

        except Exception as e:
            logger.error(f"Midpoint calculation failed: {e}")
            raise SpatialCalculationError(f"Failed to calculate midpoint: {e}") from e

    @classmethod
    @log_spatial_operation
    def distances_to_many(
        cls,
        from_obj: Union[HasCoordinates, Tuple[float, float], List[float]],
        to_objects: List[Union[HasCoordinates, Tuple[float, float], List[float]]],
        unit: DistanceUnit = DistanceUnit.KILOMETERS
    ) -> List[Optional[float]]:
        """
        Calculate distances from one object to many others efficiently.

        This is more efficient than calling distance_between() repeatedly
        because it extracts the source coordinates once and reuses the calculation.

        Args:
            from_obj: Source object with coordinates
            to_objects: List of destination objects
            unit: Unit for distance measurements

        Returns:
            List of distances in specified units (None for objects without coordinates)

        Time Complexity: O(n) where n = len(to_objects)
        Space Complexity: O(n) for result list

        Examples:
            >>> center = Coordinate(longitude=0, latitude=0)
            >>> points = [
            ...     Coordinate(longitude=1, latitude=0),
            ...     Coordinate(longitude=0, latitude=1),
            ...     Coordinate(longitude=-1, latitude=0),
            ... ]
            >>> distances = SpatialCalculations.distances_to_many(center, points)
        """
        try:
            from_coords = cls._extract_coordinates(from_obj)
            if not from_coords:
                return [None] * len(to_objects)

            results = []
            for to_obj in to_objects:
                to_coords = cls._extract_coordinates(to_obj)
                if not to_coords:
                    results.append(None)
                else:
                    km = cls._haversine_distance(
                        from_coords.latitude, from_coords.longitude,
                        to_coords.latitude, to_coords.longitude
                    )
                    results.append(km * unit.value)

            return results

        except Exception as e:
            logger.error(f"Bulk distance calculation failed: {e}")
            raise SpatialCalculationError(f"Failed to calculate bulk distances: {e}") from e

    @classmethod
    @log_spatial_operation
    def bounding_box(
        cls,
        objects: List[Union[HasCoordinates, Tuple[float, float], List[float]]]
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Calculate minimum bounding rectangle for a set of objects.

        Args:
            objects: List of objects with coordinates

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat) or None if no valid coordinates

        Examples:
            >>> points = [
            ...     Coordinate(longitude=-1, latitude=-1),
            ...     Coordinate(longitude=1, latitude=1),
            ...     Coordinate(longitude=0, latitude=2),
            ... ]
            >>> bbox = SpatialCalculations.bounding_box(points)
            >>> print(f"Bounding box: {bbox}")  # (-1, -1, 1, 2)
        """
        if not objects:
            return None

        valid_coords = []
        for obj in objects:
            coords = cls._extract_coordinates(obj)
            if coords:
                valid_coords.append(coords)

        if not valid_coords:
            return None

        min_lon = min(coord.longitude for coord in valid_coords)
        max_lon = max(coord.longitude for coord in valid_coords)
        min_lat = min(coord.latitude for coord in valid_coords)
        max_lat = max(coord.latitude for coord in valid_coords)

        return min_lon, min_lat, max_lon, max_lat

    @classmethod
    @log_spatial_operation
    def interpolate(
        cls,
        start: Union[HasCoordinates, Tuple[float, float], List[float]],
        end: Union[HasCoordinates, Tuple[float, float], List[float]],
        fraction: float
    ) -> Optional['Coordinate']:
        """
        Find a point along the great circle path between two coordinates.

        Args:
            start: Starting coordinates
            end: Ending coordinates
            fraction: Position along path (0.0 = start, 1.0 = end, 0.5 = midpoint)

        Returns:
            Coordinate at the specified fraction along the path, or None if coordinates unavailable

        Raises:
            ValueError: If fraction is not in range [0, 1]

        Examples:
            >>> start = Coordinate(longitude=0, latitude=0)
            >>> end = Coordinate(longitude=10, latitude=10)
            >>> quarter_point = SpatialCalculations.interpolate(start, end, 0.25)
            >>> midpoint = SpatialCalculations.interpolate(start, end, 0.5)
        """
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"Fraction must be between 0 and 1, got {fraction}")

        try:
            from ..models.point import Coordinate

            start_coords = cls._extract_coordinates(start)
            end_coords = cls._extract_coordinates(end)

            if not start_coords or not end_coords:
                logger.debug("Cannot interpolate: missing coordinates")
                return None

            # Special cases
            if fraction == 0.0:
                return start_coords
            elif fraction == 1.0:
                return end_coords
            elif fraction == 0.5:
                return cls.midpoint(start, end)

            # Convert to radians
            lat1_r = start_coords.latitude * DEGREES_TO_RADIANS
            lon1_r = start_coords.longitude * DEGREES_TO_RADIANS
            lat2_r = end_coords.latitude * DEGREES_TO_RADIANS
            lon2_r = end_coords.longitude * DEGREES_TO_RADIANS

            # Calculate intermediate point using spherical interpolation
            d = 2 * math.asin(math.sqrt(
                math.sin((lat1_r - lat2_r) / 2) ** 2 +
                math.cos(lat1_r) * math.cos(lat2_r) * math.sin((lon1_r - lon2_r) / 2) ** 2
            ))

            if d == 0:  # Same point
                return start_coords

            a = math.sin((1 - fraction) * d) / math.sin(d)
            b = math.sin(fraction * d) / math.sin(d)

            x = a * math.cos(lat1_r) * math.cos(lon1_r) + b * math.cos(lat2_r) * math.cos(lon2_r)
            y = a * math.cos(lat1_r) * math.sin(lon1_r) + b * math.cos(lat2_r) * math.sin(lon2_r)
            z = a * math.sin(lat1_r) + b * math.sin(lat2_r)

            lat_interp = math.atan2(z, math.sqrt(x ** 2 + y ** 2))
            lon_interp = math.atan2(y, x)

            # Convert back to degrees
            lat_interp = lat_interp * RADIANS_TO_DEGREES
            lon_interp = lon_interp * RADIANS_TO_DEGREES

            return Coordinate(longitude=lon_interp, latitude=lat_interp)

        except Exception as e:
            logger.error(f"Interpolation failed: {e}")
            raise SpatialCalculationError(f"Failed to interpolate: {e}") from e
