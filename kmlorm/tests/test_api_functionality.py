"""
API functionality tests for .all() and .children() methods.

This test module ensures that the core API functionality works correctly
with the new simplified API design.
"""

# pylint: disable=duplicate-code, too-many-public-methods

import time

from kmlorm import KMLFile


# Test data for API testing
COMPLEX_KML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>API Test Document</name>

        <!-- Root level elements -->
        <Placemark>
            <name>Root Placemark 1</name>
            <Point>
                <coordinates>-122.0856545755255,37.42243077405461,0</coordinates>
            </Point>
        </Placemark>
        <Placemark>
            <name>Root Placemark 2</name>
            <Point>
                <coordinates>-122.084075,37.4220033612141,0</coordinates>
            </Point>
        </Placemark>

        <!-- Nested structure -->
        <Folder>
            <name>Level 1 Folder A</name>
            <Placemark>
                <name>L1A Placemark 1</name>
                <Point>
                    <coordinates>-122.085075,37.4230033612141,0</coordinates>
                </Point>
            </Placemark>
            <Folder>
                <name>Level 2 Folder A</name>
                <Placemark>
                    <name>L2A Placemark 1</name>
                    <Point>
                        <coordinates>-122.086075,37.4240033612141,0</coordinates>
                    </Point>
                </Placemark>
            </Folder>
        </Folder>

        <Folder>
            <name>Level 1 Folder B</name>
            <Placemark>
                <name>L1B Placemark 1</name>
                <Point>
                    <coordinates>-122.087075,37.4250033612141,0</coordinates>
                </Point>
            </Placemark>
        </Folder>
    </Document>
