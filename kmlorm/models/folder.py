"""
Folder model for KML containers.

This module implements the Folder class for organizing and containing
other KML elements in a hierarchical structure.
"""

from typing import Any, Dict, List
from kmlorm.core.managers import (
    FolderManager,
    PlacemarkRelatedManager,
    FolderRelatedManager,
    PathRelatedManager,
    PolygonRelatedManager,
    PointRelatedManager,
)
from .base import KMLElement


class Folder(KMLElement):
    """
    Represents a KML Folder (container for organizing elements).

    Folders provide hierarchical organization for KML elements,
    allowing grouping of placemarks, paths, polygons, and nested folders.
    """

    # Type annotations for related managers (set in __init__)
    placemarks: "PlacemarkRelatedManager"
    folders: "FolderRelatedManager"
    paths: "PathRelatedManager"
    polygons: "PolygonRelatedManager"
    points: "PointRelatedManager"
    objects: FolderManager = FolderManager()

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a Folder.

        Args:
            **kwargs: Base element attributes (id, name, description, etc.)
        """
        super().__init__(**kwargs)

        # Related managers for contained elements

        self.placemarks = PlacemarkRelatedManager(self, "placemarks")
        self.folders = FolderRelatedManager(self, "folders")
        self.paths = PathRelatedManager(self, "paths")
        self.polygons = PolygonRelatedManager(self, "polygons")
        self.points = PointRelatedManager(self, "points")

    def __str__(self) -> str:
        """String representation of the folder."""
        if self.name:
            return f"Folder: {self.name}"
        return "Folder (unnamed)"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert folder to dictionary representation.

        Returns:
            Dictionary with folder attributes and element counts
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "placemark_count": self.placemarks.count(),
                "folder_count": self.folders.count(),
                "path_count": self.paths.count(),
                "polygon_count": self.polygons.count(),
                "point_count": self.points.count(),
            }
        )
        return base_dict

    def all_elements(self) -> List["KMLElement"]:
        """
        Get all elements contained in this folder.

        Returns:
            Combined list of all contained elements
        """
        elements: List["KMLElement"] = []
        elements.extend(self.placemarks.children())
        elements.extend(self.folders.children())
        elements.extend(self.paths.children())
        elements.extend(self.polygons.children())
        elements.extend(self.points.children())
        return elements

    def total_element_count(self) -> int:
        """
        Get total count of all contained elements.

        Returns:
            Total number of elements in this folder
        """
        return (
            self.placemarks.count()
            + self.folders.count()
            + self.paths.count()
            + self.polygons.count()
            + self.points.count()
        )
