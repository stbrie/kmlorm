"""
Polygon model for KML area elements.

This module implements the Polygon class for representing
geographic areas and regions with boundaries.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from ..core.exceptions import KMLInvalidCoordinates
from .base import KMLElement


class Polygon(KMLElement):
    """
    Represents a KML Polygon.

    Polygons represent enclosed geographic areas with an outer boundary
    and optional inner boundaries (holes).
    """

    def __init__(
        self,
        outer_boundary: Optional[List[Union[Tuple[float, ...], str]]] = None,
        inner_boundaries: Optional[List[List[Union[Tuple[float, ...], str]]]] = None,
        extrude: bool = False,
        altitude_mode: str = "clampToGround",
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Polygon with boundaries.

        Args:
            outer_boundary: List of coordinates defining the outer boundary
            inner_boundaries: List of inner boundary coordinate lists (holes)
            extrude: Whether to extrude the polygon to ground level
            altitude_mode: How altitude is interpreted
            **kwargs: Base element attributes (id, name, description, etc.)
        """
        super().__init__(**kwargs)

        self.outer_boundary = self._parse_coordinates_list(outer_boundary) if outer_boundary else []
        self.inner_boundaries = []
        if inner_boundaries:
            for boundary in inner_boundaries:
                self.inner_boundaries.append(self._parse_coordinates_list(boundary))

        self.extrude = extrude
        self.altitude_mode = altitude_mode

    def __str__(self) -> str:
        """String representation of the polygon."""
        boundary_count = len(self.outer_boundary)
        hole_count = len(self.inner_boundaries)

        if self.name:
            if hole_count > 0:
                return f"Polygon: {self.name} " f"({boundary_count} points, {hole_count} holes)"
            return f"Polygon: {self.name} ({boundary_count} points)"

        if hole_count > 0:
            return f"Polygon ({boundary_count} points, {hole_count} holes)"

        return f"Polygon ({boundary_count} points)"

    @property
    def boundary_point_count(self) -> int:
        """
        Get the number of points in the outer boundary.

        Returns:
            Number of boundary points
        """
        return len(self.outer_boundary)

    @property
    def hole_count(self) -> int:
        """
        Get the number of holes (inner boundaries).

        Returns:
            Number of holes
        """
        return len(self.inner_boundaries)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert polygon to dictionary representation.

        Returns:
            Dictionary with polygon attributes
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "outer_boundary": self.outer_boundary,
                "inner_boundaries": self.inner_boundaries,
                "boundary_point_count": self.boundary_point_count,
                "hole_count": self.hole_count,
                "extrude": self.extrude,
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
