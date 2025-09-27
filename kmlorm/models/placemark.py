"""
Placemark model for KML point locations.

This module implements the Placemark class for representing point locations
with coordinates and extended attributes from KML files.
"""

# pylint: disable=too-many-arguments, too-many-positional-arguments
import math
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from kmlorm.core.managers import PlacemarkManager
from .base import KMLElement
from .point import Coordinate, Point


if TYPE_CHECKING:
    from .multigeometry import MultiGeometry


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

    def distance_to(self, other: Union["Placemark", Tuple[float, float]]) -> Optional[float]:
        """
        Calculate distance to another placemark or coordinates.

        Args:
            other: Another Placemark or (longitude, latitude) tuple

        Returns:
            Distance in kilometers, or None if coordinates unavailable
        """
        if not self.has_coordinates:
            return None

        if isinstance(other, Placemark):
            if not other.has_coordinates:
                return None
            # Type assertion: we've checked has_coordinates for other
            assert other.longitude is not None and other.latitude is not None
            other_coords = (other.longitude, other.latitude)
        else:
            other_coords = other
            # Validate coordinate tuple length for user-provided coordinates
            if len(other_coords) < 2:
                return None  # type: ignore[unreachable] # Defensive programming for user input

        # Type assertion: we've already checked has_coordinates
        assert self.longitude is not None and self.latitude is not None
        return self._haversine_distance(
            self.longitude,
            self.latitude,
            float(other_coords[0]),
            float(other_coords[1]),
        )

    def bearing_to(self, other: Union["Placemark", Tuple[float, float]]) -> Optional[float]:
        """
        Calculate bearing to another placemark or coordinates.

        Args:
            other: Another Placemark or (longitude, latitude) tuple

        Returns:
            Bearing in degrees (0-360), or None if coordinates unavailable
        """
        if not self.has_coordinates:
            return None

        if isinstance(other, Placemark):
            if not other.has_coordinates:
                return None
            # Type assertion: we've checked has_coordinates for other
            assert other.longitude is not None and other.latitude is not None
            other_coords = (other.longitude, other.latitude)
        else:
            other_coords = other
            # Validate coordinate tuple length for user-provided coordinates
            if len(other_coords) < 2:
                return None  # type: ignore[unreachable] # Defensive programming for user input

        # Type assertion: we've already checked has_coordinates
        assert self.longitude is not None and self.latitude is not None
        return self._calculate_bearing(
            self.longitude, self.latitude, float(other_coords[0]), float(other_coords[1])
        )

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

    def _haversine_distance(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """
        Calculate the great circle distance between two points.

        Args:
            lon1, lat1: First point coordinates
            lon2, lat2: Second point coordinates

        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in kilometers
        r = 6371

        return c * r

    def _calculate_bearing(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """
        Calculate the bearing from one point to another.

        Args:
            lon1, lat1: Starting point coordinates
            lon2, lat2: Destination point coordinates

        Returns:
            Bearing in degrees (0-360)
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Calculate bearing
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

        bearing = math.atan2(y, x)

        # Convert to degrees and normalize to 0-360
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360

        return bearing
