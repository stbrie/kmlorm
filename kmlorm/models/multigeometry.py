"""
MultiGeometry model for KML multi-geometry collections.

This module defines the MultiGeometry class for handling KML elements
that contain multiple geometry types within a single container.
"""

from typing import Any, Dict, Iterator, List, Optional

from .base import KMLElement


class MultiGeometry(KMLElement):
    """
    Represents a KML MultiGeometry element.

    MultiGeometry elements can contain multiple geometry objects
    including Points, LineStrings, Polygons, and even nested MultiGeometries.
    This allows for complex geometric collections within a single KML feature.

    Attributes:
        geometries: List of geometry objects (Point, Path, Polygon, MultiGeometry)
    """

    def __init__(self, geometries: Optional[List[Any]] = None, **kwargs: Any) -> None:
        """
        Initialize a MultiGeometry with contained geometries.

        Args:
            geometries: List of geometry objects
            **kwargs: Additional base element attributes (id, name, etc.)
        """
        super().__init__(**kwargs)
        self.geometries: List[Any] = geometries or []

    def add_geometry(self, geometry: Any) -> None:
        """
        Add a geometry object to this MultiGeometry.

        Args:
            geometry: A Point, Path, Polygon, or MultiGeometry object
        """
        if geometry is not None:
            self.geometries.append(geometry)

    def get_points(self) -> List[Any]:
        """
        Get all Point objects from this MultiGeometry.

        Returns:
            List of Point objects, including nested ones
        """
        from .point import Point  # pylint: disable=import-outside-toplevel

        points = []
        for geom in self.geometries:
            if isinstance(geom, Point):
                points.append(geom)
            elif hasattr(geom, "get_points"):  # Nested MultiGeometry
                points.extend(geom.get_points())
        return points

    def get_paths(self) -> List[Any]:
        """
        Get all Path objects from this MultiGeometry.

        Returns:
            List of Path objects, including nested ones
        """
        from .path import Path  # pylint: disable=import-outside-toplevel

        paths = []
        for geom in self.geometries:
            if isinstance(geom, Path):
                paths.append(geom)
            elif hasattr(geom, "get_paths"):  # Nested MultiGeometry
                paths.extend(geom.get_paths())
        return paths

    def get_polygons(self) -> List[Any]:
        """
        Get all Polygon objects from this MultiGeometry.

        Returns:
            List of Polygon objects, including nested ones
        """
        from .polygon import Polygon  # pylint: disable=import-outside-toplevel

        polygons = []
        for geom in self.geometries:
            if isinstance(geom, Polygon):
                polygons.append(geom)
            elif hasattr(geom, "get_polygons"):  # Nested MultiGeometry
                polygons.extend(geom.get_polygons())
        return polygons

    def get_multigeometries(self) -> List["MultiGeometry"]:
        """
        Get all nested MultiGeometry objects.

        Returns:
            List of nested MultiGeometry objects
        """
        multigeoms = []
        for geom in self.geometries:
            if isinstance(geom, MultiGeometry):
                multigeoms.append(geom)
                # Recursively get nested MultiGeometries
                multigeoms.extend(geom.get_multigeometries())
        return multigeoms

    def geometry_counts(self) -> Dict[str, int]:
        """
        Get counts of each geometry type in this MultiGeometry.

        Returns:
            Dictionary with geometry type counts
        """
        return {
            "points": len(self.get_points()),
            "paths": len(self.get_paths()),
            "polygons": len(self.get_polygons()),
            "multigeometries": len(self.get_multigeometries()),
            "total": len(self.geometries),
        }

    def has_coordinates(self) -> bool:
        """
        Check if any contained geometry has coordinates.

        Returns:
            True if any geometry has coordinates
        """
        for geom in self.geometries:
            if hasattr(geom, "has_coordinates") and geom.has_coordinates():
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert MultiGeometry to dictionary representation.

        Returns:
            Dictionary with all MultiGeometry attributes
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "geometries": [
                    geom.to_dict() if hasattr(geom, "to_dict") else str(geom)
                    for geom in self.geometries
                ],
                "geometry_counts": self.geometry_counts(),
            }
        )
        return base_dict

    def __str__(self) -> str:
        """String representation of the MultiGeometry."""
        if self.name:
            return f"MultiGeometry: {self.name} ({len(self.geometries)} geometries)"
        return f"MultiGeometry ({len(self.geometries)} geometries)"

    def __repr__(self) -> str:
        """Detailed representation of the MultiGeometry."""
        return (
            f"MultiGeometry(id='{self.id}', name='{self.name}', "
            f"geometries={len(self.geometries)})"
        )

    def __len__(self) -> int:
        """Return the number of contained geometries."""
        return len(self.geometries)

    def __iter__(self) -> Iterator[Any]:
        """Iterate over contained geometries."""
        return iter(self.geometries)

    def __getitem__(self, index: int) -> Any:
        """Get geometry by index."""
        return self.geometries[index]
