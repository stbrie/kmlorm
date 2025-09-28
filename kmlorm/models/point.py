"""
Point model for standalone Point geometries in KML files.

This module defines the Point class for handling standalone Point elements
that exist as direct children of Document/Folder elements, separate from
Placemarks that contain Point geometries.
"""

from dataclasses import dataclass
from typing import Any, Optional, Tuple, Union
from ..core.exceptions import KMLValidationError
from .base import KMLElement


@dataclass(frozen=True)
class Coordinate:
    """
    Represents a geographic coordinate with longitude, latitude, and optional altitude.

    Attributes:
        longitude (float): The longitude of the coordinate.
        latitude (float): The latitude of the coordinate.
        altitude (Optional[float]): The altitude of the coordinate, if available.

    Methods:
        from_tuple(t: Tuple[float, ...]) -> "Coordinate":
            Creates a Coordinate instance from a tuple containing longitude, latitude,
            and optionally altitude.

        from_string(s: str) -> "Coordinate":
            Creates a Coordinate instance from a comma-separated string representation of
            longitude, latitude, and optionally altitude.
    """

    longitude: float
    latitude: float
    altitude: float = 0

    def __post_init__(self) -> None:
        """
        Post-initialization hook that is automatically called after the dataclass is instantiated.
        This method triggers validation logic to ensure the object's state is consistent and valid.
        """
        self.validate()

    @classmethod
    def from_tuple(cls, t: Tuple[float, ...]) -> "Coordinate":
        """
        Create a Coordinate instance from a tuple of floats.

        Args:
            t (Tuple[float, ...]): A tuple containing longitude, latitude, and optionally altitude.

        Returns:
            Coordinate: An instance of Coordinate with the specified longitude, latitude,
                and optional altitude.

        Raises:
            IndexError: If the tuple does not contain at least two elements.
            ValueError: If the tuple elements cannot be converted to float.
        """
        try:
            lon = float(t[0])
            lat = float(t[1])
            alt = float(t[2]) if len(t) > 2 else 0.0
        except (IndexError, TypeError, ValueError) as exc:
            raise KMLValidationError(
                "Invalid coordinate tuple.  Expected (lon, lat, [alt])"
                f"with numeric arguments.  Got ({t}]"
            ) from exc
        rv = cls(longitude=lon, latitude=lat, altitude=alt)
        rv.validate()
        return rv

    @classmethod
    def from_string(cls, s: str) -> "Coordinate":
        """
        Creates a Coordinate instance from a comma-separated string.

        Args:
            s (str): A string containing coordinate values separated by commas (e.g.,
                "longitude, latitude, [altitude]").

        Returns:
            Coordinate: An instance of the Coordinate class created from the parsed values.

        Raises:
            ValueError: If the string cannot be parsed into valid float values.
        """
        parts = [p.strip() for p in s.split(",")]
        try:
            rv = cls.from_tuple(tuple(float(p) for p in parts))
        except KMLValidationError as kve:
            raise KMLValidationError(
                f"Could not parse '{s}' into tuple(float, float, float)"
            ) from kve
        return rv

    @classmethod
    def from_any(cls, value: Union[Tuple[float, ...], str, list, "Coordinate"]) -> "Coordinate":
        """
        Creates a Coordinate instance from various input types.

        Args:
            value (Union[Tuple[float, ...], str, list, Coordinate]): The input value to convert.
                Can be a tuple, list, string, or another Coordinate instance.

        Returns:
            Coordinate: A Coordinate instance created from the input value.

        Raises:
            TypeError: If the input value is not a tuple, list, string, or Coordinate.
        """
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls.from_string(value)
        if isinstance(value, (tuple, list)):
            return cls.from_tuple(tuple(value))
        raise TypeError("Unsupported coordinate type; expected tuple, list, str, or Coordinate")

    def validate(self) -> bool:
        """
        Validates the longitude, latitude, and optional altitude values of the point.

        Returns:
            bool: True if all coordinate values are valid.

        Raises:
            KMLValidationError: If longitude or latitude are not numeric, out of valid range,
                                or if altitude is provided and is not a finite numeric value.
        """
        try:
            lon = float(self.longitude)
            lat = float(self.latitude)
        except (TypeError, ValueError) as exc:
            raise KMLValidationError("Coordinate values must be numeric") from exc

        if not -180.0 <= lon <= 180.0:
            raise KMLValidationError(f"Invalid longitude: {lon}.  Must be between -180.0 and 180.0")
        if not -90 <= lat <= 90:
            raise KMLValidationError(f"Invalid latitude: {lat}. Must be between -90.0 and 90.0")

        if self.altitude is not None:
            try:
                alt = float(self.altitude)
            except (TypeError, ValueError) as exc:
                raise KMLValidationError("Altitude must be numeric") from exc

            # pylint: disable=comparison-with-itself
            # NaN or infinity check
            if not (alt == alt and abs(alt) != float("inf")):
                raise KMLValidationError("Altitude must be a finite number")

        return True

    def to_dict(self) -> dict[str, float]:
        """
        Convert coordinate to dictionary representation.

        Returns:
            Dictionary with longitude, latitude, and altitude values.
        """
        return {"longitude": self.longitude, "latitude": self.latitude, "altitude": self.altitude}

    def get_coordinates(self) -> Optional['Coordinate']:
        """
        Return self as the coordinate representation.

        This method satisfies the HasCoordinates protocol, allowing Coordinate
        objects to be used directly in spatial calculations.

        Returns:
            Self (this Coordinate object)
        """
        return self

    def distance_to(
        self,
        other: Union['Coordinate', 'Point', 'Placemark', Tuple[float, float], list],
        unit: Optional['DistanceUnit'] = None
    ) -> Optional[float]:
        """
        Calculate distance to another spatial object.

        Args:
            other: Target object with coordinates (Coordinate, Point, Placemark, or tuple)
            unit: Distance unit (defaults to kilometers)

        Returns:
            Distance in specified units, or None if target has no coordinates

        Examples:
            >>> coord1 = Coordinate(longitude=-74.006, latitude=40.7128)  # NYC
            >>> coord2 = Coordinate(longitude=-0.1276, latitude=51.5074)  # London
            >>> distance = coord1.distance_to(coord2)
            >>> print(f"Distance: {distance:.1f} km")

            >>> # Different units
            >>> from kmlorm.spatial import DistanceUnit
            >>> distance_miles = coord1.distance_to(coord2, unit=DistanceUnit.MILES)
        """
        from ..spatial.calculations import SpatialCalculations, DistanceUnit
        if unit is None:
            unit = DistanceUnit.KILOMETERS
        return SpatialCalculations.distance_between(self, other, unit)

    def bearing_to(
        self,
        other: Union['Coordinate', 'Point', 'Placemark', Tuple[float, float], list]
    ) -> Optional[float]:
        """
        Calculate bearing to another spatial object.

        Args:
            other: Target object with coordinates

        Returns:
            Initial bearing in degrees (0-360), or None if target has no coordinates
            0° = North, 90° = East, 180° = South, 270° = West

        Examples:
            >>> coord1 = Coordinate(longitude=0, latitude=0)
            >>> coord2 = Coordinate(longitude=1, latitude=0)  # Due east
            >>> bearing = coord1.bearing_to(coord2)
            >>> print(f"Bearing: {bearing:.1f}°")  # Should be ~90°
        """
        from ..spatial.calculations import SpatialCalculations
        return SpatialCalculations.bearing_between(self, other)

    def midpoint_to(
        self,
        other: Union['Coordinate', 'Point', 'Placemark', Tuple[float, float], list]
    ) -> Optional['Coordinate']:
        """
        Find geographic midpoint to another spatial object.

        Args:
            other: Target object with coordinates

        Returns:
            Coordinate at the midpoint, or None if target has no coordinates

        Examples:
            >>> coord1 = Coordinate(longitude=0, latitude=0)
            >>> coord2 = Coordinate(longitude=2, latitude=2)
            >>> midpoint = coord1.midpoint_to(coord2)
            >>> print(f"Midpoint: ({midpoint.longitude}, {midpoint.latitude})")
        """
        from ..spatial.calculations import SpatialCalculations
        return SpatialCalculations.midpoint(self, other)

    def __hash__(self) -> int:
        """
        Hash for caching support in spatial calculations.

        Returns:
            Hash based on longitude, latitude, and altitude
        """
        return hash((self.longitude, self.latitude, self.altitude))


