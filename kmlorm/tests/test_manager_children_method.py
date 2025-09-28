"""
Tests for the new .children() method on KMLManager.

This test module validates the implementation of the .children() method
added as part of the Manager API Enhancement (Phase 1).

The .children() method should return only direct child elements,
providing the same behavior as the current .all() method without flatten=True.
"""

# pylint: disable=duplicate-code

import pytest
from kmlorm import KMLFile


class TestManagerChildrenMethod:
    """Test suite for the new .children() method functionality."""

    kml: KMLFile

    @pytest.fixture(autouse=True)
    def setup_kml(self, nested_kml_content: str) -> None:
        """Set up test data using shared fixture."""
        self.kml = KMLFile.from_string(nested_kml_content)

    def test_children_method_exists(self) -> None:
        """Test that the .children() method exists on managers."""
        assert hasattr(self.kml.placemarks, "children") is True
        assert hasattr(self.kml.folders, "children") is True
        assert callable(self.kml.placemarks.children) is True
        assert callable(self.kml.folders.children) is True

    def test_children_returns_direct_children_only(self) -> None:
        """Test that .children() returns only direct child placemarks."""
        children_placemarks = self.kml.placemarks.children()

        # Should return only the 2 root-level placemarks
        assert len(children_placemarks) == 2

        # Verify the names of the direct children
        names = {p.name for p in children_placemarks}
        expected_names = {"Root Placemark 1", "Root Placemark 2"}
        assert names == expected_names

    def test_children_vs_all_without_flatten(self) -> None:
        """Test that .children() differs from new .all() behavior."""
        children_result = self.kml.placemarks.children()
        all_result = self.kml.placemarks.all()  # New behavior includes nested elements

        # .all() should return more elements than .children() due to including nested
        assert len(all_result) >= len(children_result)
        assert len(children_result) == 2  # Direct children only
        assert len(all_result) == 5  # All elements including nested

        # Children should be a subset of all results
        children_names = {p.name for p in children_result}
        all_names = {p.name for p in all_result}
        assert children_names.issubset(all_names) is True

    def test_children_vs_all_with_flatten_true(self) -> None:
        """Test that .children() differs from .all()."""
        children_result = self.kml.placemarks.children()
        flattened_result = self.kml.placemarks.all()

        # children() should return fewer elements than flatten=True
        assert len(children_result) < len(flattened_result)

        # children() should return 2, flatten=True should return 5
        assert len(children_result) == 2
        assert len(flattened_result) == 5

    def test_children_works_with_folders(self) -> None:
        """Test that .children() works correctly with folder managers."""
        root_folders = self.kml.folders.children()

        # Should return 2 root-level folders
        assert len(root_folders) == 2

        folder_names = {f.name for f in root_folders}
        expected_names = {"Level 1 Folder", "Another Root Folder"}
        assert folder_names == expected_names

    def test_children_method_chainable(self) -> None:
        """Test that .children() returns a QuerySet that supports chaining."""
        # Test that we can chain filter operations
        filtered_children = self.kml.placemarks.children().filter(name__icontains="Root")

        # Should return 2 placemarks (both root placemarks contain "Root")
        assert len(filtered_children) == 2

        # Test that we can chain other QuerySet methods
        first_child = self.kml.placemarks.children().first()
        assert first_child is not None
        assert first_child is not None
        assert first_child.name is not None
        assert "Root Placemark" in str(first_child.name)

    def test_children_on_nested_folder_manager(self) -> None:
        """Test .children() method on nested folder's placemark manager."""
        # Get the first root folder
        level1_folder = self.kml.folders.children().filter(name="Level 1 Folder").first()
        assert level1_folder is not None

        # Get direct children of this folder
        assert level1_folder is not None
        assert level1_folder.placemarks is not None
        nested_children = level1_folder.placemarks.children()

        # Should return only 1 direct child placemark
        assert len(nested_children) == 1
        assert nested_children[0].name == "Nested Placemark 1"

        # Test that it doesn't include the deeply nested placemark
        child_names = {p.name for p in nested_children}
        assert "Deep Nested Placemark" not in child_names

    def test_children_empty_result(self) -> None:
        """Test .children() behavior when no direct children exist."""
        # Create KML with only nested placemarks, no root placemarks
        empty_root_kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Folder>
                    <name>Only Folder</name>
                    <Placemark>
                        <name>Only Nested Placemark</name>
                        <Point>
                            <coordinates>-122.0856545755255,37.42243077405461,0</coordinates>
                        </Point>
                    </Placemark>
                </Folder>
            </Document>
        </kml>"""

        kml = KMLFile.from_string(empty_root_kml)
        children_result = kml.placemarks.children()

        # Should return empty list for direct children
        assert len(children_result) == 0

        # But flatten=True should still find the nested placemark
        flattened_result = kml.placemarks.all()
        assert len(flattened_result) == 1

    def test_children_return_type(self) -> None:
        """Test that .children() returns the correct QuerySet type."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core.querysets import KMLQuerySet

        children_result = self.kml.placemarks.children()
        assert isinstance(children_result, KMLQuerySet)

        # Test that the QuerySet contains the expected element types
        for placemark in children_result:
            assert type(placemark).__name__ == "Placemark"

    def test_children_consistency_across_multiple_calls(self) -> None:
        """Test that .children() returns consistent results across multiple calls."""
        first_call = self.kml.placemarks.children()
        second_call = self.kml.placemarks.children()

        # Should return same number of elements
        assert len(first_call) == len(second_call)

        # Should return elements with same names
        first_names = {p.name for p in first_call}
        second_names = {p.name for p in second_call}
        assert first_names == second_names

    def test_children_with_mixed_element_types(self) -> None:
        """Test .children() behavior when document has mixed direct children."""
        # The test data has both placemarks and folders as direct children
        placemark_children = self.kml.placemarks.children()
        folder_children = self.kml.folders.children()

        # Each manager should only return its own element type
        assert len(placemark_children) == 2  # 2 root placemarks
        assert len(folder_children) == 2  # 2 root folders

        # Verify types
        for pm in placemark_children:
            assert type(pm).__name__ == "Placemark"
        for folder in folder_children:
            assert type(folder).__name__ == "Folder"
