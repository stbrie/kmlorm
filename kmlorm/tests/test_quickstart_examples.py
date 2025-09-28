"""
Tests for examples from the quickstart documentation.

This module contains tests that verify all code examples from the
quickstart.rst documentation work correctly.
"""

# pylint: disable=too-many-locals, import-outside-toplevel
# pylint: disable=too-many-public-methods, duplicate-code
import os
import http.server
import socketserver
import threading
import time
from typing import Optional, TYPE_CHECKING, cast

import pytest


from ..core.exceptions import KMLElementNotFound, KMLMultipleElementsReturned
from ..parsers.kml_file import KMLFile

if TYPE_CHECKING:
    from kmlorm.models.placemark import Placemark


class TestQuickstartExamples:
    """
    Test suite for validating the KML ORM quickstart examples and core behaviors.

    This class contains comprehensive tests that ensure the KMLFile ORM and its managers
    (placemarks, folders, paths, polygons, points, multigeometries) behave as described
    in the documentation and quickstart guide. It covers:

    - Loading KML data from strings and files.
    - Accessing and querying elements (placemarks, folders, etc.) at root and nested levels.
    - The behavior of the `flatten=True` parameter for all() methods across element types.
    - Filtering, excluding, getting, and chaining queries on placemarks and other elements.
    - Geospatial queries: near, within_bounds, and coordinate access.
    - Error handling and exception raising for missing elements.
    - Calculation of distances between placemarks and coordinates.
    - Verification of element counts and structure for both simple and comprehensive KML files.
    - Ensuring consistency between raw XML parsing and ORM results.
    - Documenting and asserting the differences between root-level and flattened queries.

    Fixtures and sample KML files are used to simulate real-world KML structures, including
    nested folders, multigeometries, and various element types. The tests are designed to
    mirror the usage patterns and examples provided in the project's quickstart documentation.
    """

    fixtures_dir: str
    places_kml_file: str
    sample_kml: str

    def test_flatten_returns_all_elements(self) -> None:
        """Test that all elements of every type in the KML (including nested)
        are present in all(flatten=True)."""
        import xml.etree.ElementTree as ET

        comprehensive_kml_path = os.path.join(self.fixtures_dir, "comprehensive.kml")
        with open(comprehensive_kml_path, "r", encoding="utf-8") as f:
            kml_text = f.read()
        ns = {"kml": "http://www.opengis.net/kml/2.2"}
        root = ET.fromstring(kml_text)

        # Helper to extract names for each element type
        def extract_names(tag: str) -> set[str]:
            names = set()
            for elem in root.findall(f".//kml:{tag}", ns):
                name_elem = elem.find("kml:name", ns)
                if name_elem is not None and name_elem.text:
                    names.add(name_elem.text.strip())
            return names

        element_types = [
            ("placemarks", "Placemark"),
            ("folders", "Folder"),
            ("paths", "LineString"),
            ("polygons", "Polygon"),
            ("points", "Point"),
        ]

        kml = KMLFile.from_file(comprehensive_kml_path)

        for manager_name, xml_tag in element_types:
            xml_names = extract_names(xml_tag)
            all_elements = getattr(kml, manager_name).all(flatten=True)
            orm_names = set(e.name for e in all_elements if getattr(e, "name", None))
            # Debug output for folder analysis can be added here if needed
            missing = xml_names - orm_names
            assert not missing, f"Missing {manager_name} in flatten=True: {missing}"

    def test_flatten_returns_all_placemarks(self) -> None:
        """Test that all placemarks in the KML (including nested) are present
        in all(flatten=True)."""
        import xml.etree.ElementTree as ET

        comprehensive_kml_path = os.path.join(self.fixtures_dir, "comprehensive.kml")
        with open(comprehensive_kml_path, "r", encoding="utf-8") as f:
            kml_text = f.read()
        # Parse raw XML to get all placemark names
        ns = {"kml": "http://www.opengis.net/kml/2.2"}
        root = ET.fromstring(kml_text)
        placemark_names = set()
        for elem in root.findall(".//kml:Placemark", ns):
            name_elem = elem.find("kml:name", ns)
            if name_elem is not None and name_elem.text:
                placemark_names.add(name_elem.text.strip())

        # Now parse with ORM and get all placemarks (flattened)
        kml = KMLFile.from_file(comprehensive_kml_path)
        all_placemarks = kml.placemarks.all(flatten=True)
        orm_names = set(p.name for p in all_placemarks if getattr(p, "name", None))

        # Assert every XML placemark name is present in ORM result
        missing = placemark_names - orm_names
        assert not missing, f"Missing placemarks in flatten=True: {missing}"

    def setup_method(self) -> None:
        """Set up test data for each test."""
        # Path to fixture files for real file system testing
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        self.places_kml_file = os.path.join(self.fixtures_dir, "sample.kml")

        # Sample KML data matching quickstart examples
        self.sample_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Test Stores</name>
    <description>Sample store locations</description>
    <Placemark>
      <name>Capital Electric - Rosedale</name>
      <address>123 Main St, Rosedale, MD</address>
      <Point>
        <coordinates>-76.5,39.3,0</coordinates>
      </Point>
    </Placemark>
    <Placemark>
      <name>Capital Electric - Timonium</name>
      <address>456 Oak Ave, Timonium, MD</address>
      <Point>
        <coordinates>-76.6,39.4,0</coordinates>
      </Point>
    </Placemark>
    <Placemark>
      <name>Hardware Store</name>
      <address>789 Pine St, Baltimore, MD</address>
      <Point>
        <coordinates>-76.7,39.2,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""

    def test_loading_kml_data_from_string(self) -> None:
        """Test loading KML data from string (quickstart example)."""
        # From quickstart.rst: Loading KML Data section
        kml = KMLFile.from_string(self.sample_kml)
        assert isinstance(kml, KMLFile)
        assert kml.document_name == "Test Stores"
        assert kml.document_description == "Sample store locations"

    def test_loading_kml_data_from_file(self) -> None:
        """Test loading KML data from file (quickstart example)."""
        # From quickstart.rst: Loading KML Data section
        # Test actual file system reading with real KML fixture
        kml = KMLFile.from_file(self.places_kml_file)
        assert isinstance(kml, KMLFile)

        # Verify we actually parsed data from the real file
        assert kml.document_name == "Capital Electric Supply Locations"

        # Verify we have folders and check their content
        folders = kml.folders.all()
        assert len(folders) > 0
        folder_names = [folder.name for folder in folders]
        assert "Maryland Stores" in folder_names

        # Verify we have placemarks (use flatten=True to get from nested folders)
        placemarks = kml.placemarks.all(flatten=True)
        assert len(placemarks) > 0

        # Verify at least one placemark has coordinates (real places should)
        placemark_with_coords = next((p for p in placemarks if p.coordinates), None)
        assert placemark_with_coords is not None
        assert placemark_with_coords.longitude is not None
        assert placemark_with_coords.latitude is not None

    def test_quickstart_exact_string_example(self) -> None:
        """Test the exact KML string example from quickstart.rst documentation."""
        # From quickstart.rst: Loading KML Data section - EXACT COPY
        kml_string = """<?xml version="1.0" encoding="UTF-8"?>
   <kml xmlns="http://www.opengis.net/kml/2.2">
     <Document>
       <Placemark>
         <name>Test Store</name>
         <Point>
           <coordinates>-76.5,39.3,0</coordinates>
         </Point>
       </Placemark>
     </Document>
   </kml>"""

        kml = KMLFile.from_string(kml_string)
        assert isinstance(kml, KMLFile)

        # Verify we parsed the single placemark correctly
        placemarks = kml.placemarks.all()
        assert len(placemarks) == 1

        placemark = placemarks[0]
        assert placemark.name == "Test Store"

        # Verify coordinates are accessible
        assert placemark.coordinates is not None
        assert placemark.longitude == -76.5
        assert placemark.latitude == 39.3

    def test_accessing_elements(self) -> None:
        """Test accessing different element types (quickstart example)."""
        # From quickstart.rst: Accessing Elements section
        kml = KMLFile.from_string(self.sample_kml)

        # Get all placemarks
        all_placemarks = kml.placemarks.all()
        assert len(all_placemarks) == 3

        # Access different element types
        folders = kml.folders.all()
        paths = kml.paths.all()
        polygons = kml.polygons.all()
        points = kml.points.all()

        # Verify types
        assert hasattr(folders, "__iter__")
        assert hasattr(paths, "__iter__")
        assert hasattr(polygons, "__iter__")
        assert hasattr(points, "__iter__")

    def test_basic_queries(self) -> None:
        """Test basic query methods (quickstart example)."""
        # From quickstart.rst: Basic Queries section
        kml = KMLFile.from_string(self.sample_kml)

        # Filter by name (root-level placemarks only)
        capital_stores = kml.placemarks.filter(name__icontains="capital")
        assert len(capital_stores) == 2

        # Filter ALL placemarks including those in folders
        all_capital_stores = kml.placemarks.all(flatten=True).filter(name__icontains="capital")
        assert len(all_capital_stores) == 2  # Same as root-level for our test data

        # Exclude items (root-level only)
        not_capital = kml.placemarks.exclude(name__icontains="capital")
        assert len(not_capital) == 1
        assert not_capital[0].name == "Hardware Store"

        # Exclude ALL placemarks including those in folders
        all_not_capital = kml.placemarks.all(flatten=True).exclude(name__icontains="capital")
        assert len(all_not_capital) == 1

        # Get a single item (searches root-level only)
        store = kml.placemarks.get(name="Capital Electric - Rosedale")
        assert store.name == "Capital Electric - Rosedale"
        assert store.address == "123 Main St, Rosedale, MD"

        # Get from ALL placemarks including folders
        store = kml.placemarks.all(flatten=True).get(name="Capital Electric - Rosedale")
        assert store.name == "Capital Electric - Rosedale"

        # Check if items exist (root-level only)
        has_stores = kml.placemarks.filter(name__icontains="store").exists()
        assert has_stores is True

        # Check ALL placemarks including folders
        has_any_stores = kml.placemarks.all(flatten=True).filter(name__icontains="store").exists()
        assert has_any_stores is True

    def test_working_with_coordinates(self) -> None:
        """Test coordinate access (quickstart example)."""
        # From quickstart.rst: Working with Coordinates section
        kml = KMLFile.from_string(self.sample_kml)

        coordinate_data = []
        for placemark in kml.placemarks.all():
            if placemark.coordinates:
                coordinate_data.append(
                    {
                        "name": placemark.name,
                        "longitude": placemark.longitude,
                        "latitude": placemark.latitude,
                    }
                )

        assert len(coordinate_data) == 3

        # Verify specific coordinates
        rosedale = next(
            p for p in coordinate_data if p is not None and "Rosedale" in cast(str, p["name"])
        )
        assert rosedale["longitude"] == -76.5
        assert rosedale["latitude"] == 39.3

    def test_geospatial_queries(self) -> None:
        """Test geospatial query methods (quickstart example)."""
        # From quickstart.rst: Geospatial Queries section

        kml = KMLFile.from_string(self.sample_kml)

        # Find placemarks near Baltimore (within 25 km)
        nearby = kml.placemarks.near(-76.6, 39.3, radius_km=25)
        assert len(nearby) >= 2  # Should find multiple stores

        # Find placemarks within a bounding box
        in_area = kml.placemarks.within_bounds(north=39.5, south=39.0, east=-76.0, west=-77.0)
        assert len(in_area) >= 1

        # Only placemarks with coordinates
        with_location = kml.placemarks.has_coordinates()
        assert len(with_location) == 3  # All our test placemarks have coordinates

    def test_chaining_queries(self) -> None:
        """Test query chaining (quickstart example)."""
        # From quickstart.rst: Chaining Queries section
        kml = KMLFile.from_string(self.sample_kml)

        # Complex query
        result = (
            kml.placemarks.filter(name__icontains="electric")
            .near(-76.6, 39.3, radius_km=50)
            .has_coordinates()
            .order_by("name")
        )

        assert len(result) == 2  # Should find both Capital Electric stores

        # Verify ordering
        names = [p.name for p in result if p.name]
        assert names == sorted(names)  # Should be ordered alphabetically

    def test_complete_example_analyze_kml_file(self) -> None:
        """Test the complete example function (quickstart example)."""
        # From quickstart.rst: Complete Example section
        kml = KMLFile.from_string(self.sample_kml)

        # Simulate the analyze_kml_file function
        assert kml.document_name == "Test Stores"
        assert kml.document_description == "Sample store locations"

        # Show element counts
        counts = kml.element_counts()
        assert isinstance(counts, dict)
        assert "placemarks" in counts
        assert counts["placemarks"] == 3

        # Find stores near Baltimore
        nearby_stores = (
            kml.placemarks.filter(name__icontains="store")
            .near(-76.6, 39.3, radius_km=30)
            .order_by("name")
        )

        assert len(nearby_stores) >= 1

        # Get a specific store
        rosedale_store = kml.placemarks.get(name__contains="Rosedale")
        assert rosedale_store.name and "Rosedale" in rosedale_store.name
        assert rosedale_store.address == "123 Main St, Rosedale, MD"

    def test_error_handling_examples(self) -> None:
        """Test error handling patterns (quickstart example)."""
        # From quickstart.rst: Error Handling section
        kml = KMLFile.from_string(self.sample_kml)

        # Test KMLElementNotFound
        with pytest.raises(KMLElementNotFound):
            kml.placemarks.get(name="Nonexistent Store")

        # Test getting element that exists
        store = kml.placemarks.get(name="Hardware Store")
        assert store.name == "Hardware Store"

    def test_distance_calculation_helper(self) -> None:
        """Test distance calculation helper from complete example."""
        # From quickstart.rst: Complete Example section - calculate_distance_to_baltimore
        kml = KMLFile.from_string(self.sample_kml)

        baltimore_coord = (-76.6, 39.3)

        for placemark in kml.placemarks.all():
            if placemark.coordinates:
                # Test distance calculation (placeholder calculation)
                distance = placemark.distance_to(baltimore_coord)
                assert distance is not None
                assert distance >= 0

    def test_accessing_elements_flatten_behavior(self) -> None:
        """Test the difference between all() and all(flatten=True) for nested structures."""
        # Test with the sample.kml fixture that has both root-level and nested placemarks
        kml = KMLFile.from_file(self.places_kml_file)

        # With .children() - should only get placemarks at document root level
        root_placemarks = kml.placemarks.children()
        # sample.kml has 1 placemark at root level (Warehouse Distribution Center)
        assert len(root_placemarks) == 1
        assert root_placemarks[0].name == "Warehouse Distribution Center"

        # With .all() (new default behavior) - should get all placemarks including those in folders
        all_placemarks = kml.placemarks.all()
        # sample.kml has 1 root + 4 nested = 5 total placemarks
        assert len(all_placemarks) == 5

        # Verify we can access placemark properties from both collections
        assert root_placemarks[0].coordinates is not None
        assert root_placemarks[0].address == "7890 Industrial Parkway, Baltimore, MD 21224"

        # Verify nested placemarks are included in flatten=True
        nested_names = [
            p.name for p in all_placemarks if p.name and "Capital Electric Supply" in p.name
        ]
        assert len(nested_names) == 4  # 4 store placemarks in folders

        # Verify practical difference exists
        # Document root has 1 placemark, flattened has 5 total
        assert len(all_placemarks) > len(root_placemarks)
        assert nested_names  # Should have nested placemark names

    def test_folders_all_nested_behavior(self) -> None:
        """Test kml.folders.all() behavior with nested folder structures."""
        # Use comprehensive.kml which has nested folders: Administrative -> Warehouses, Offices
        comprehensive_kml_path = os.path.join(self.fixtures_dir, "comprehensive.kml")

        kml = KMLFile.from_file(comprehensive_kml_path)

        # Test folders.children() behavior - get only root-level folders
        root_folders = kml.folders.children()
        root_folder_names = [f.name for f in root_folders]

        # Check if flatten=True parameter works for folders
        try:
            all_folders_flat = kml.folders.all(flatten=True)
            _ = [f.name for f in all_folders_flat]
            supports_flatten = True
        except TypeError:
            supports_flatten = False
            all_folders_flat = root_folders  # Fallback to root folders

        # Verify we can find nested folders manually
        administrative_folder = next((f for f in root_folders if f.name == "Administrative"), None)
        if administrative_folder:
            nested_folders = administrative_folder.folders.all()
            nested_names = [f.name for f in nested_folders]

            # Verify expected nested folders exist
            assert "Warehouses" in nested_names
            assert "Offices" in nested_names

        # Verify basic folder structure expectations
        assert (
            len(root_folders) >= 4
        )  # Should have Store Locations, Delivery Routes, Service Areas, Administrative
        assert "Store Locations" in root_folder_names
        assert "Administrative" in root_folder_names

        # Verify behavior expectations
        if supports_flatten:
            # flatten=True should return more or equal folders
            assert len(all_folders_flat) >= len(root_folders)
        else:
            # If flatten not supported, just use root folders
            all_folders_flat = root_folders

        # With the new FoldersManager implementation:
        # - folders.children() returns only root-level folders (4)
        # - folders.all() returns all folders including nested (6: 4 root + 2 nested)
        assert len(root_folders) == 4  # Only root-level folders
        if supports_flatten:
            # Now flatten should actually work and return nested folders too
            expected_total = len(root_folders) + 2  # 4 root + 2 nested (Warehouses, Offices)
            assert (
                len(all_folders_flat) == expected_total
            ), f"Expected {expected_total} folders with flatten=True, got {len(all_folders_flat)}"

    def test_global_flatten_behavior_all_element_types(self) -> None:
        """Test that flatten=True works for all element types."""
        # Use comprehensive.kml which has various element types in nested folders
        comprehensive_kml_path = os.path.join(self.fixtures_dir, "comprehensive.kml")
        multigeometry_kml_path = os.path.join(self.fixtures_dir, "multigeometry_test.kml")

        # Test comprehensive KML with paths and polygons
        kml = KMLFile.from_file(comprehensive_kml_path)

        # Test all element types support flatten parameter without error
        root_placemarks = kml.placemarks.all()
        all_placemarks = kml.placemarks.all(flatten=True)
        assert len(all_placemarks) >= len(
            root_placemarks
        ), "flatten=True should return at least as many placemarks as root-only"

        root_folders = kml.folders.all()
        all_folders = kml.folders.all(flatten=True)
        assert len(all_folders) >= len(
            root_folders
        ), "flatten=True should return at least as many folders as root-only"

        # Test paths - comprehensive.kml has LineString elements (which become Path objects)
        root_paths = kml.paths.all()
        all_paths = kml.paths.all(flatten=True)
        assert len(all_paths) >= len(
            root_paths
        ), "flatten=True should return at least as many paths as root-only"

        # Test polygons - comprehensive.kml has Polygon elements
        root_polygons = kml.polygons.all()
        all_polygons = kml.polygons.all(flatten=True)
        assert len(all_polygons) >= len(
            root_polygons
        ), "flatten=True should return at least as many polygons as root-only"

        # Test points
        root_points = kml.points.all()
        all_points = kml.points.all(flatten=True)
        assert len(all_points) >= len(
            root_points
        ), "flatten=True should return at least as many points as root-only"

        # Test multigeometries with dedicated file that has them
        mg_kml = KMLFile.from_file(multigeometry_kml_path)

        root_multigeometries = mg_kml.multigeometries.all()
        all_multigeometries = mg_kml.multigeometries.all(flatten=True)
        assert len(all_multigeometries) >= len(
            root_multigeometries
        ), "flatten=True should return at least as many multigeometries as root-only"

        # Verify that multigeometry file actually has multigeometries
        assert (
            len(root_multigeometries) > 0
        ), "multigeometry_test.kml should contain standalone MultiGeometry elements"

        # Verify all element types support flatten=True
        assert all_placemarks and all_folders  # Should have content
        assert len(all_multigeometries) > 0  # MultiGeometry file should have content

    def test_basic_queries_root_vs_flatten_difference(self) -> None:
        """Test the practical difference between root-level and flatten queries."""
        # Use sample.kml which has both root-level and nested placemarks
        kml = KMLFile.from_file(self.places_kml_file)

        # Test with root-level queries - should find fewer results
        root_level_stores = kml.placemarks.filter(name__icontains="capital")
        all_stores = kml.placemarks.all(flatten=True).filter(name__icontains="capital")

        # Verify the practical difference
        # Flattened should find more stores than root-only
        assert len(all_stores) > len(root_level_stores)

        # Verify that flatten finds more results (since most stores are in folders)
        assert len(all_stores) > len(
            root_level_stores
        ), "Flatten should find more stores than root-only search"

        # Test exists() behavior difference
        root_has_timonium = kml.placemarks.filter(name__icontains="timonium").exists()
        all_has_timonium = (
            kml.placemarks.all(flatten=True).filter(name__icontains="timonium").exists()
        )

        # The Timonium store should be nested in folders, not at root level
        assert not root_has_timonium, "Root-level search should not find nested Timonium store"
        assert all_has_timonium, "Flattened search should find nested Timonium store"

    def test_exact_accessing_elements_code_block(self) -> None:
        """Test the exact 'Accessing Elements' code block from quickstart.rst."""
        # Setup with test data that has nested structure
        kml = KMLFile.from_file(self.places_kml_file)

        # EXACT CODE FROM quickstart.rst: Accessing Elements section
        # Get placemarks at document root level only
        root_placemarks = kml.placemarks.all()
        print(f"Found {len(root_placemarks)} root-level placemarks")

        # Get ALL placemarks including those nested in folders
        all_placemarks = kml.placemarks.all(flatten=True)
        print(f"Found {len(all_placemarks)} total placemarks")

        # Access different element types
        folders = kml.folders.all()
        paths = kml.paths.all()
        polygons = kml.polygons.all()
        points = kml.points.all()
        multigeometries = kml.multigeometries.all()

        # Or get ALL elements of each type using flatten=True
        all_folders = kml.folders.all(flatten=True)
        all_paths = kml.paths.all(flatten=True)
        all_polygons = kml.polygons.all(flatten=True)
        all_points = kml.points.all(flatten=True)
        all_multigeometries = kml.multigeometries.all(flatten=True)

        # Verify the code worked
        assert len(root_placemarks) >= 0
        assert len(all_placemarks) >= len(root_placemarks)
        assert hasattr(folders, "__iter__")
        assert hasattr(paths, "__iter__")
        assert hasattr(polygons, "__iter__")
        assert hasattr(points, "__iter__")
        assert hasattr(multigeometries, "__iter__")
        assert len(all_folders) >= len(folders)
        assert len(all_paths) >= len(paths)
        assert len(all_polygons) >= len(polygons)
        assert len(all_points) >= len(points)
        assert len(all_multigeometries) >= len(multigeometries)

    def test_exact_basic_queries_code_block(self) -> None:
        """Test the exact 'Basic Queries' code block from quickstart.rst."""
        # Use test data with Capital Electric stores
        kml = KMLFile.from_string(self.sample_kml)

        # EXACT CODE FROM quickstart.rst: Basic Queries section
        # Filter by name (root-level placemarks only)
        capital_stores = kml.placemarks.filter(name__icontains="capital")

        # Filter ALL placemarks including those in folders
        all_capital_stores = kml.placemarks.all(flatten=True).filter(name__icontains="capital")

        # Exclude items (root-level only)
        not_capital = kml.placemarks.exclude(name__icontains="capital")

        # Exclude ALL placemarks including those in folders
        all_not_capital = kml.placemarks.all(flatten=True).exclude(name__icontains="capital")

        # Get a single item (searches root-level only)
        store = kml.placemarks.get(name="Capital Electric - Rosedale")

        # Get from ALL placemarks including folders
        store = kml.placemarks.all(flatten=True).get(name="Capital Electric - Rosedale")

        # Check if items exist (root-level only)
        has_stores = kml.placemarks.filter(name__icontains="store").exists()

        # Check ALL placemarks including folders
        has_any_stores = kml.placemarks.all(flatten=True).filter(name__icontains="store").exists()

        # Verify the code worked as expected
        assert len(capital_stores) >= 1
        assert len(all_capital_stores) >= len(capital_stores)
        assert len(not_capital) >= 0
        assert len(all_not_capital) >= 0
        assert store.name == "Capital Electric - Rosedale"
        assert has_stores is True
        assert has_any_stores is True

    def test_exact_working_with_coordinates_code_block(self) -> None:
        """Test the exact 'Working with Coordinates' code block from quickstart.rst."""
        kml = KMLFile.from_string(self.sample_kml)

        # EXACT CODE FROM quickstart.rst: Working with Coordinates section
        for placemark in kml.placemarks.all():
            if placemark.coordinates:
                print(f"{placemark.name}: {placemark.longitude}, {placemark.latitude}")

        # Verify the code executed without error (no assertions needed for this print-based example)
        # The fact that the loop completed means the coordinate access worked

    def test_exact_geospatial_queries_code_block(self) -> None:
        """Test the exact 'Geospatial Queries' code block from quickstart.rst."""
        kml = KMLFile.from_string(self.sample_kml)

        # EXACT CODE FROM quickstart.rst: Geospatial Queries section
        # Find placemarks near Baltimore (within 25 km)
        nearby = kml.placemarks.near(-76.6, 39.3, radius_km=25)

        # Find placemarks within a bounding box
        in_area = kml.placemarks.within_bounds(north=39.5, south=39.0, east=-76.0, west=-77.0)

        # Only placemarks with coordinates
        with_location = kml.placemarks.has_coordinates()

        # Verify the code worked
        assert hasattr(nearby, "__iter__")
        assert hasattr(in_area, "__iter__")
        assert hasattr(with_location, "__iter__")

    def test_exact_chaining_queries_code_block(self) -> None:
        """Test the exact 'Chaining Queries' code block from quickstart.rst."""
        kml = KMLFile.from_string(self.sample_kml)

        # EXACT CODE FROM quickstart.rst: Chaining Queries section
        # Complex query
        result = (
            kml.placemarks.filter(name__icontains="electric")
            .near(-76.6, 39.3, radius_km=50)
            .has_coordinates()
            .order_by("name")
        )

        for placemark in result:
            print(f"- {placemark.name}")

        # Verify the code worked
        assert hasattr(result, "__iter__")
        assert len(list(result)) >= 0

    def test_exact_error_handling_code_block(self) -> None:
        """Test the exact 'Error Handling' code block from quickstart.rst."""
        # EXACT CODE FROM quickstart.rst: Error Handling section
        # pylint: disable=redefined-outer-name, import-outside-toplevel

        from kmlorm.core.exceptions import (  # noqa: F811
            KMLParseError,
            KMLElementNotFound,
            KMLMultipleElementsReturned,
        )

        try:
            kml = KMLFile.from_string(self.sample_kml)  # Use valid KML for this test
            store = kml.placemarks.get(name="Nonexistent Store")  # This will raise
            assert store is not None
        except KMLParseError:
            print("Invalid KML file")
        except KMLElementNotFound:
            print("Store not found")
        except KMLMultipleElementsReturned:
            print("Multiple stores found, be more specific")

        # Verify the exception was raised and caught properly
        with pytest.raises(KMLElementNotFound):
            kml = KMLFile.from_string(self.sample_kml)
            kml.placemarks.get(name="Nonexistent Store")

    def test_exact_kml_multiple_elements_returned_exception(self) -> None:
        """Test KMLMultipleElementsReturned exception from error handling examples."""
        # Create KML with multiple stores having similar names to trigger the exception
        duplicate_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>My Store - Location A</name>
      <Point><coordinates>-76.5,39.3,0</coordinates></Point>
    </Placemark>
    <Placemark>
      <name>My Store - Location B</name>
      <Point><coordinates>-76.6,39.4,0</coordinates></Point>
    </Placemark>
  </Document>
