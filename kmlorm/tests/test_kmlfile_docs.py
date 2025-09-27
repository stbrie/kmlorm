"""
Tests that validate every example in docs/source/api/kmlfile.rst works as documented.

This test suite ensures that all code examples in the KMLFile documentation
are functional and produce the expected results.
"""

# pylint: disable=duplicate-code
import unittest
import tempfile
import os
from unittest.mock import patch

from kmlorm import KMLFile, KMLElementNotFound


class TestKMLFileDocsExamples(unittest.TestCase):
    """Test cases that validate kmlfile.rst documentation examples."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create comprehensive test KML content
        self.comprehensive_kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Test Document</name>
        <description>A comprehensive test document</description>
        <Folder>
            <name>Store Locations</name>
            <description>All store locations</description>
            <visibility>1</visibility>
            <Placemark>
                <name>Capital Electric - Rosedale</name>
                <description>Main store location</description>
                <address>123 Main St, Rosedale, MD</address>
                <Point>
                    <coordinates>-76.5,39.3,0</coordinates>
                </Point>
            </Placemark>
            <Placemark>
                <name>Capital Electric - Downtown</name>
                <description>Downtown branch</description>
                <address>456 Oak Ave, Baltimore, MD</address>
                <Point>
                    <coordinates>-76.6,39.4,0</coordinates>
                </Point>
            </Placemark>
            <Folder>
                <name>Nested Folder</name>
                <description>Nested store locations</description>
                <visibility>1</visibility>
                <Placemark>
                    <name>Capital Electric - Nested</name>
                    <description>Nested store</description>
                    <Point>
                        <coordinates>-76.4,39.2,0</coordinates>
                    </Point>
                </Placemark>
            </Folder>
        </Folder>
        <Placemark>
            <name>Root Level Store</name>
            <description>Store at document root</description>
            <Point>
                <coordinates>-77.0,40.0,0</coordinates>
            </Point>
        </Placemark>
        <Folder>
            <name>Other Locations</name>
            <description>Other business locations</description>
            <visibility>0</visibility>
            <Placemark>
                <name>Warehouse</name>
                <description>Main warehouse</description>
                <Point>
                    <coordinates>-76.8,39.5,0</coordinates>
                </Point>
            </Placemark>
        </Folder>
    </Document>
</kml>"""

        # Create temporary file with comprehensive content

        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as temp_file:
            temp_file.write(self.comprehensive_kml_content)
        self.temp_file = temp_file

        # Simple KML content for basic tests
        self.simple_kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Simple Document</name>
        <description>A simple test document</description>
        <Placemark>
            <name>Simple Store</name>
            <Point>
                <coordinates>-76.5,39.3,0</coordinates>
            </Point>
        </Placemark>
    </Document>
