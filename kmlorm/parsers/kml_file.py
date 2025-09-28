"""
KMLFile class for loading and parsing KML files.

This module provides the main entry point for loading KML data from files,
strings, or URLs and exposing it through the Django-style ORM interface.
"""

# pylint: disable=too-many-instance-attributes, duplicate-code
from typing import Any, Dict, List, Optional

from ..core.managers import (
    FolderManager,
    MultiGeometryManager,
    PathManager,
    PlacemarkManager,
    PointManager,
    PolygonManager,
)
from ..models.folder import Folder
from ..models.multigeometry import MultiGeometry
from ..models.path import Path
from ..models.placemark import Placemark
from ..models.point import Point
from ..models.polygon import Polygon
from .xml_parser import XMLKMLParser


class KMLFile:
    """
    Main class for loading and accessing KML file data.

    Provides Django-style managers for accessing different types of
    KML elements with familiar query interfaces.
    """

    # Type annotations for manager attributes
    folders: FolderManager
    placemarks: PlacemarkManager
    paths: PathManager
    polygons: PolygonManager
    points: PointManager
    multigeometries: MultiGeometryManager

    def __init__(self) -> None:
        """Initialize an empty KML file."""
        # Initialize folders manager first
        self.folders = FolderManager()

        # Set up self-reference for folders to support nested folder flattening
        self.folders._folders_manager = self.folders

        # Managers for different element types with folders reference for flatten functionality
        self.placemarks = PlacemarkManager(folders_manager=self.folders)
        self.paths = PathManager(folders_manager=self.folders)
        self.polygons = PolygonManager(folders_manager=self.folders)
        self.points = PointManager(folders_manager=self.folders)
        self.multigeometries = MultiGeometryManager(folders_manager=self.folders)

        # Give geometry managers access to placemarks for complete collection
        self.points._placemarks_manager = self.placemarks
        self.paths._placemarks_manager = self.placemarks
        self.polygons._placemarks_manager = self.placemarks

        # Document metadata
        self._document_name: Optional[str] = None
        self._document_description: Optional[str] = None

        # XML parser
        self._parser = XMLKMLParser()

    @classmethod
    def from_file(cls, file_path: str) -> "KMLFile":
        """
        Load KML data from a file.

        Args:
            file_path: Path to KML or KMZ file

        Returns:
            KMLFile instance with loaded data

        Raises:
            KMLParseError: If file cannot be read or parsed
            FileNotFoundError: If file doesn't exist
        """
        instance = cls()
        doc_name, doc_description, elements = instance._parser.parse_from_file(file_path)

        instance._document_name = doc_name
        instance._document_description = doc_description
        instance._populate_managers(elements)

        return instance

    @classmethod
    def from_string(cls, kml_string: str) -> "KMLFile":
        """
        Load KML data from a string.

        Args:
            kml_string: KML content as string

        Returns:
            KMLFile instance with loaded data

        Raises:
            KMLParseError: If KML cannot be parsed
        """
        instance = cls()
        doc_name, doc_description, elements = instance._parser.parse_from_string(kml_string)

        instance._document_name = doc_name
        instance._document_description = doc_description
        instance._populate_managers(elements)

        return instance

    @classmethod
    def from_url(cls, url: str) -> "KMLFile":
        """
        Load KML data from a URL.

        Args:
            url: URL to KML or KMZ file

        Returns:
            KMLFile instance with loaded data

        Raises:
            KMLParseError: If URL cannot be accessed or parsed
        """
        instance = cls()
        doc_name, doc_description, elements = instance._parser.parse_from_url(url)

        instance._document_name = doc_name
        instance._document_description = doc_description
        instance._populate_managers(elements)

        return instance

    @property
    def document_name(self) -> Optional[str]:
        """Get the document name from KML."""
        return self._document_name

    @property
    def document_description(self) -> Optional[str]:
        """Get the document description from KML."""
        return self._document_description

    def all_elements(self) -> List[Any]:
        """
        Get all elements from the KML file.

        Returns:
            Combined list of all elements
        """
        elements: List[Any] = []
        elements.extend(self.placemarks.children())
        elements.extend(self.folders.children())
        elements.extend(self.paths.children())
        elements.extend(self.polygons.children())
        elements.extend(self.points.children())
        elements.extend(self.multigeometries.children())
        return elements

    def element_counts(self) -> Dict[str, int]:
        """
        Get counts of each element type.

        Returns:
            Dictionary with element type counts
        """
        return {
            "placemarks": self.placemarks.count(),
            "folders": self.folders.count(),
            "paths": self.paths.count(),
            "polygons": self.polygons.count(),
            "points": self.points.count(),
            "multigeometries": self.multigeometries.count(),
        }

    @staticmethod
    def _is_zip_content(content: bytes) -> bool:
        """
        Return True if the provided bytes look like ZIP (KMZ) content.

        This performs a lightweight signature check for the PK.. ZIP file
        header. It is intentionally simple and only checks the leading
        bytes which is sufficient for KMZ detection in tests.
        """
        if not content:
            return False

        # ZIP files start with 'PK' signature. The most common local file
        # header begins with PK\x03\x04. Check the first 4 bytes when
        # available, otherwise check the first 2 bytes.
        try:
            return content[:4] == b"PK\x03\x04" or content[:2] == b"PK"
        except (IndexError, TypeError):
            return False

    def _populate_managers(self, elements: List[Any]) -> None:
        """
        Populate the managers with parsed elements.

        Args:
            elements: List of parsed KML element objects
        """
        for element in elements:
            if isinstance(element, Placemark):
                self.placemarks.add(element)
            elif isinstance(element, Folder):
                self.folders.add(element)
            elif isinstance(element, Path):
                self.paths.add(element)
            elif isinstance(element, Polygon):
                self.polygons.add(element)
            elif isinstance(element, Point):
                self.points.add(element)
            elif isinstance(element, MultiGeometry):
                self.multigeometries.add(element)