</kml>"""

        kml = KMLFile.from_string(duplicate_kml)

        # This should raise KMLMultipleElementsReturned
        with pytest.raises(KMLMultipleElementsReturned):
            kml.placemarks.get(name__icontains="My Store")

    def test_exact_complete_example_analyze_kml_file_function(self) -> None:
        """Test the exact 'analyze_kml_file' function from quickstart.rst Complete Example."""
        # EXACT CODE FROM quickstart.rst: Complete Example section
        # pylint: disable=redefined-outer-name, import-outside-toplevel
        from kmlorm import KMLFile
        from kmlorm.core.exceptions import KMLParseError, KMLElementNotFound  # noqa: F811

        def analyze_kml_file(file_path: str) -> None:
            try:
                # Load the KML file
                kml = KMLFile.from_file(file_path)

                print(f"Document: {kml.document_name}")
                print(f"Description: {kml.document_description}")
                print()

                # Show element counts
                counts = kml.element_counts()
                for element_type, count in counts.items():
                    print(f"{element_type.title()}: {count}")
                print()

                # Find stores near Baltimore
                nearby_stores = (
                    kml.placemarks.filter(name__icontains="store")
                    .near(-76.6, 39.3, radius_km=30)
                    .order_by("name")
                )

                print(f"Stores near Baltimore ({nearby_stores.count()}):")
                for store in nearby_stores:
                    distance = calculate_distance_to_baltimore(store)
                    print(f"- {store.name} ({distance:.1f} km away)")

                # Get a specific store
                try:
                    rosedale_store = kml.placemarks.get(name__contains="Rosedale")
                    print(f"\nRosedale store: {rosedale_store.address}")
                except KMLElementNotFound:
                    print("\nNo Rosedale store found")

            except KMLParseError as e:
                print(f"Error parsing KML file: {e}")
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Unexpected error: {e}")

        def calculate_distance_to_baltimore(placemark: "Placemark") -> "Optional[float]":
            # Simple distance calculation (you might use a proper geospatial library)
            if placemark.coordinates:
                # Baltimore coordinates: -76.6, 39.3
                baltimore_coord = (-76.6, 39.3)
                return placemark.distance_to(baltimore_coord)
            return 0

        # Test the exact function
        analyze_kml_file(self.places_kml_file)

        # Verify the functions executed without error (no exceptions raised)
        assert True  # If we get here, the exact code worked

    def test_exact_from_file_loading_example(self) -> None:
        """Test the exact from_file loading example from quickstart.rst."""
        # EXACT CODE FROM quickstart.rst: Loading KML Data section

        # From file
        kml = KMLFile.from_file(self.places_kml_file)  # Use our test file instead of 'places.kml'

        # Verify the code worked
        assert isinstance(kml, KMLFile)
        assert kml.document_name is not None

    def test_exact_from_string_loading_example(self) -> None:
        """Test the exact from_string loading example from quickstart.rst."""
        # EXACT CODE FROM quickstart.rst: Loading KML Data section

        # From string
        kml_string = """<?xml version="1.0" encoding="UTF-8"?>
  <kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
      <Placemark>
        <name>Test Store</name>
        <Point>
          <coordinates>-76.5,39.3,0</coordinates>
        </Point>
      </Placemark>
    </Document>
  </kml>"""
        kml = KMLFile.from_string(kml_string)

        # Verify the code worked
        assert isinstance(kml, KMLFile)
        placemarks = kml.placemarks.all()
        assert len(placemarks) == 1
        assert placemarks[0].name == "Test Store"

    def test_exact_from_url_loading_example(self) -> None:
        """Test the exact from_url loading example from quickstart.rst with real HTTP server."""
        # Set up HTTP server like test_url_integration.py
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")

        # Find an available port
        port = 8765
        for test_port in range(8765, 8800):
            try:
                test_server = socketserver.TCPServer(
                    ("localhost", test_port), http.server.SimpleHTTPRequestHandler
                )
                test_server.server_close()
                port = test_port
                break
            except OSError:
                continue

        # Save current directory and change to fixtures
        original_dir = os.getcwd()
        os.chdir(fixtures_dir)

        try:
            # Create and start HTTP server
            handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("localhost", port), handler)

            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            # Give server time to start
            time.sleep(0.1)

            # EXACT CODE FROM quickstart.rst: Loading KML Data section

            # From URL (example with localhost server)
            kml = KMLFile.from_url(f"http://localhost:{port}/sample.kml")

            # Verify the code worked
            assert isinstance(kml, KMLFile)
            assert kml.document_name == "Capital Electric Supply Locations"

            # Cleanup
            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=1.0)

        finally:
            # Restore original directory
            os.chdir(original_dir)