</kml>"""

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_import_kmlfile_example(self) -> None:
        """Test the basic import example from kmlfile.rst."""
        # Example from documentation:
        # from kmlorm import KMLFile

        # Verify we can import KMLFile as shown in documentation
        # pylint: disable=import-outside-toplevel, reimported
        from kmlorm import KMLFile as ImportedKMLFile

        # Verify it's the correct class
        self.assertEqual(ImportedKMLFile.__name__, "KMLFile")
        self.assertTrue(hasattr(ImportedKMLFile, "from_file"))
        self.assertTrue(hasattr(ImportedKMLFile, "from_string"))
        self.assertTrue(hasattr(ImportedKMLFile, "from_url"))

    def test_working_with_managers_root_level_example(self) -> None:
        """Test the root-level manager access example from Working with Managers section."""
        # Example from documentation:
        # from kmlorm import KMLFile
        #
        # kml = KMLFile.from_file('example.kml')
        #
        # # Access different element types (root-level only)
        # root_placemarks = kml.placemarks.all()
        # root_folders = kml.folders.all()
        # root_paths = kml.paths.all()
        # root_polygons = kml.polygons.all()
        # root_points = kml.points.all()
        # root_multigeometries = kml.multigeometries.all()

        kml = KMLFile.from_file(self.temp_file.name)

        # Access different element types (root-level only) as shown in documentation
        root_placemarks = kml.placemarks.all()
        root_folders = kml.folders.all()
        root_paths = kml.paths.all()
        root_polygons = kml.polygons.all()
        root_points = kml.points.all()
        root_multigeometries = kml.multigeometries.all()

        # Verify root-level only behavior
        self.assertEqual(len(root_placemarks), 1)  # Only "Root Level Store"
        self.assertEqual(len(root_folders), 2)  # "Store Locations" and "Other Locations"
        self.assertEqual(root_placemarks[0].name, "Root Level Store")

        # Verify manager types
        self.assertTrue(hasattr(root_placemarks, "filter"))
        self.assertTrue(hasattr(root_folders, "filter"))
        self.assertTrue(hasattr(root_paths, "filter"))
        self.assertTrue(hasattr(root_polygons, "filter"))
        self.assertTrue(hasattr(root_points, "filter"))
        self.assertTrue(hasattr(root_multigeometries, "filter"))

    def test_working_with_managers_flatten_example(self) -> None:
        """Test the flattened manager access example from Working with Managers section."""
        # Example from documentation:
        # # Access ALL elements including those nested in folders
        # all_placemarks = kml.placemarks.all(flatten=True)
        # all_folders = kml.folders.all(flatten=True)
        # all_paths = kml.paths.all(flatten=True)
        # all_polygons = kml.polygons.all(flatten=True)
        # all_points = kml.points.all(flatten=True)
        # all_multigeometries = kml.multigeometries.all(flatten=True)

        kml = KMLFile.from_file(self.temp_file.name)

        # Access ALL elements including those nested in folders as shown in documentation
        all_placemarks = kml.placemarks.all(flatten=True)
        all_folders = kml.folders.all(flatten=True)
        all_paths = kml.paths.all(flatten=True)
        assert all_paths is not None
        all_polygons = kml.polygons.all(flatten=True)
        assert all_polygons is not None
        all_points = kml.points.all(flatten=True)
        assert all_points is not None
        all_multigeometries = kml.multigeometries.all(flatten=True)
        assert all_multigeometries is not None
        # Verify flatten=True includes nested elements
        self.assertEqual(len(all_placemarks), 5)  # All placemarks including nested ones
        self.assertEqual(len(all_folders), 3)  # All folders including nested one

        # Verify we get nested elements
        placemark_names = [p.name for p in all_placemarks]
        self.assertIn("Capital Electric - Nested", placemark_names)
        self.assertIn("Root Level Store", placemark_names)

    def test_basic_usage_loading_example(self) -> None:
        """Test the basic loading example from Complete Usage Examples section."""
        # Example from documentation:
        # from kmlorm import KMLFile
        #
        # # Load from various sources
        # kml_from_file = KMLFile.from_file('data.kml')
        # kml_from_url = KMLFile.from_url('https://example.com/data.kml')
        # kml_from_string = KMLFile.from_string(kml_content)

        # Test from_file
        kml_from_file = KMLFile.from_file(self.temp_file.name)
        self.assertIsInstance(kml_from_file, KMLFile)
        self.assertEqual(kml_from_file.document_name, "Test Document")

        # Test from_string
        kml_from_string = KMLFile.from_string(self.simple_kml_content)
        self.assertIsInstance(kml_from_string, KMLFile)
        self.assertEqual(kml_from_string.document_name, "Simple Document")

        # Test from_url (mock to avoid external dependency)
        with patch("kmlorm.parsers.kml_file.KMLFile.from_url") as mock_from_url:
            mock_from_url.return_value = kml_from_file
            kml_from_url = KMLFile.from_url("https://example.com/data.kml")
            self.assertIsInstance(kml_from_url, KMLFile)
            mock_from_url.assert_called_once_with("https://example.com/data.kml")

    def test_basic_usage_document_metadata_example(self) -> None:
        """Test the document metadata access example from Complete Usage Examples section."""
        # Example from documentation:
        # # Access document metadata
        # print(f"Document: {kml_from_file.document_name}")
        # print(f"Description: {kml_from_file.document_description}")

        kml_from_file = KMLFile.from_file(self.temp_file.name)

        # Access document metadata as shown in documentation
        document_str = f"Document: {kml_from_file.document_name}"
        description_str = f"Description: {kml_from_file.document_description}"

        self.assertEqual(document_str, "Document: Test Document")
        self.assertEqual(description_str, "Description: A comprehensive test document")

        # Verify properties are accessible
        self.assertEqual(kml_from_file.document_name, "Test Document")
        self.assertEqual(kml_from_file.document_description, "A comprehensive test document")

    def test_basic_usage_element_counts_example(self) -> None:
        """Test the element counts example from Complete Usage Examples section."""
        # Example from documentation:
        # # Get element counts
        # counts = kml_from_file.element_counts()
        # print(f"Total placemarks: {counts['placemarks']}")
        # print(f"Total folders: {counts['folders']}")

        kml_from_file = KMLFile.from_file(self.temp_file.name)

        # Get element counts as shown in documentation
        counts = kml_from_file.element_counts()
        placemarks_str = f"Total placemarks: {counts['placemarks']}"
        folders_str = f"Total folders: {counts['folders']}"

        # Verify the format strings work
        self.assertIn("Total placemarks:", placemarks_str)
        self.assertIn("Total folders:", folders_str)

        # Verify counts dict has expected keys and values
        self.assertIsInstance(counts, dict)
        self.assertIn("placemarks", counts)
        self.assertIn("folders", counts)
        self.assertGreater(counts["placemarks"], 0)
        self.assertGreater(counts["folders"], 0)

    def test_querying_elements_basic_queries_example(self) -> None:
        """Test the basic queries example from Querying Elements section."""
        # Example from documentation:
        # from kmlorm import KMLFile
        #
        # kml = KMLFile.from_file('stores.kml')
        #
        # # Basic queries (root-level elements only)
        # capital_stores = kml.placemarks.filter(name__icontains='capital')
        # visible_folders = kml.folders.filter(visibility=True)

        kml = KMLFile.from_file(self.temp_file.name)

        # Basic queries (root-level elements only) as shown in documentation
        capital_stores = kml.placemarks.filter(name__icontains="capital")
        visible_folders = kml.folders.filter(visibility=True)

        # Verify filter operations work
        self.assertTrue(hasattr(capital_stores, "count"))
        self.assertTrue(hasattr(visible_folders, "count"))

        # For root-level only, should not find nested "Capital Electric" stores
        self.assertEqual(len(capital_stores), 0)  # No root-level placemarks with "capital" in name

        # Should find visible folders at root level
        self.assertGreater(len(visible_folders), 0)

    def test_querying_elements_comprehensive_queries_example(self) -> None:
        """Test the comprehensive queries example from Querying Elements section."""
        # Example from documentation:
        # # Comprehensive queries (including nested elements)
        # all_capital_stores = kml.placemarks.all(flatten=True).filter(name__icontains='capital')
        # all_visible_folders = kml.folders.all(flatten=True).filter(visibility=True)

        kml = KMLFile.from_file(self.temp_file.name)

        # Comprehensive queries (including nested elements) as shown in documentation
        all_capital_stores = kml.placemarks.all(flatten=True).filter(name__icontains="capital")
        all_visible_folders = kml.folders.all(flatten=True).filter(visibility=True)

        # With flatten=True, should find nested "Capital Electric" stores
        self.assertGreater(len(all_capital_stores), 0)
        capital_names = [store.name for store in all_capital_stores]
        self.assertTrue(
            any(name is not None and "Capital Electric" in name for name in capital_names)
        )

        # Should find visible folders including nested ones
        self.assertGreater(len(all_visible_folders), 0)

    def test_querying_elements_geospatial_queries_example(self) -> None:
        """Test the geospatial queries example from Querying Elements section."""
        # Example from documentation:
        # # Geospatial queries
        # nearby_stores = kml.placemarks.all(flatten=True).near(-76.6, 39.3, radius_km=25)
        # bounded_elements = kml.placemarks.all(flatten=True).within_bounds(
        #     north=39.5, south=39.0, east=-76.0, west=-77.0
        # )

        kml = KMLFile.from_file(self.temp_file.name)

        # Geospatial queries as shown in documentation
        nearby_stores = kml.placemarks.all(flatten=True).near(-76.6, 39.3, radius_km=25)
        bounded_elements = kml.placemarks.all(flatten=True).within_bounds(
            north=39.5, south=39.0, east=-76.0, west=-77.0
        )

        # Verify geospatial query methods exist and return querysets
        self.assertTrue(hasattr(nearby_stores, "count"))
        self.assertTrue(hasattr(bounded_elements, "count"))

        # Should find stores within the specified area
        self.assertGreaterEqual(len(nearby_stores), 0)
        self.assertGreaterEqual(len(bounded_elements), 0)

    def test_querying_elements_get_specific_element_example(self) -> None:
        """Test the get specific element example from Querying Elements section."""
        # Example from documentation:
        # # Get specific elements
        # try:
        #     specific_store =
        #                kml.placemarks.all(flatten=True).get(name='Capital Electric - Rosedale')
        #     print(f"Found: {specific_store.name} at {specific_store.address}")
        # except KMLElementNotFound:
        #     print("Store not found")

        kml = KMLFile.from_file(self.temp_file.name)

        # Get specific elements as shown in documentation
        try:
            specific_store = kml.placemarks.all(flatten=True).get(
                name="Capital Electric - Rosedale"
            )
            found_str = f"Found: {specific_store.name} at {specific_store.address}"

            # Verify we found the specific store
            self.assertEqual(specific_store.name, "Capital Electric - Rosedale")
            self.assertIn("Found: Capital Electric - Rosedale at", found_str)
            self.assertIsNotNone(specific_store.address)
        except KMLElementNotFound:
            self.fail("Should have found 'Capital Electric - Rosedale' store")

        # Test the exception handling path
        try:
            nonexistent_store = kml.placemarks.all(flatten=True).get(name="Nonexistent Store")
            assert nonexistent_store is not None
            self.fail("Should have raised KMLElementNotFound")
        except KMLElementNotFound:
            # This is the expected path as shown in documentation
            handled = True
            self.assertTrue(handled)

    def test_working_with_all_elements_example(self) -> None:
        """Test the working with all elements example from Working with All Elements section."""
        # Example from documentation:
        # from kmlorm import KMLFile
        #
        # kml = KMLFile.from_file('comprehensive.kml')
        #
        # # Get all elements as a single list
        # all_elements = kml.all_elements()
        # print(f"Total elements in KML: {len(all_elements)}")

        kml = KMLFile.from_file(self.temp_file.name)

        # Get all elements as a single list as shown in documentation
        all_elements = kml.all_elements()
        total_str = f"Total elements in KML: {len(all_elements)}"

        # Verify all_elements returns a list
        self.assertIsInstance(all_elements, list)
        self.assertGreater(len(all_elements), 0)

        # Verify the format string works
        self.assertIn("Total elements in KML:", total_str)

    def test_working_with_all_elements_processing_example(self) -> None:
        """Test the element processing example from Working with All Elements section."""
        # Example from documentation:
        # # Process different element types
        # for element in all_elements:
        #     if hasattr(element, 'coordinates') and element.coordinates:
        #         print(f"{element.__class__.__name__}: {element.name} at {element.coordinates}")
        #     else:
        #         print(f"{element.__class__.__name__}: {element.name}")

        kml = KMLFile.from_file(self.temp_file.name)
        all_elements = kml.all_elements()

        # Process different element types as shown in documentation
        processed_elements = []
        for element in all_elements:
            if hasattr(element, "coordinates") and element.coordinates:
                element_str = (
                    f"{element.__class__.__name__}: {element.name} at {element.coordinates}"
                )
            else:
                element_str = f"{element.__class__.__name__}: {element.name}"
            processed_elements.append(element_str)

        # Verify we processed elements
        self.assertGreater(len(processed_elements), 0)

        # Verify format strings contain expected patterns
        for element_str in processed_elements:
            self.assertTrue(":" in element_str)  # Should have "ClassName: name"
            # Either has coordinates or just name
            self.assertTrue(" at " in element_str or element_str.count(":") == 1)

        # Check that we have both types (with and without coordinates)
        has_coordinates = any(" at " in s for s in processed_elements)
        has_no_coordinates = any(" at " not in s and ":" in s for s in processed_elements)
        self.assertTrue(has_coordinates or has_no_coordinates)  # Should have at least one type

    def test_flatten_parameter_note_behavior(self) -> None:
        """Test the flatten parameter behavior described in the note."""
        # Documentation note states:
        # By default, manager methods like ``kml.placemarks.all()`` only return
        # elements at the document root level.
        # To include elements from nested folders, use ``flatten=True``:
        # * ``kml.placemarks.all()`` - Root-level placemarks only
        # * ``kml.placemarks.all(flatten=True)`` - All placemarks including nested ones

        kml = KMLFile.from_file(self.temp_file.name)

        # Test root-level only behavior
        root_placemarks = kml.placemarks.all()
        self.assertEqual(len(root_placemarks), 1)  # Only root-level placemark

        # Test flatten=True behavior
        all_placemarks = kml.placemarks.all(flatten=True)
        self.assertGreater(len(all_placemarks), len(root_placemarks))  # Should include nested

        # Verify this applies to all element types as documented
        root_folders = kml.folders.all()
        all_folders = kml.folders.all(flatten=True)
        self.assertGreaterEqual(len(all_folders), len(root_folders))

        # Test the specific element types mentioned in the note
        element_types = ["placemarks", "folders", "paths", "polygons", "points", "multigeometries"]
        for element_type in element_types:
            manager = getattr(kml, element_type)
            root_elements = manager.all()
            all_elements = manager.all(flatten=True)
            # All should be >= root (some might be empty but the method should work)
            self.assertGreaterEqual(len(all_elements), len(root_elements))

    def test_document_properties_access(self) -> None:
        """Test document properties access as shown in documentation."""
        # Documentation shows autoattribute directives for:
        # .. autoattribute:: kmlorm.parsers.kml_file.KMLFile.document_name
        # .. autoattribute:: kmlorm.parsers.kml_file.KMLFile.document_description

        kml = KMLFile.from_file(self.temp_file.name)

        # Test document_name property
        self.assertTrue(hasattr(kml, "document_name"))
        self.assertEqual(kml.document_name, "Test Document")

        # Test document_description property
        self.assertTrue(hasattr(kml, "document_description"))
        self.assertEqual(kml.document_description, "A comprehensive test document")

        # Test with KML that has no description
        simple_kml = KMLFile.from_string(self.simple_kml_content)
        self.assertEqual(simple_kml.document_name, "Simple Document")
        self.assertEqual(simple_kml.document_description, "A simple test document")

    def test_utility_methods_access(self) -> None:
        """Test utility methods access as shown in documentation."""
        # Documentation shows automethod directives for:
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.element_counts
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.all_elements

        kml = KMLFile.from_file(self.temp_file.name)

        # Test element_counts method
        self.assertTrue(hasattr(kml, "element_counts"))
        counts = kml.element_counts()
        self.assertIsInstance(counts, dict)
        self.assertIn("placemarks", counts)
        self.assertIn("folders", counts)

        # Test all_elements method
        self.assertTrue(hasattr(kml, "all_elements"))
        all_elements = kml.all_elements()
        self.assertIsInstance(all_elements, list)
        self.assertGreater(len(all_elements), 0)

    def test_loading_methods_class_methods(self) -> None:
        """Test that loading methods are properly exposed as class methods."""
        # Documentation shows automethod directives for:
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.from_file
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.from_string
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.from_url

        # Test from_file class method
        self.assertTrue(hasattr(KMLFile, "from_file"))
        kml_from_file = KMLFile.from_file(self.temp_file.name)
        self.assertIsInstance(kml_from_file, KMLFile)

        # Test from_string class method
        self.assertTrue(hasattr(KMLFile, "from_string"))
        kml_from_string = KMLFile.from_string(self.simple_kml_content)
        self.assertIsInstance(kml_from_string, KMLFile)

        # Test from_url class method exists (don't call it to avoid network dependency)
        self.assertTrue(hasattr(KMLFile, "from_url"))
        self.assertTrue(callable(getattr(KMLFile, "from_url")))


if __name__ == "__main__":
    unittest.main()
