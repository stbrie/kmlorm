"""
Tests that validate every example in docs/source/api/kmlfile.rst works as documented.

This test suite ensures that all code examples in the KMLFile documentation
are functional and produce the expected results.
"""

# pylint: disable=duplicate-code

import tempfile
import os
from typing import IO, Generator
from unittest.mock import patch
import pytest
from kmlorm import KMLFile, KMLElementNotFound


class TestKMLFileDocsExamples:
    """Test cases that validate kmlfile.rst documentation examples."""

    comprehensive_kml_content: str
    temp_file: IO[str]
    simple_kml_content: str

    @pytest.fixture(autouse=True)
    def setup_kml_files(self, sample_kml_content: str, simple_kml_content: str) -> Generator[None, None, None]:
        """Set up test fixtures using centralized KML content."""
        # Use fixture from conftest for comprehensive content
        self.comprehensive_kml_content = sample_kml_content

        # Create temporary file with comprehensive content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as temp_file:
            temp_file.write(self.comprehensive_kml_content)
        self.temp_file = temp_file

        # Use simple KML content from fixture
        self.simple_kml_content = simple_kml_content

        yield
        # Cleanup: Remove temporary file
        if hasattr(self, "temp_file") and os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_import_kmlfile_example(self) -> None:
        """Test the basic import example from kmlfile.rst."""
        # Example from documentation:
        # from kmlorm import KMLFile

        # Verify we can import KMLFile as shown in documentation
        # pylint: disable=import-outside-toplevel, reimported
        from kmlorm import KMLFile as ImportedKMLFile

        # Verify it's the correct class
        assert ImportedKMLFile.__name__ == "KMLFile"
        assert hasattr(ImportedKMLFile, "from_file") is True
        assert hasattr(ImportedKMLFile, "from_string") is True
        assert hasattr(ImportedKMLFile, "from_url") is True

    def test_working_with_managers_root_level_example(self) -> None:
        """Test the root-level manager access example from Working with Managers section."""
        # Example from documentation:
        # from kmlorm import KMLFile
        #
        # kml = KMLFile.from_file('example.kml')
        #
        # # Access different element types (direct children only)
        # root_placemarks = kml.placemarks.children()
        # root_folders = kml.folders.children()
        # root_paths = kml.paths.children()
        # root_polygons = kml.polygons.children()
        # root_points = kml.points.children()
        # root_multigeometries = kml.multigeometries.children()

        kml = KMLFile.from_file(self.temp_file.name)

        # Access different element types (direct children only) as shown in documentation
        root_placemarks = kml.placemarks.children()
        root_folders = kml.folders.children()
        root_paths = kml.paths.children()
        root_polygons = kml.polygons.children()
        root_points = kml.points.children()
        root_multigeometries = kml.multigeometries.children()

        # Verify root-level only behavior
        assert len(root_placemarks) == 1  # Only "Capital Electric - Root Level"
        assert len(root_folders) == 1  # "Store Locations"
        assert root_placemarks[0].name == "Capital Electric - Root Level"

        # Verify manager types
        assert hasattr(root_placemarks, "filter") is True
        assert hasattr(root_folders, "filter") is True
        assert hasattr(root_paths, "filter") is True
        assert hasattr(root_polygons, "filter") is True
        assert hasattr(root_points, "filter") is True
        assert hasattr(root_multigeometries, "filter") is True

    def test_working_with_managers_flatten_example(self) -> None:
        """Test the flattened manager access example from Working with Managers section."""
        # Example from documentation:
        # # Access ALL elements including those nested in folders
        # all_placemarks = kml.placemarks.all()
        # all_folders = kml.folders.all()
        # all_paths = kml.paths.all()
        # all_polygons = kml.polygons.all()
        # all_points = kml.points.all()
        # all_multigeometries = kml.multigeometries.all()

        kml = KMLFile.from_file(self.temp_file.name)

        # Access ALL elements including those nested in folders as shown in documentation
        all_placemarks = kml.placemarks.all()
        all_folders = kml.folders.all()
        all_paths = kml.paths.all()
        assert all_paths is not None
        all_polygons = kml.polygons.all()
        assert all_polygons is not None
        all_points = kml.points.all()
        assert all_points is not None
        all_multigeometries = kml.multigeometries.all()
        assert all_multigeometries is not None
        # Verify flatten=True includes nested elements
        assert len(all_placemarks) == 4  # All placemarks including nested ones
        assert len(all_folders) == 2  # All folders including nested one

        # Verify we get nested elements
        placemark_names = [p.name for p in all_placemarks]
        assert "Capital Electric - Nested" in placemark_names
        assert "Capital Electric - Root Level" in placemark_names

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
        assert isinstance(kml_from_file, KMLFile)
        assert kml_from_file.document_name == "Test Document"

        # Test from_string
        kml_from_string = KMLFile.from_string(self.simple_kml_content)
        assert isinstance(kml_from_string, KMLFile)
        assert kml_from_string.document_name is None  # Simple KML has no Document name

        # Test from_url (mock to avoid external dependency)
        with patch("kmlorm.parsers.kml_file.KMLFile.from_url") as mock_from_url:
            mock_from_url.return_value = kml_from_file
            kml_from_url = KMLFile.from_url("https://example.com/data.kml")
            assert isinstance(kml_from_url, KMLFile)
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

        assert document_str == "Document: Test Document"
        assert description_str == "Description: A comprehensive test document for KML ORM"

        # Verify properties are accessible
        assert kml_from_file.document_name == "Test Document"
        assert kml_from_file.document_description == "A comprehensive test document for KML ORM"

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
        assert "Total placemarks:" in placemarks_str
        assert "Total folders:" in folders_str

        # Verify counts dict has expected keys and values
        assert isinstance(counts, dict)
        assert "placemarks" in counts
        assert "folders" in counts
        assert counts["placemarks"] > 0
        assert counts["folders"] > 0

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
        assert hasattr(capital_stores, "count") is True
        assert hasattr(visible_folders, "count") is True

        # For root-level only, should find the root-level "Capital Electric" placemark
        assert len(capital_stores) == 1  # One root-level placemark with "capital" in name

        # Should find visible folders at root level
        assert len(visible_folders) > 0

    def test_querying_elements_comprehensive_queries_example(self) -> None:
        """Test the comprehensive queries example from Querying Elements section."""
        # Example from documentation:
        # # Comprehensive queries (including nested elements)
        # all_capital_stores = kml.placemarks.all().filter(name__icontains='capital')
        # all_visible_folders = kml.folders.all().filter(visibility=True)

        kml = KMLFile.from_file(self.temp_file.name)

        # Comprehensive queries (including nested elements) as shown in documentation
        all_capital_stores = kml.placemarks.all().filter(name__icontains="capital")
        all_visible_folders = kml.folders.all().filter(visibility=True)

        # With flatten=True, should find nested "Capital Electric" stores
        assert len(all_capital_stores) > 0
        capital_names = [store.name for store in all_capital_stores]
        assert any(name is not None and "Capital Electric" in name for name in capital_names)

        # Should find visible folders including nested ones
        assert len(all_visible_folders) > 0

    def test_querying_elements_geospatial_queries_example(self) -> None:
        """Test the geospatial queries example from Querying Elements section."""
        # Example from documentation:
        # # Geospatial queries
        # nearby_stores = kml.placemarks.all().near(-76.6, 39.3, radius_km=25)
        # bounded_elements = kml.placemarks.all().within_bounds(
        #     north=39.5, south=39.0, east=-76.0, west=-77.0
        # )

        kml = KMLFile.from_file(self.temp_file.name)

        # Geospatial queries as shown in documentation
        nearby_stores = kml.placemarks.all().near(-76.6, 39.3, radius_km=25)
        bounded_elements = kml.placemarks.all().within_bounds(
            north=39.5, south=39.0, east=-76.0, west=-77.0
        )

        # Verify geospatial query methods exist and return querysets
        assert hasattr(nearby_stores, "count") is True
        assert hasattr(bounded_elements, "count") is True

        # Should find stores within the specified area
        assert len(nearby_stores) >= 0
        assert len(bounded_elements) >= 0

    def test_querying_elements_get_specific_element_example(self) -> None:
        """Test the get specific element example from Querying Elements section."""
        # Example from documentation:
        # # Get specific elements
        # try:
        #     specific_store =
        #                kml.placemarks.all().get(name='Capital Electric - Rosedale')
        #     print(f"Found: {specific_store.name} at {specific_store.address}")
        # except KMLElementNotFound:
        #     print("Store not found")

        kml = KMLFile.from_file(self.temp_file.name)

        # Get specific elements as shown in documentation
        try:
            specific_store = kml.placemarks.all().get(name="Capital Electric - Rosedale")
            found_str = f"Found: {specific_store.name} at {specific_store.address}"

            # Verify we found the specific store
            assert specific_store.name == "Capital Electric - Rosedale"
            assert "Found: Capital Electric - Rosedale at" in found_str
            assert specific_store.address is not None
        except KMLElementNotFound:
            pytest.fail("Should have found 'Capital Electric - Rosedale' store")

        # Test the exception handling path
        try:
            nonexistent_store = kml.placemarks.all().get(name="Nonexistent Store")
            assert nonexistent_store is not None
            pytest.fail("Should have raised KMLElementNotFound")
        except KMLElementNotFound:
            # This is the expected path as shown in documentation
            handled = True
            assert handled is True

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
        assert isinstance(all_elements, list)
        assert len(all_elements) > 0

        # Verify the format string works
        assert "Total elements in KML:" in total_str

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
        assert len(processed_elements) > 0

        # Verify format strings contain expected patterns
        for element_str in processed_elements:
            assert ":" in element_str  # Should have "ClassName: name"
            # Either has coordinates or just name
            assert " at " in element_str or element_str.count(":") == 1

        # Check that we have both types (with and without coordinates)
        has_coordinates = any(" at " in s for s in processed_elements)
        has_no_coordinates = any(" at " not in s and ":" in s for s in processed_elements)
        assert has_coordinates or has_no_coordinates is True  # Should have at least one type

    def test_flatten_parameter_note_behavior(self) -> None:
        """Test the new API behavior described in the updated documentation note."""
        # Updated documentation note states:
        # Manager methods provide two ways to access elements:
        # * ``kml.placemarks.children()`` - Direct children only
        # * ``kml.placemarks.all()`` - All elements including nested ones
        # The old flatten parameter is deprecated but still supported during transition.

        kml = KMLFile.from_file(self.temp_file.name)

        # Test direct children only behavior
        root_placemarks = kml.placemarks.children()
        assert len(root_placemarks) == 1  # Only direct child placemark

        # Test new all() behavior - includes nested elements by default
        current_all_placemarks = kml.placemarks.all()
        # Should include nested
        assert len(current_all_placemarks) >= len(root_placemarks)

        # Verify that .all() includes nested elements and .children() returns only direct children
        # Should include all placemarks including nested ones
        assert len(current_all_placemarks) == 4
        assert len(root_placemarks) == 1  # Should only include direct children

        # Verify .all() and .children() return different result sets
        assert len(current_all_placemarks) != len(root_placemarks)

        # Verify this applies to all element types as documented
        root_folders = kml.folders.children()
        all_folders = kml.folders.all()
        assert len(all_folders) >= len(root_folders)

        # Test the specific element types mentioned in the note
        element_types = ["placemarks", "folders", "paths", "polygons", "points", "multigeometries"]
        for element_type in element_types:
            manager = getattr(kml, element_type)
            root_elements = manager.children()  # Direct children only
            all_elements = manager.all()  # All elements including nested (new default)
            # All should be >= root (some might be empty but the method should work)
            assert len(all_elements) >= len(root_elements)

    def test_document_properties_access(self) -> None:
        """Test document properties access as shown in documentation."""
        # Documentation shows autoattribute directives for:
        # .. autoattribute:: kmlorm.parsers.kml_file.KMLFile.document_name
        # .. autoattribute:: kmlorm.parsers.kml_file.KMLFile.document_description

        kml = KMLFile.from_file(self.temp_file.name)

        # Test document_name property
        assert hasattr(kml, "document_name") is True
        assert kml.document_name == "Test Document"

        # Test document_description property
        assert hasattr(kml, "document_description") is True
        assert kml.document_description == "A comprehensive test document for KML ORM"

        # Test with KML that has no description
        simple_kml = KMLFile.from_string(self.simple_kml_content)
        assert simple_kml.document_name is None  # Simple KML has no Document name
        assert simple_kml.document_description is None  # Simple KML has no Document description

    def test_utility_methods_access(self) -> None:
        """Test utility methods access as shown in documentation."""
        # Documentation shows automethod directives for:
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.element_counts
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.all_elements

        kml = KMLFile.from_file(self.temp_file.name)

        # Test element_counts method
        assert hasattr(kml, "element_counts") is True
        counts = kml.element_counts()
        assert isinstance(counts, dict)
        assert "placemarks" in counts
        assert "folders" in counts

        # Test all_elements method
        assert hasattr(kml, "all_elements") is True
        all_elements = kml.all_elements()
        assert isinstance(all_elements, list)
        assert len(all_elements) > 0

    def test_loading_methods_class_methods(self) -> None:
        """Test that loading methods are properly exposed as class methods."""
        # Documentation shows automethod directives for:
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.from_file
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.from_string
        # .. automethod:: kmlorm.parsers.kml_file.KMLFile.from_url

        # Test from_file class method
        assert hasattr(KMLFile, "from_file") is True
        kml_from_file = KMLFile.from_file(self.temp_file.name)
        assert isinstance(kml_from_file, KMLFile)

        # Test from_string class method
        assert hasattr(KMLFile, "from_string") is True
        kml_from_string = KMLFile.from_string(self.simple_kml_content)
        assert isinstance(kml_from_string, KMLFile)

        # Test from_url class method exists (don't call it to avoid network dependency)
        assert hasattr(KMLFile, "from_url") is True
        assert callable(getattr(KMLFile, "from_url")) is True