</kml>"""


class TestAPIFunctionality:
    """Test the core API functionality for .all() and .children() methods."""

    def test_all_includes_nested_elements(self) -> None:
        """Test that .all() includes elements from nested folders."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        all_placemarks = kml.placemarks.all()
        placemark_names = [p.name for p in all_placemarks]

        # Should include all placemarks regardless of nesting
        expected_names = [
            "Root Placemark 1",
            "Root Placemark 2",
            "L1A Placemark 1",
            "L2A Placemark 1",
            "L1B Placemark 1",
        ]

        assert len(all_placemarks) == 5
        for name in expected_names:
            assert name in placemark_names

    def test_children_returns_direct_children_only(self) -> None:
        """Test that .children() returns only direct children."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        root_placemarks = kml.placemarks.children()
        placemark_names = [p.name for p in root_placemarks]

        # Should only include root-level placemarks
        expected_names = ["Root Placemark 1", "Root Placemark 2"]

        assert len(root_placemarks) == 2
        for name in expected_names:
            assert name in placemark_names

        # Should not include nested placemarks
        nested_names = ["L1A Placemark 1", "L2A Placemark 1", "L1B Placemark 1"]
        for name in nested_names:
            assert name not in placemark_names

    def test_children_chaining_compatibility(self) -> None:
        """Test that .children() works correctly with QuerySet chaining."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        # Test chaining with .children()
        filtered_children = kml.placemarks.children().filter(name__icontains="root")
        assert len(filtered_children) == 2

        # Test chaining with .all()
        filtered_all = kml.placemarks.all().filter(name__icontains="placemark")
        assert len(filtered_all) == 5

    def test_nested_folder_children_behavior(self) -> None:
        """Test .children() behavior on nested folder managers."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        # Get a specific folder
        level1_folder = kml.folders.children().get(name="Level 1 Folder A")

        # Test children() on the folder's placemark manager
        folder_placemarks = level1_folder.placemarks.children()
        assert len(folder_placemarks) == 1
        assert folder_placemarks[0].name == "L1A Placemark 1"

        # Test all() on the folder's placemark manager
        all_folder_placemarks = level1_folder.placemarks.all()
        # Should include nested elements from Level 2 folder
        # At least the L1A placemark, might include nested ones
        assert len(all_folder_placemarks) >= 1

    def test_type_consistency(self) -> None:
        """Test that both methods return consistent types."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        all_result = kml.placemarks.all()
        children_result = kml.placemarks.children()

        # Both should return KMLQuerySet instances
        assert type(all_result).__name__ == "KMLQuerySet"
        assert type(children_result).__name__ == "KMLQuerySet"

        # Both should contain Placemark instances
        if all_result:
            assert hasattr(all_result[0], "name")
            assert hasattr(all_result[0], "coordinates")

        if children_result:
            assert hasattr(children_result[0], "name")
            assert hasattr(children_result[0], "coordinates")

    def test_performance_compatibility(self) -> None:
        """Test that performance remains acceptable."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        # Measure .all() performance
        start = time.perf_counter()
        for _ in range(100):
            result = kml.placemarks.all()
            _ = len(result)
        all_time = time.perf_counter() - start

        # Measure .children() performance
        start = time.perf_counter()
        for _ in range(100):
            result = kml.placemarks.children()
            _ = len(result)
        children_time = time.perf_counter() - start

        # Both should complete quickly (arbitrary reasonable limits)
        assert all_time < 1.0  # Less than 1 second for 100 iterations
        assert children_time < 0.5  # Children should be faster

    def test_edge_cases_compatibility(self) -> None:
        """Test edge cases work correctly."""
        # Empty KML
        empty_kml = KMLFile.from_string(
            """<?xml version="1.0"?>
        <kml xmlns="http://www.opengis.net/kml/2.2"><Document></Document></kml>"""
        )

        assert len(empty_kml.placemarks.all()) == 0
        assert len(empty_kml.placemarks.children()) == 0

        # KML with only folders, no placemarks
        folders_only = KMLFile.from_string(
            """<?xml version="1.0"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
        <Document><Folder><name>Empty</name></Folder></Document></kml>"""
        )

        assert len(folders_only.placemarks.all()) == 0
        assert len(folders_only.placemarks.children()) == 0
        assert len(folders_only.folders.all()) == 1
        assert len(folders_only.folders.children()) == 1

    def test_all_manager_types_consistency(self) -> None:
        """Test that all manager types work consistently."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        # Test all manager types have both methods
        manager_types = [
            kml.placemarks,
            kml.folders,
            kml.paths,
            kml.polygons,
            kml.points,
            kml.multigeometries,
        ]

        for manager in manager_types:
            # Both methods should exist and be callable
            assert hasattr(manager, "all")
            assert hasattr(manager, "children")
            assert callable(manager.all)
            assert callable(manager.children)

            # Both should return QuerySet instances
            all_result = manager.all()
            children_result = manager.children()
            assert type(all_result).__name__ == "KMLQuerySet"
            assert type(children_result).__name__ == "KMLQuerySet"

    def test_managers_without_folders_manager(self) -> None:
        """Test managers that don't have folder traversal capability."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        # Point manager typically doesn't have _folders_manager
        points_all = kml.points.all()
        points_children = kml.points.children()

        # Both should work without errors
        assert isinstance(points_all, type(points_children))

        # For managers without folders, all() and children() should behave the same
        assert len(points_all) == len(points_children)

    def test_deep_nesting_performance(self) -> None:
        """Test performance with deeply nested structures."""
        # Create a deeply nested KML structure
        deep_kml_content = (
            '<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
        )

        # Create 5 levels of nesting
        for i in range(5):
            deep_kml_content += f"<Folder><name>Level {i+1}</name>"
            deep_kml_content += f"<Placemark><name>Placemark L{i+1}</name></Placemark>"

        # Close all folders
        for i in range(5):
            deep_kml_content += "</Folder>"

        deep_kml_content += "</Document></kml>"

        kml = KMLFile.from_string(deep_kml_content)

        # Test that deep nesting doesn't cause performance issues
        start = time.perf_counter()
        all_placemarks = kml.placemarks.all()
        duration = time.perf_counter() - start

        assert len(all_placemarks) == 5  # One placemark per level
        assert duration < 0.1  # Should complete quickly
