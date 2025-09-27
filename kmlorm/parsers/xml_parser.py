"""
Direct XML-based KML parser using lxml.

This module provides robust KML parsing without external KML library
dependencies, focusing on extracting data for Django-style access rather
than geospatial calculations.
"""

# pylint: disable= too-many-branches, import-outside-toplevel, too-many-lines
import logging
import os
import xml.etree.ElementTree as _et

import zipfile
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
from urllib.request import urlopen
from lxml import etree

from ..core.exceptions import KMLParseError
from ..models.folder import Folder
from ..models.multigeometry import MultiGeometry
from ..models.path import Path
from ..models.placemark import Placemark
from ..models.point import Point
from ..models.polygon import Polygon


# Require lxml for XML parsing. Do not fall back to ElementTree.


LXML_AVAILABLE = True

# Define a backend-appropriate parse exception alias so we can catch parse
# errors without relying on attributes that may not exist on the imported
# etree name (lxml vs stdlib ElementTree).
# Prefer the lxml XMLSyntaxError when available; fall back to stdlib ParseError.
_xml_syntax_exc = getattr(etree, "XMLSyntaxError", None)  # pylint: disable=invalid-name
if _xml_syntax_exc is not None:
    ParseException = _xml_syntax_exc
else:
    ParseException = _et.ParseError

# Set up logger for this module
logger = logging.getLogger(__name__)