class Point(KMLElement):
    """
    Represents a standalone Point geometry in KML.

    Points can exist as standalone elements or within other containers.
    This class handles Points that are direct children of Document/Folder
    elements, separate from Points that exist within Placemarks.

    Attributes:
        coordinates: Tuple of (longitude, latitude, altitude)
        extrude: Whether the point is extruded to ground
        altitude_mode: How altitude is interpreted
        tessellate: Whether lines are tessellated
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a Point with coordinates and properties."""
        super().__init__(**kwargs)

        # Geometry properties
        self._coordinates: Optional["Coordinate"] = None
        if "coordinates" in kwargs and kwargs["coordinates"] is not None:
            self.coordinates = kwargs["coordinates"]
        self.extrude: bool = kwargs.get("extrude", False)
        self.altitude_mode: str = kwargs.get("altitude_mode", "clampToGround")
        self.tessellate: bool = kwargs.get("tessellate", False)

    @property
    def coordinates(self) -> Optional["Coordinate"]:
        """Get coordinates tuple."""
        return self._coordinates

    @coordinates.setter
    def coordinates(self, value: Union[Tuple[float, ...], str, "Coordinate", None]) -> None:
        """Set coordinates, handling various input formats."""
        if value is None:
            self._coordinates = None
            return

        try:
            coord = Coordinate.from_any(value)
        except (ValueError, TypeError, IndexError) as exc:
            raise ValueError("Invalid coordinate value") from exc
        self._coordinates = coord

    @property
    def longitude(self) -> Optional[float]:
        """Get longitude from coordinates."""
        return self.coordinates.longitude if self.coordinates else None

    @property
    def latitude(self) -> Optional[float]:
        """Get latitude from coordinates."""
        return self.coordinates.latitude if self.coordinates else None

    @property
    def altitude(self) -> Optional[float]:
        """Get altitude from coordinates."""
        return self.coordinates.altitude if self.coordinates else None

    def has_coordinates(self) -> bool:
        """Check if point has valid coordinates."""
        return bool(
            self.coordinates is not None
            and self.coordinates.latitude is not None
            and self.coordinates.longitude is not None
        )

    def __str__(self) -> str:
        """String representation of the Point."""
        if self.name:
            return f"Point: {self.name}"
        if self.coordinates:
            return f"Point: ({self.longitude}, {self.latitude})"
        return "Point: (no coordinates)"

    def __repr__(self) -> str:
        """Detailed representation of the Point."""
        return f"Point(id='{self.id}', name='{self.name}', " f"coordinates={self.coordinates})"

    def validate(self) -> bool:
        """
        Validate the point's coordinates.

        Returns:
            True if validation passes

        Raises:
            Exception: If coordinates are invalid
        """
        # Call parent validation first
        super().validate()

        # Validate coordinates if present delegate to Coordinate
        if self.coordinates is not None:
            self.coordinates.validate()

        return True

    def to_dict(self) -> dict[str, Any]:
        """
        Convert point to dictionary representation.

        Returns:
            Dictionary containing point properties and coordinate data.
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "coordinates": self.coordinates.to_dict() if self.coordinates else None,
                "longitude": self.longitude,
                "latitude": self.latitude,
                "altitude": self.altitude,
                "extrude": self.extrude,
                "altitude_mode": self.altitude_mode,
                "tessellate": self.tessellate,
            }
        )
        return base_dict

    def get_coordinates(self) -> Optional['Coordinate']:
        """
        Return the coordinate representation of this point.

        This method satisfies the HasCoordinates protocol, allowing Point
        objects to be used directly in spatial calculations.

        Returns:
            The Coordinate object, or None if no coordinates are set
        """
        return self.coordinates

    def distance_to(
        self,
        other: Union['Coordinate', 'Point', 'Placemark', Tuple[float, float], list],
        unit: Optional['DistanceUnit'] = None
    ) -> Optional[float]:
        """
        Calculate distance to another spatial object.

        Args:
            other: Target object with coordinates
            unit: Distance unit (defaults to kilometers)

        Returns:
            Distance in specified units, or None if this point or target has no coordinates

        Examples:
            >>> point1 = Point(coordinates=(0, 0))
            >>> point2 = Point(coordinates=(1, 1))
            >>> distance = point1.distance_to(point2)
        """
        if not self.coordinates:
            return None
        return self.coordinates.distance_to(other, unit)

    def bearing_to(
        self,
        other: Union['Coordinate', 'Point', 'Placemark', Tuple[float, float], list]
    ) -> Optional[float]:
        """
        Calculate bearing to another spatial object.

        Args:
            other: Target object with coordinates

        Returns:
            Initial bearing in degrees (0-360), or None if this point or target has no coordinates

        Examples:
            >>> point1 = Point(coordinates=(0, 0))
            >>> point2 = Point(coordinates=(1, 0))  # Due east
            >>> bearing = point1.bearing_to(point2)  # Should be ~90°
        """
        if not self.coordinates:
            return None
        return self.coordinates.bearing_to(other)

    def midpoint_to(
        self,
        other: Union['Coordinate', 'Point', 'Placemark', Tuple[float, float], list]
    ) -> Optional['Coordinate']:
        """
        Find geographic midpoint to another spatial object.

        Args:
            other: Target object with coordinates

        Returns:
            Coordinate at the midpoint, or None if this point or target has no coordinates

        Examples:
            >>> point1 = Point(coordinates=(0, 0))
            >>> point2 = Point(coordinates=(2, 2))
            >>> midpoint = point1.midpoint_to(point2)
        """
        if not self.coordinates:
            return None
        return self.coordinates.midpoint_to(other)
