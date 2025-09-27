"""
Path model for KML LineString elements.

This module implements the Path class for representing routes,
tracks, and other linear geographic features.
"""

# pylint: disable=duplicate-code
from typing import Any, Dict, List, Optional, Tuple, Union

from ..core.exceptions import KMLInvalidCoordinates
from .base import KMLElement


class Path(KMLElement):
    """
    Represents a KML Path (LineString).

    Paths represent linear features like routes, tracks, or boundaries
    defined by a sequence of coordinate points.
    """

    def __init__(
        self,
        coordinates: Optional[List[Union[Tuple[float, ...], str]]] = None,
        tessellate: bool = False,
        altitude_mode: str = "clampToGround",
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Path with coordinate points.

        Args:
            coordinates: List of coordinate points as tuples or strings
            tessellate: Whether to tessellate the path to follow terrain
            altitude_mode: How altitude is interpreted ("clampToGround",
                          "relativeToGround", "absolute")
            **kwargs: Base element attributes (id, name, description, etc.)
        """
        super().__init__(**kwargs)

        self.coordinates = self._parse_coordinates_list(coordinates) if coordinates else []
        self.tessellate = tessellate
        self.altitude_mode = altitude_mode

    def __str__(self) -> str:
        """String representation of the path."""
        if self.name:
            return f"Path: {self.name} ({len(self.coordinates)} points)"

        return f"Path ({len(self.coordinates)} points)"

    @property
    def point_count(self) -> int:
        """
        Get the number of coordinate points in the path.

        Returns:
            Number of coordinate points
        """
        return len(self.coordinates)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert path to dictionary representation.

        Returns:
            Dictionary with path attributes
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "coordinates": self.coordinates,
                "point_count": self.point_count,
                "tessellate": self.tessellate,
                "altitude_mode": self.altitude_mode,
            }
        )
        return base_dict

    def _parse_coordinates_list(
        self, coordinates: List[Union[Tuple[float, ...], str]]
    ) -> List[Tuple[float, ...]]:
        """
        Parse a list of coordinates from various formats.

        Args:
            coordinates: List of coordinate data

        Returns:
            List of parsed coordinate tuples
        """
        parsed = []
        for i, coord in enumerate(coordinates):
            try:
                if isinstance(coord, str):
                    parts = [part.strip() for part in coord.split(",")]
                    if len(parts) < 2:
                        raise ValueError("Need at least longitude and latitude")
                    parsed.append(tuple(float(part) for part in parts))
                elif isinstance(coord, (tuple, list)):
                    if len(coord) < 2:
                        raise ValueError("Need at least longitude and latitude")
                    parsed.append(tuple(float(c) for c in coord))
                else:
                    raise ValueError("Invalid coordinate format")
            except (ValueError, TypeError) as e:
                raise KMLInvalidCoordinates(
                    f"Invalid coordinate at index {i}: {e}", coordinates=coord
                ) from e

        return parsed