class XMLKMLParser:
    """
    Direct XML parser for KML files using lxml or xml.AnyTree.

    Focuses on robust parsing and data extraction rather than geospatial
    calculations.
    """

    # KML namespace constants
    KML_NS = "http://www.opengis.net/kml/2.2"
    GX_NS = "http://www.google.com/kml/ext/2.2"
    ATOM_NS = "http://www.w3.org/2005/Atom"

    def __init__(self) -> None:
        """Initialize the parser."""
        self.namespaces = {
            "kml": self.KML_NS,
            "gx": self.GX_NS,
            "atom": self.ATOM_NS,
        }

    def parse_from_file(self, file_path: str) -> Tuple[Optional[str], Optional[str], List[Any]]:
        """
        Parse KML file and extract elements.

        Args:
            file_path: Path to KML or KMZ file

        Returns:
            Tuple of (document_name, document_description, elements_list)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"KML file not found: {file_path}")

        try:
            if file_path.lower().endswith(".kmz"):
                content = self._extract_kmz(file_path)
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
        except Exception as e:  # pylint: disable=broad-except
            raise KMLParseError(f"Error reading file: {e}", source=file_path) from e

        return self.parse_from_string(content)

    def parse_from_string(
        self, kml_content: Union[str, bytes]
    ) -> Tuple[Optional[str], Optional[str], List[Any]]:
        """
        Parse KML content string and extract elements.

        Supports Google Earth KML files with unescaped XML entities by attempting
        preprocessing when standard XML parsing fails.

        Args:
            kml_content: KML content as string or bytes

        Returns:
            Tuple of (document_name, document_description, elements_list)
        """
        # First, attempt to parse XML and translate only parse-related
        # exceptions into KMLParseError. Use ParseException alias defined above
        # so behavior is consistent across lxml and stdlib ElementTree.
        try:
            if isinstance(kml_content, str):
                content_bytes = kml_content.encode("utf-8")
            else:
                content_bytes = kml_content

            root = etree.fromstring(content_bytes)
        except ParseException as e:
            # If standard parsing fails, try preprocessing for Google Earth compatibility
            try:
                if isinstance(kml_content, bytes):
                    kml_content = kml_content.decode("utf-8")

                preprocessed_content = self._preprocess_google_earth_entities(kml_content)
                content_bytes = preprocessed_content.encode("utf-8")
                root = etree.fromstring(content_bytes)

                logger.info("Successfully parsed KML after preprocessing Google Earth entities")
            except ParseException:
                # If preprocessing also fails, raise the original error
                raise KMLParseError(f"Invalid XML syntax: {e}") from e

        # If parsing succeeded, continue extracting data. Wrap extraction in a
        # broad catch so we can present consistent KMLParseError for any
        # unexpected failures during extraction.
        try:
            doc_name, doc_description = self._extract_document_info(root)
            elements = self._extract_all_elements(root)

            return doc_name, doc_description, elements
        except Exception as e:  # pylint: disable=broad-except
            raise KMLParseError(f"Error parsing KML: {e}") from e

    def parse_from_url(self, url: str) -> Tuple[Optional[str], Optional[str], List[Any]]:
        """
        Parse KML from URL.

        Args:
            url: URL to KML or KMZ file

        Returns:
            Tuple of (document_name, document_description, elements_list)
        """
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")

            with urlopen(url) as response:
                content = response.read()

            if url.lower().endswith(".kmz") or self._is_zip_content(content):
                kml_content = self._extract_kmz_from_bytes(content)
            else:
                kml_content = content.decode("utf-8")

            return self.parse_from_string(kml_content)

        except Exception as e:  # pylint: disable=broad-except
            raise KMLParseError(f"Error loading from URL: {e}", source=url) from e

    def _extract_document_info(self, root: Any) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract document name and description from KML root.

        Args:
            root: KML root element

        Returns:
            Tuple of (name, description)
        """
        doc_name = None
        doc_description = None

        # Find Document element
        doc_elem = root.find(".//kml:Document", self.namespaces)
        if doc_elem is not None:
            name_elem = doc_elem.find("kml:name", self.namespaces)
            if name_elem is not None and name_elem.text:
                doc_name = name_elem.text.strip()

            desc_elem = doc_elem.find("kml:description", self.namespaces)
            if desc_elem is not None and desc_elem.text:
                doc_description = desc_elem.text.strip()

        return doc_name, doc_description

    def _extract_all_elements(self, root: Any) -> List[Any]:
        """
        Extract all KML elements from the root.

        Args:
            root: KML root element

        Returns:
            List of extracted KML element objects
        """
        elements = []

        def process_children(parent: Any) -> None:
            """
            Recursively processes the child elements of a given XML parent element,
            identifying and handling KML-specific tags such as Placemark, Folder,
            LineString, Polygon, Point, MultiGeometry, and Document.

            For each recognized tag, the corresponding handler method is called
            to create and append the appropriate geometry or folder object to the
            `elements` list. If a Document element is encountered, its children are
            processed recursively.

            Args:
                parent (Any): The XML parent element whose children will be processed.

            Returns:
                None
            """
            for elem in parent:
                if not hasattr(elem, "tag") or not isinstance(elem.tag, str):
                    continue
                if elem.tag.endswith("}Placemark") or elem.tag == "Placemark":
                    geometry_objects = self._create_placemark_with_geometry(elem)
                    elements.extend(geometry_objects)
                elif elem.tag.endswith("}Folder") or elem.tag == "Folder":
                    folder = self._create_folder(elem)
                    if folder:
                        elements.append(folder)
                elif elem.tag.endswith("}LineString") or elem.tag == "LineString":
                    path = self._create_path_from_linestring(elem)
                    if path:
                        elements.append(path)
                elif elem.tag.endswith("}Polygon") or elem.tag == "Polygon":
                    polygon = self._create_polygon_from_element(elem)
                    if polygon:
                        elements.append(polygon)
                elif elem.tag.endswith("}Point") or elem.tag == "Point":
                    point = self._create_point_from_element(elem)
                    if point:
                        elements.append(point)
                elif elem.tag.endswith("}MultiGeometry") or elem.tag == "MultiGeometry":
                    multigeom = self._create_multigeometry_from_element(elem)
                    if multigeom:
                        elements.append(multigeom)
                elif elem.tag.endswith("}Document") or elem.tag == "Document":
                    process_children(elem)

        process_children(root)
        return elements

    def _create_placemark_with_geometry(self, elem: Any) -> List[Any]:
        """
        Create appropriate objects based on Placemark geometry type.

        Args:
            elem: Placemark XML element

        Returns:
            List of created objects (Placemark, Path, or Polygon)
        """
        objects: List[Any] = []

        # Check what geometry this Placemark contains - MultiGeometry first
        multigeom_elem = elem.find("kml:MultiGeometry", self.namespaces)

        if multigeom_elem is not None:
            # MultiGeometry Placemark - create Placemark with associated MultiGeometry
            multigeom = self._create_multigeometry_from_element(multigeom_elem)
            if multigeom is not None:
                placemark = self._create_placemark_with_multigeometry(elem, multigeom)
                if placemark:
                    objects.append(placemark)
            # Note: MultiGeometry is contained within Placemark, not separate

        else:
            # Check for direct child geometries (not within MultiGeometry)
            point_elem = elem.find("kml:Point", self.namespaces)
            linestring_elem = elem.find("kml:LineString", self.namespaces)
            polygon_elem = elem.find("kml:Polygon", self.namespaces)

            if point_elem is not None:
                # Standard Point Placemark
                placemark = self._create_placemark(elem, point_elem)
                if placemark:
                    objects.append(placemark)

            elif linestring_elem is not None:
                # LineString Placemark - create both Placemark and Path
                placemark = self._create_placemark(elem, None)  # No coordinates in placemark
                if placemark:
                    objects.append(placemark)

                path = self._create_path_from_placemark(elem, linestring_elem)
                if path:
                    objects.append(path)

            elif polygon_elem is not None:
                # Polygon Placemark - create both Placemark and Polygon
                placemark = self._create_placemark(elem, None)  # No coordinates in placemark
                if placemark:
                    objects.append(placemark)

                polygon = self._create_polygon_from_placemark(elem, polygon_elem)
                if polygon:
                    objects.append(polygon)

            else:
                # Placemark with no recognized geometry
                placemark = self._create_placemark(elem, None)
                if placemark:
                    objects.append(placemark)

        return objects

    def _create_placemark(self, elem: Any, point_elem: Optional[Any] = None) -> Optional[Placemark]:
        """
        Create Placemark object from XML element.

        Args:
            elem: Placemark XML element
            point_elem: Optional Point geometry element (if None, searches for it)

        Returns:
            Placemark object or None if invalid
        """
        try:
            # Extract basic attributes
            placemark_data = {
                "id": elem.get("id"),
                "name": self._get_text(elem, "kml:name"),
                "description": self._get_text(elem, "kml:description"),
                "visibility": self._get_bool(elem, "kml:visibility", default=True),
                "address": self._get_text(elem, "kml:address"),
                "phone_number": self._get_text(elem, "kml:phoneNumber"),
                "snippet": self._get_text(elem, "kml:Snippet"),
                "style_url": self._get_text(elem, "kml:styleUrl"),
            }

            # Create Point object from geometry if provided (direct child Points only)
            point_obj = None
            # Only create Point if explicitly provided (means it's a direct child Point)
            # Do NOT search for Points within MultiGeometry elements

            if point_elem is not None:
                coord_elem = point_elem.find("kml:coordinates", self.namespaces)
                if coord_elem is not None and coord_elem.text:
                    coord_string = coord_elem.text.strip()
                    coordinates = self._parse_coordinate_string(coord_string)
                    if coordinates and len(coordinates) > 0:
                        # For Point, we expect a single coordinate tuple
                        point_coords = coordinates[0]

                        point_obj = Point(
                            id=placemark_data["id"],
                            name=placemark_data["name"],
                            description=placemark_data["description"],
                            coordinates=point_coords,
                            extrude=self._get_bool(point_elem, "kml:extrude", default=False),
                            altitude_mode=self._get_text(
                                point_elem, "kml:altitudeMode", default="clampToGround"
                            ),
                            tessellate=self._get_bool(point_elem, "kml:tessellate", default=False),
                        )

            placemark_data["point"] = point_obj

            # Extract extended data
            placemark_data["extended_data"] = self._extract_extended_data(elem)

            return Placemark(**placemark_data)

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            placemark_id = elem.get("id", "unknown")
            placemark_name = self._get_text(elem, "kml:name") or "unnamed"
            logger.warning(
                "Failed to parse Placemark '%s' (id=%s): %s. Skipping this placemark.",
                placemark_name,
                placemark_id,
                str(e),
            )
            return None

    def _create_placemark_with_multigeometry(
        self, elem: Any, multigeometry: MultiGeometry
    ) -> Optional[Placemark]:
        """
        Create Placemark object with associated MultiGeometry.

        Args:
            elem: Placemark XML element
            multigeometry: MultiGeometry object to associate

        Returns:
            Placemark object with MultiGeometry or None if invalid
        """
        try:
            # Extract basic attributes
            placemark_data = {
                "id": elem.get("id"),
                "name": self._get_text(elem, "kml:name"),
                "description": self._get_text(elem, "kml:description"),
                "visibility": self._get_bool(elem, "kml:visibility", default=True),
                "address": self._get_text(elem, "kml:address"),
                "phone_number": self._get_text(elem, "kml:phoneNumber"),
                "snippet": self._get_text(elem, "kml:Snippet"),
                "style_url": self._get_text(elem, "kml:styleUrl"),
                "multigeometry": multigeometry,
            }

            # Extract extended data
            placemark_data["extended_data"] = self._extract_extended_data(elem)

            return Placemark(**placemark_data)

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            placemark_id = elem.get("id", "unknown")
            placemark_name = self._get_text(elem, "kml:name") or "unnamed"
            logger.warning(
                "Failed to parse MultiGeometry Placemark '%s' (id=%s): %s. "
                "Skipping this placemark.",
                placemark_name,
                placemark_id,
                str(e),
            )
            return None

    def _create_folder(self, elem: Any) -> Optional[Folder]:
        """
        Create Folder object from XML element and parse child elements.

        Args:
            elem: Folder XML element

        Returns:
            Folder object or None if invalid
        """
        try:
            folder_data = {
                "id": elem.get("id"),
                "name": self._get_text(elem, "kml:name"),
                "description": self._get_text(elem, "kml:description"),
                "visibility": self._get_bool(elem, "kml:visibility", default=True),
            }

            folder = Folder(**folder_data)

            # Parse child elements and associate them with this folder
            self._parse_folder_children(folder, elem)

            return folder

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            folder_id = elem.get("id", "unknown")
            folder_name = self._get_text(elem, "kml:name") or "unnamed"
            logger.warning(
                "Failed to parse Folder '%s' (id=%s): %s. Skipping this folder.",
                folder_name,
                folder_id,
                str(e),
            )
            return None

    def _parse_folder_children(self, folder: "Folder", elem: Any) -> None:
        """
        Parse child elements of a folder and associate them with the folder.

        Args:
            folder: Folder object to populate
            elem: XML element containing child elements
        """

        # Parse direct child elements only (not all descendants)
        for child_elem in elem:
            # Skip non-element nodes
            if not hasattr(child_elem, "tag") or not isinstance(child_elem.tag, str):
                continue

            if child_elem.tag.endswith("}Placemark") or child_elem.tag == "Placemark":
                # Create placemark(s) and add to folder
                geometry_objects = self._create_placemark_with_geometry(child_elem)
                for obj in geometry_objects:
                    if isinstance(obj, Placemark):
                        folder.placemarks.add(obj)
                    elif isinstance(obj, Path):
                        folder.paths.add(obj)
                    elif isinstance(obj, Polygon):
                        folder.polygons.add(obj)
                    elif isinstance(obj, Point):
                        folder.points.add(obj)

            elif child_elem.tag.endswith("}Folder") or child_elem.tag == "Folder":
                # Create nested folder and add to parent folder
                nested_folder = self._create_folder(child_elem)
                if nested_folder:
                    folder.folders.add(nested_folder)

            elif child_elem.tag.endswith("}LineString") or child_elem.tag == "LineString":
                # Standalone LineString (not in Placemark)
                path = self._create_path_from_linestring(child_elem)
                if path:
                    folder.paths.add(path)

            elif child_elem.tag.endswith("}Polygon") or child_elem.tag == "Polygon":
                # Standalone Polygon (not in Placemark)
                polygon = self._create_polygon_from_element(child_elem)
                if polygon:
                    folder.polygons.add(polygon)

    def _create_path_from_placemark(
        self, placemark_elem: Any, linestring_elem: Any
    ) -> Optional[Path]:
        """
        Create Path object from Placemark containing LineString.

        Args:
            placemark_elem: Parent Placemark XML element
            linestring_elem: LineString XML element

        Returns:
            Path object or None if invalid
        """
        try:
            # Extract coordinates from LineString
            coord_elem = linestring_elem.find("kml:coordinates", self.namespaces)
            coordinates_raw = (
                coord_elem.text.strip() if coord_elem is not None and coord_elem.text else ""
            )

            path_data = {
                "id": placemark_elem.get("id"),
                "name": self._get_text(placemark_elem, "kml:name"),
                "description": self._get_text(placemark_elem, "kml:description"),
                "coordinates": self._parse_coordinate_string(coordinates_raw),
                "tessellate": self._get_bool(linestring_elem, "kml:tessellate", default=False),
                "altitude_mode": self._get_text(
                    linestring_elem, "kml:altitudeMode", default="clampToGround"
                ),
            }

            return Path(**path_data)

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            placemark_id = placemark_elem.get("id", "unknown")
            placemark_name = self._get_text(placemark_elem, "kml:name") or "unnamed"
            logger.warning(
                "Failed to parse Path from Placemark '%s' (id=%s): %s. Skipping this path.",
                placemark_name,
                placemark_id,
                str(e),
            )
            return None

    def _create_polygon_from_placemark(
        self, placemark_elem: Any, polygon_elem: Any
    ) -> Optional[Polygon]:
        """
        Create Polygon object from Placemark containing Polygon.

        Args:
            placemark_elem: Parent Placemark XML element
            polygon_elem: Polygon XML element

        Returns:
            Polygon object or None if invalid
        """
        try:
            # Extract outer boundary
            outer_elem = polygon_elem.find(
                ".//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates", self.namespaces
            )
            outer_coords = (
                outer_elem.text.strip() if outer_elem is not None and outer_elem.text else ""
            )

            # Extract inner boundaries (holes)
            inner_boundaries = []
            for inner_elem in polygon_elem.findall(
                ".//kml:innerBoundaryIs/kml:LinearRing/kml:coordinates", self.namespaces
            ):
                if inner_elem.text:
                    inner_boundaries.append(self._parse_coordinate_string(inner_elem.text.strip()))

            polygon_data = {
                "id": placemark_elem.get("id"),
                "name": self._get_text(placemark_elem, "kml:name"),
                "description": self._get_text(placemark_elem, "kml:description"),
                "outer_boundary": self._parse_coordinate_string(outer_coords),
                "inner_boundaries": inner_boundaries,
                "extrude": self._get_bool(polygon_elem, "kml:extrude", default=False),
                "altitude_mode": self._get_text(
                    polygon_elem, "kml:altitudeMode", default="clampToGround"
                ),
            }

            return Polygon(**polygon_data)

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            placemark_id = placemark_elem.get("id", "unknown")
            placemark_name = self._get_text(placemark_elem, "kml:name") or "unnamed"
            logger.warning(
                "Failed to parse Polygon from Placemark '%s' (id=%s): %s. Skipping this polygon.",
                placemark_name,
                placemark_id,
                str(e),
            )
            return None

    def _create_path_from_linestring(self, elem: Any) -> Optional[Path]:
        """
        Create Path object from LineString XML element.

        Args:
            elem: LineString XML element

        Returns:
            Path object or None if invalid
        """
        try:
            # Get parent Placemark for name/description
            parent = elem.getparent()
            if parent is not None and (
                parent.tag.endswith("}Placemark") or parent.tag == "Placemark"
            ):
                name = self._get_text(parent, "kml:name")
                description = self._get_text(parent, "kml:description")
                placemark_id = parent.get("id")
            else:
                name = None
                description = None
                placemark_id = None

            # Extract coordinates
            coord_elem = elem.find("kml:coordinates", self.namespaces)
            coordinates_raw = (
                coord_elem.text.strip() if coord_elem is not None and coord_elem.text else ""
            )

            path_data = {
                "id": placemark_id,
                "name": name,
                "description": description,
                "coordinates": self._parse_coordinate_string(coordinates_raw),
                "tessellate": self._get_bool(elem, "kml:tessellate", default=False),
                "altitude_mode": self._get_text(elem, "kml:altitudeMode", default="clampToGround"),
            }

            return Path(**path_data)

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            elem_id = elem.get("id", "unknown")
            logger.warning(
                "Failed to parse LineString Path (id=%s): %s. Skipping this path.", elem_id, str(e)
            )
            return None

    def _create_polygon_from_element(self, elem: Any) -> Optional[Polygon]:
        """
        Create Polygon object from Polygon XML element.

        Args:
            elem: Polygon XML element

        Returns:
            Polygon object or None if invalid
        """
        try:
            # Get parent Placemark for name/description
            parent = elem.getparent()
            if parent is not None and (
                parent.tag.endswith("}Placemark") or parent.tag == "Placemark"
            ):
                name = self._get_text(parent, "kml:name")
                description = self._get_text(parent, "kml:description")
                placemark_id = parent.get("id")
            else:
                name = None
                description = None
                placemark_id = None

            # Extract outer boundary
            outer_elem = elem.find(
                ".//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates", self.namespaces
            )
            outer_coords = (
                outer_elem.text.strip() if outer_elem is not None and outer_elem.text else ""
            )

            # Extract inner boundaries (holes)
            inner_boundaries = []
            for inner_elem in elem.findall(
                ".//kml:innerBoundaryIs/kml:LinearRing/kml:coordinates", self.namespaces
            ):
                if inner_elem.text:
                    inner_boundaries.append(self._parse_coordinate_string(inner_elem.text.strip()))

            polygon_data = {
                "id": placemark_id,
                "name": name,
                "description": description,
                "outer_boundary": self._parse_coordinate_string(outer_coords),
                "inner_boundaries": inner_boundaries,
                "extrude": self._get_bool(elem, "kml:extrude", default=False),
                "altitude_mode": self._get_text(elem, "kml:altitudeMode", default="clampToGround"),
            }

            return Polygon(**polygon_data)

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            elem_id = elem.get("id", "unknown")
            logger.warning(
                "Failed to parse Polygon element (id=%s): %s. Skipping this polygon.",
                elem_id,
                str(e),
            )
            return None

    def _create_point_from_element(self, elem: Any) -> Optional[Point]:
        """
        Create Point object from standalone Point XML element.

        Args:
            elem: Point XML element

        Returns:
            Point object or None if invalid
        """
        try:
            # Get parent element for name/description if available
            parent = elem.getparent()
            if parent is not None and (
                parent.tag.endswith("}Placemark") or parent.tag == "Placemark"
            ):
                name = self._get_text(parent, "kml:name")
                description = self._get_text(parent, "kml:description")
                point_id = parent.get("id")
            else:
                name = None
                description = None
                point_id = elem.get("id")

            # Extract coordinates
            coord_elem = elem.find("kml:coordinates", self.namespaces)
            coordinates: Optional[Tuple[float, ...]] = None
            if coord_elem is not None and coord_elem.text:
                coord_string = coord_elem.text.strip()
                if coord_string:
                    coord_list = self._parse_coordinate_string(coord_string)
                    # For Point, we expect a single coordinate tuple
                    if coord_list and len(coord_list) > 0:
                        coordinates = coord_list[0]

            point_data = {
                "id": point_id,
                "name": name,
                "description": description,
                "coordinates": coordinates,
                "extrude": self._get_bool(elem, "kml:extrude", default=False),
                "altitude_mode": self._get_text(elem, "kml:altitudeMode", default="clampToGround"),
                "tessellate": self._get_bool(elem, "kml:tessellate", default=False),
            }

            return Point(**point_data)

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            point_id = elem.get("id", "unknown")
            logger.warning(
                "Failed to parse Point element (id=%s): %s. Skipping this point.", point_id, str(e)
            )
            return None

    def _create_multigeometry_from_element(self, elem: Any) -> Optional[MultiGeometry]:
        """
        Create MultiGeometry object from MultiGeometry XML element.

        Args:
            elem: MultiGeometry XML element

        Returns:
            MultiGeometry object or None if invalid
        """
        try:
            # Get parent element for name/description if available
            parent = elem.getparent()
            if parent is not None and (
                parent.tag.endswith("}Placemark") or parent.tag == "Placemark"
            ):
                name = self._get_text(parent, "kml:name")
                description = self._get_text(parent, "kml:description")
                multigeom_id = parent.get("id")
            else:
                name = None
                description = None
                multigeom_id = elem.get("id")

            # Create MultiGeometry container
            multigeom = MultiGeometry(id=multigeom_id, name=name, description=description)

            # Find and create contained geometries
            for child_elem in elem:
                if child_elem.tag.endswith("}Point") or child_elem.tag == "Point":
                    point = self._create_point_from_element(child_elem)
                    if point:
                        multigeom.add_geometry(point)

                elif child_elem.tag.endswith("}LineString") or child_elem.tag == "LineString":
                    path = self._create_path_from_linestring(child_elem)
                    if path:
                        multigeom.add_geometry(path)

                elif child_elem.tag.endswith("}Polygon") or child_elem.tag == "Polygon":
                    polygon = self._create_polygon_from_element(child_elem)
                    if polygon:
                        multigeom.add_geometry(polygon)

                elif child_elem.tag.endswith("}MultiGeometry") or child_elem.tag == "MultiGeometry":
                    # Nested MultiGeometry (recursive)
                    nested_multigeom = self._create_multigeometry_from_element(child_elem)
                    if nested_multigeom:
                        multigeom.add_geometry(nested_multigeom)

            return multigeom

        except Exception as e:  # pylint: disable=broad-except
            # Log the error with context about what went wrong
            elem_id = elem.get("id", "unknown")
            logger.warning(
                "Failed to parse MultiGeometry element (id=%s): %s. Skipping this multigeometry.",
                elem_id,
                str(e),
            )
            return None

    def _extract_extended_data(self, elem: Any) -> Dict[str, str]:
        """
        Extract extended data from element.

        Args:
            elem: XML element containing ExtendedData

        Returns:
            Dictionary of extended data key-value pairs
        """
        extended_data = {}

        # Find ExtendedData element
        ext_data_elem = elem.find("kml:ExtendedData", self.namespaces)
        if ext_data_elem is not None:
            # Extract Data elements
            for data_elem in ext_data_elem.findall("kml:Data", self.namespaces):
                name = data_elem.get("name")
                value_elem = data_elem.find("kml:value", self.namespaces)
                if name and value_elem is not None and value_elem.text:
                    extended_data[name] = value_elem.text

            # Extract SchemaData elements
            for schema_elem in ext_data_elem.findall("kml:SchemaData", self.namespaces):
                for simple_elem in schema_elem.findall("kml:SimpleData", self.namespaces):
                    name = simple_elem.get("name")
                    if name and simple_elem.text:
                        extended_data[name] = simple_elem.text

        return extended_data

    def _parse_coordinate_string(self, coord_string: str) -> List[Tuple[float, ...]]:
        """
        Parse coordinate string into list of coordinate tuples.

        Args:
            coord_string: Raw coordinate string from KML

        Returns:
            List of (longitude, latitude, altitude) tuples
        """
        if not coord_string or not coord_string.strip():
            return []

        coordinates: List[Tuple[float, ...]] = []
        # Split by whitespace and commas, handle various formats
        parts = coord_string.replace(",", " ").split()

        # Group by 3s (lon, lat, alt) or 2s (lon, lat)
        i = 0
        while i < len(parts):
            try:
                if i + 2 < len(parts):
                    # Has altitude
                    lon = float(parts[i])
                    lat = float(parts[i + 1])
                    alt = float(parts[i + 2])
                    coordinates.append((lon, lat, alt))
                    i += 3
                elif i + 1 < len(parts):
                    # No altitude
                    lon = float(parts[i])
                    lat = float(parts[i + 1])
                    coordinates.append((lon, lat))
                    i += 2
                else:
                    break
            except ValueError:
                # Skip invalid coordinates
                i += 1

        return coordinates

    def _get_text(self, parent: Any, xpath: str, default: Optional[str] = None) -> Optional[str]:
        """Get text content from child element."""
        elem = parent.find(xpath, self.namespaces)
        if elem is not None and elem.text:
            return str(elem.text).strip()
        return default

    def _get_bool(self, parent: Any, xpath: str, default: bool = False) -> bool:
        """Get boolean value from child element."""
        text = self._get_text(parent, xpath)
        if text is None:
            return default
        return text.lower() in ("1", "true", "yes")

    @staticmethod
    def _extract_kmz(file_path: str) -> str:
        """Extract KML content from KMZ file."""
        try:
            with zipfile.ZipFile(file_path, "r") as kmz:
                kml_files = [f for f in kmz.namelist() if f.endswith(".kml")]

                if "doc.kml" in kml_files:
                    kml_file = "doc.kml"
                elif kml_files:
                    kml_file = kml_files[0]
                else:
                    raise KMLParseError("No KML file found in KMZ archive")

                with kmz.open(kml_file) as kml_content:
                    return kml_content.read().decode("utf-8")

        except zipfile.BadZipFile as bzf:
            raise KMLParseError("Invalid KMZ file format") from bzf
        except Exception as e:  # pylint: disable=broad-except
            raise KMLParseError(f"Error extracting KMZ: {e}") from e

    @staticmethod
    def _extract_kmz_from_bytes(content: bytes) -> str:
        """Extract KML content from KMZ bytes."""
        import io

        try:
            with zipfile.ZipFile(io.BytesIO(content), "r") as kmz:
                kml_files = [f for f in kmz.namelist() if f.endswith(".kml")]

                if "doc.kml" in kml_files:
                    kml_file = "doc.kml"
                elif kml_files:
                    kml_file = kml_files[0]
                else:
                    raise KMLParseError("No KML file found in KMZ archive")

                with kmz.open(kml_file) as kml_content:
                    return kml_content.read().decode("utf-8")

        except zipfile.BadZipFile as bzf:
            raise KMLParseError("Invalid KMZ content") from bzf
        except Exception as e:  # pylint: disable=broad-except
            raise KMLParseError(f"Error extracting KMZ: {e}") from e

    @staticmethod
    def _is_zip_content(content: bytes) -> bool:
        """Check if content appears to be a ZIP file."""
        return content.startswith(b"PK")

    @staticmethod
    def _preprocess_google_earth_entities(kml_content: str) -> str:
        """
        Preprocess KML content to escape common unescaped XML entities.

        Google Earth sometimes produces KML files with unescaped entities in
        metadata URLs and text content. This method handles the most common cases.

        Args:
            kml_content: Raw KML content string

        Returns:
            KML content with entities properly escaped
        """
        # Common Google Earth entity escaping patterns
        # Handle & that are not already part of an entity
        kml_content = kml_content.replace("&", "&amp;")

        # Fix double-escaping of already escaped entities
        kml_content = kml_content.replace("&amp;amp;", "&amp;")
        kml_content = kml_content.replace("&amp;lt;", "&lt;")
        kml_content = kml_content.replace("&amp;gt;", "&gt;")
        kml_content = kml_content.replace("&amp;quot;", "&quot;")
        kml_content = kml_content.replace("&amp;apos;", "&apos;")

        # Handle < and > in text content (but not in XML tags)
        # This is a simplified approach - more sophisticated parsing could be added
        # if needed for specific Google Earth metadata patterns

        return kml_content
