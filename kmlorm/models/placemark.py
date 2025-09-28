"""
Placemark model for KML point locations.

This module implements the Placemark class for representing point locations
with coordinates and extended attributes from KML files.
"""

# pylint: disable=too-many-arguments, too-many-positional-arguments
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from kmlorm.core.managers import PlacemarkManager
from .base import KMLElement
from .point import Coordinate, Point


if TYPE_CHECKING:
    from .multigeometry import MultiGeometry
    from ..spatial.calculations import DistanceUnit


class Placemark(KMLElement):
    """
    Represents a KML Placemark (point location).

    Placemarks are the most common KML elements, representing specific
    geographic locations with coordinates and optional metadata like
    addresses, phone numbers, and extended data.
    """

    objects: PlacemarkManager = PlacemarkManager()
    point: Optional["Point"]
    multigeometry: Optional["MultiGeometry"]
    address: Optional[str]
    phone_number: Optional[str]
    snippet: Optional[str]
    style_url: Optional[str]
    extended_data: Optional[Dict[str, Any]]

    def __init__(
        self,
        point: Optional["Point"] = None,
        multigeometry: Optional["MultiGeometry"] = None,
        address: Optional[str] = None,
        phone_number: Optional[str] = None,
        snippet: Optional[str] = None,
        style_url: Optional[str] = None,
        extended_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Placemark with location and metadata.

        Args:
            point: Point object containing geometry (for direct Point Placemarks)
            multigeometry: MultiGeometry object (for MultiGeometry Placemarks)
            address: Street address or location description
            phone_number: Contact phone number
            snippet: Short description snippet
            style_url: Reference to KML style definition
            extended_data: Dictionary of additional key-value data
            **kwargs: Additional base element attributes (id, name, etc.)
        """
        # Initialize point first to avoid AttributeError in coordinates setter
        self.point = point
        self.multigeometry = multigeometry
        self.address = address
        self.phone_number = phone_number
        self.snippet = snippet
        self.style_url = style_url
        self.extended_data = extended_data or {}

        # Call super after initializing our attributes
        super().__init__(**kwargs)

    def __str__(self) -> str:
        """
        String representation of the Placemark.

        Returns name if available, otherwise address, otherwise coordinates.
        """
        if self.name:
            return self.name
        if self.address:
            return f"Placemark at {self.address}"
        if self.point and self.point.coordinates:
            lon, lat = self.point.coordinates.latitude, self.point.coordinates.longitude
            return f"Placemark({lon:.4f}, {lat:.4f})"
        return "Placemark(no location)"

    @property
    def coordinates(self) -> "Optional[Coordinate]":
        """Get coordinates from the point."""
        return self.point.coordinates if self.point else None

    @coordinates.setter
    def coordinates(self, value: "Union[Tuple[float, ...], str, None]") -> None:
        """Set coordinates by creating or updating the point."""

        if self.point is None:
            self.point = Point(coordinates=value)
        else:
            self.point.coordinates = value

    @property
    def longitude(self) -> Optional[float]:
        """Get the longitude coordinate."""
        return self.point.longitude if self.point else None

    @property
    def latitude(self) -> Optional[float]:
        """Get the latitude coordinate."""
        return self.point.latitude if self.point else None

    @property
    def altitude(self) -> Optional[float]:
        """Get the altitude coordinate."""
        return self.point.altitude if self.point else None

    @property
    def has_coordinates(self) -> bool:
        """Check if placemark has valid coordinates."""
        return self.point.has_coordinates() if self.point else False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert placemark to dictionary representation.

        Returns:
            Dictionary with all placemark attributes
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "point": self.point.to_dict() if self.point else None,
                "multigeometry": (self.multigeometry.to_dict() if self.multigeometry else None),
                "coordinates": self.coordinates,
                "longitude": self.longitude,
                "latitude": self.latitude,
                "altitude": self.altitude,
                "address": self.address,
                "phone_number": self.phone_number,
                "snippet": self.snippet,
                "style_url": self.style_url,
                "extended_data": self.extended_data,
            }
        )
        return base_dict

    def get_coordinates(self) -> Optional["Coordinate"]:
        """
        Return the coordinate representation of this placemark.

        This method satisfies the HasCoordinates protocol, allowing Placemark
        objects to be used directly in spatial calculations.

        Returns:
            The Coordinate object from the point, or None if no point/coordinates exist
        """
        if self.point and self.point.coordinates:
            return self.point.coordinates
        return None

    def distance_to(
        self,
        other: Union["Coordinate", "Point", "Placemark", Tuple[float, float], list],
        unit: Optional["DistanceUnit"] = None,
    ) -> Optional[float]:
        """
        Calculate distance to another spatial object.

        Args:
            other: Target object with coordinates (Coordinate, Point, Placemark, or tuple/list)
            unit: Distance unit (defaults to kilometers)

        Returns:
            Distance in specified units, or None if this placemark or target has no coordinates

        Examples:
            >>> placemark1 = Placemark(name="NYC", coordinates=(-74.006, 40.7128))
            >>> placemark2 = Placemark(name="London", coordinates=(-0.1276, 51.5074))
            >>> distance = placemark1.distance_to(placemark2)
            >>> print(f"Distance: {distance:.1f} km")

            >>> # Different units
            >>> from kmlorm.spatial import DistanceUnit
            >>> distance_miles = placemark1.distance_to(placemark2, unit=DistanceUnit.MILES)

            >>> # Works with Point and Coordinate objects too
            >>> from kmlorm.models.point import Point, Coordinate
            >>> point = Point(coordinates=(0, 0))
            >>> coord = Coordinate(longitude=1, latitude=1)
            >>> distance_to_point = placemark1.distance_to(point)
            >>> distance_to_coord = placemark1.distance_to(coord)
        """
        if not self.has_coordinates:
            return None

        # Use the point's spatial functionality if available
        if self.point:
            return self.point.distance_to(other, unit)

        return None

    def bearing_to(
        self, other: Union["Coordinate", "Point", "Placemark", Tuple[float, float], list]
    ) -> Optional[float]:
        """
        Calculate bearing to another spatial object.

        Args:
            other: Target object with coordinates

        Returns:
            Initial bearing in degrees (0-360), or None if this placemark or target has
            no coordinates 0° = North, 90° = East, 180° = South, 270° = West

        Examples:
            >>> placemark1 = Placemark(name="Start", coordinates=(0, 0))
            >>> placemark2 = Placemark(name="East", coordinates=(1, 0))
            >>> bearing = placemark1.bearing_to(placemark2)  # Should be ~90°
        """
        if not self.has_coordinates:
            return None

        # Use the point's spatial functionality if available
        if self.point:
            return self.point.bearing_to(other)

        return None

    def midpoint_to(
        self, other: Union["Coordinate", "Point", "Placemark", Tuple[float, float], list]
    ) -> Optional["Coordinate"]:
        """
        Find geographic midpoint to another spatial object.

        Args:
            other: Target object with coordinates

        Returns:
            Coordinate at the midpoint, or None if this placemark or target has no coordinates

        Examples:
            >>> placemark1 = Placemark(name="Start", coordinates=(0, 0))
            >>> placemark2 = Placemark(name="End", coordinates=(2, 2))
            >>> midpoint = placemark1.midpoint_to(placemark2)
        """
        if not self.has_coordinates:
            return None

        # Use the point's spatial functionality if available
        if self.point:
            return self.point.midpoint_to(other)

        return None

    def validate(self) -> bool:
        """
        Validate the placemark's data.

        Returns:
            True if validation passes

        Raises:
            KMLValidationError: If validation fails
        """
        # Call parent validation first
        super().validate()

        # Import here to avoid circular imports
        from ..core.exceptions import KMLValidationError  # pylint: disable=import-outside-toplevel

        # Validate point if present
        if self.point is not None:
            self.point.validate()

        # Validate extended_data is a dictionary
        if not isinstance(self.extended_data, dict):
            raise KMLValidationError(
                "Extended data must be a dictionary",
                field="extended_data",
                value=self.extended_data,
            )

        return True
