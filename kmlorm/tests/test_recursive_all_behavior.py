"""
Tests for recursive .all() behavior on folder managers.

These tests document the EXPECTED behavior where .all() returns ALL nested
elements recursively, not just direct children. Currently these tests FAIL
and are waiting for the bugfix implementation.

The principle: folder.placemarks.all() should return ALL placemarks anywhere
in the folder hierarchy, not just direct children.
"""

import pytest
from kmlorm import KMLFile


class TestRecursiveAllBehavior:
    """Test that .all() recursively collects all nested elements."""

    @pytest.fixture
    def nested_kml(self) -> KMLFile:
        """Create a KML with deeply nested structure for testing."""
        kml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <name>Test Document</name>
                <Placemark>
                    <name>Root Placemark 1</name>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
                <Placemark>
                    <name>Root Placemark 2</name>
                    <Point><coordinates>1,1,0</coordinates></Point>
                </Placemark>
                <Folder>
                    <name>North America</name>
                    <Placemark>
                        <name>NA Office</name>
                        <Point><coordinates>-100,45,0</coordinates></Point>
                    </Placemark>
                    <Folder>
                        <name>USA</name>
                        <Placemark>
                            <name>NYC Store</name>
                            <Point><coordinates>-74,40.7,0</coordinates></Point>
                        </Placemark>
                        <Placemark>
                            <name>LA Store</name>
                            <Point><coordinates>-118,34,0</coordinates></Point>
                        </Placemark>
                        <Folder>
                            <name>California</name>
                            <Placemark>
                                <name>SF Store</name>
                                <Point><coordinates>-122,37.7,0</coordinates></Point>
                            </Placemark>
                            <Placemark>
                                <name>SD Store</name>
                                <Point><coordinates>-117,32.7,0</coordinates></Point>
                            </Placemark>
                        </Folder>
                        <Folder>
                            <name>New York</name>
                            <Placemark>
                                <name>Albany Store</name>
                                <Point><coordinates>-73.7,42.6,0</coordinates></Point>
                            </Placemark>
                        </Folder>
                    </Folder>
                    <Folder>
                        <name>Canada</name>
                        <Placemark>
                            <name>Toronto Store</name>
                            <Point><coordinates>-79,43.6,0</coordinates></Point>
                        </Placemark>
                        <Placemark>
                            <name>Vancouver Store</name>
                            <Point><coordinates>-123,49.2,0</coordinates></Point>
                        </Placemark>
                    </Folder>
                </Folder>
                <Folder>
                    <name>Europe</name>
                    <Placemark>
                        <name>EU HQ</name>
                        <Point><coordinates>2.3,48.8,0</coordinates></Point>
                    </Placemark>
                    <Folder>
                        <name>UK</name>
                        <Placemark>
                            <name>London Store</name>
                            <Point><coordinates>-0.1,51.5,0</coordinates></Point>
                        </Placemark>
                    </Folder>
                </Folder>
            </Document>
        </kml>"""
        return KMLFile.from_string(kml_content)

    def test_folder_placemarks_all_returns_all_nested_placemarks(self, nested_kml: KMLFile) -> None:
        """
        Test that folder.placemarks.all() returns ALL placemarks in the folder tree.

        EXPECTED: When calling .all() on a folder's placemarks manager, it should
        return all placemarks in that folder AND all nested subfolders recursively.
        """
        # Get the North America folder
        na_folder = nested_kml.folders.get(name="North America")

        # Get all placemarks using .all() - should include nested ones
        all_placemarks = na_folder.placemarks.all()
        placemark_names = [p.name for p in all_placemarks]

        # EXPECTED: Should return ALL placemarks under North America
        expected_names = [
            "NA Office",           # Direct child of North America
            "NYC Store",           # In USA folder
            "LA Store",            # In USA folder
            "SF Store",            # In USA/California folder (nested)
            "SD Store",            # In USA/California folder (nested)
            "Albany Store",        # In USA/New York folder (nested)
            "Toronto Store",       # In Canada folder
            "Vancouver Store",     # In Canada folder
        ]

        assert len(all_placemarks) == 8, (
            f"Expected 8 placemarks under North America, got {len(all_placemarks)}: "
            f"{placemark_names}"
        )

        for expected_name in expected_names:
            assert expected_name in placemark_names, (
                f"Expected placemark '{expected_name}' not found in .all() results. "
                f"Got: {placemark_names}"
            )

    def test_folder_folders_all_returns_all_nested_folders(self, nested_kml: KMLFile) -> None:
        """
        Test that folder.folders.all() returns ALL folders in the folder tree.

        EXPECTED: When calling .all() on a folder's folders manager, it should
        return all subfolders at any depth, not just direct children.
        """
        # Get the North America folder
        na_folder = nested_kml.folders.get(name="North America")

        # Get all folders using .all() - should include deeply nested ones
        all_folders = na_folder.folders.all()
        folder_names = [f.name for f in all_folders]

        # EXPECTED: Should return ALL folders under North America
        expected_names = [
            "USA",          # Direct child
            "Canada",       # Direct child
            "California",   # Nested in USA
            "New York",     # Nested in USA
        ]

        assert len(all_folders) == 4, (
            f"Expected 4 folders under North America, got {len(all_folders)}: "
            f"{folder_names}"
        )

        for expected_name in expected_names:
            assert expected_name in folder_names, (
                f"Expected folder '{expected_name}' not found in .all() results. "
                f"Got: {folder_names}"
            )

    def test_deeply_nested_folder_returns_all_descendants(self, nested_kml: KMLFile) -> None:
        """
        Test that even deeply nested folders return all their descendants.

        EXPECTED: The USA folder should return all placemarks including those
        in California and New York subfolders.
        """
        # Navigate to USA folder (nested under North America)
        na_folder = nested_kml.folders.get(name="North America")
        usa_folder = na_folder.folders.get(name="USA")

        # Get all placemarks from USA folder
        usa_placemarks = usa_folder.placemarks.all()
        placemark_names = [p.name for p in usa_placemarks]

        # EXPECTED: Should include placemarks from USA and all state subfolders
        expected_names = [
            "NYC Store",        # Direct child of USA
            "LA Store",         # Direct child of USA
            "SF Store",         # In California subfolder
            "SD Store",         # In California subfolder
            "Albany Store",     # In New York subfolder
        ]

        assert len(usa_placemarks) == 5, (
            f"Expected 5 placemarks under USA, got {len(usa_placemarks)}: "
            f"{placemark_names}"
        )

        for expected_name in expected_names:
            assert expected_name in placemark_names, (
                f"Expected placemark '{expected_name}' not found in USA folder. "
                f"Got: {placemark_names}"
            )

    def test_empty_folder_returns_empty_list(self) -> None:
        """
        Test that empty folders correctly return empty lists.

        EXPECTED: A folder with no placemarks (even if it has subfolders)
        should return an empty list if those subfolders also have no placemarks.
        """
        # Create a KML with empty folders
        empty_kml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Folder>
                    <name>Empty Parent</name>
                    <Folder>
                        <name>Empty Child</name>
                        <Folder>
                            <name>Empty Grandchild</name>
                        </Folder>
                    </Folder>
                </Folder>
            </Document>
        </kml>"""

        kml = KMLFile.from_string(empty_kml_content)
        parent = kml.folders.get(name="Empty Parent")

        # Should return empty list since no placemarks anywhere
        placemarks = parent.placemarks.all()
        assert len(placemarks) == 0, "Expected no placemarks in empty folder tree"

        # But should return the nested folders
        folders = parent.folders.all()
        assert len(folders) == 2, "Expected 2 nested folders"
        folder_names = [f.name for f in folders]
        assert "Empty Child" in folder_names
        assert "Empty Grandchild" in folder_names

    def test_mixed_content_folder_returns_all_types(self) -> None:
        """
        Test that folders with mixed content types return all elements correctly.

        EXPECTED: Each element type manager should return all elements of that
        type from the entire folder tree.
        """
        # Create KML with mixed content types
        mixed_kml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Folder>
                    <name>Mixed Content</name>
                    <Placemark>
                        <name>Direct Placemark</name>
                        <Point><coordinates>0,0,0</coordinates></Point>
                    </Placemark>
                    <Placemark>
                        <name>Direct Path</name>
                        <LineString>
                            <coordinates>0,0,0 1,1,0</coordinates>
                        </LineString>
                    </Placemark>
                    <Folder>
                        <name>Nested Folder</name>
                        <Placemark>
                            <name>Nested Placemark</name>
                            <Point><coordinates>2,2,0</coordinates></Point>
                        </Placemark>
                        <Placemark>
                            <name>Nested Polygon</name>
                            <Polygon>
                                <outerBoundaryIs>
                                    <LinearRing>
                                        <coordinates>0,0,0 1,0,0 1,1,0 0,1,0 0,0,0</coordinates>
                                    </LinearRing>
                                </outerBoundaryIs>
                            </Polygon>
                        </Placemark>
                    </Folder>
                </Folder>
            </Document>
        </kml>"""

        kml = KMLFile.from_string(mixed_kml_content)
        mixed_folder = kml.folders.get(name="Mixed Content")

        # Get all placemarks (should include nested ones)
        all_placemarks = mixed_folder.placemarks.all()
        assert len(all_placemarks) == 4, (
            f"Expected 4 placemarks total, got {len(all_placemarks)}"
        )

        # Check that we got all placemarks including nested ones
        placemark_names = [p.name for p in all_placemarks]
        assert "Direct Placemark" in placemark_names
        assert "Direct Path" in placemark_names
        assert "Nested Placemark" in placemark_names
        assert "Nested Polygon" in placemark_names

    def test_all_vs_children_behavior_difference(self, nested_kml: KMLFile) -> None:
        """
        Test that .all() and .children() have different behaviors as intended.

        EXPECTED:
        - .children() returns only direct children (current working behavior)
        - .all() returns all nested elements recursively (needs fix)
        """
        na_folder = nested_kml.folders.get(name="North America")

        # .children() should return only direct children
        direct_children = na_folder.placemarks.children()
        assert len(direct_children) == 1, "Expected only 1 direct placemark child"
        assert direct_children[0].name == "NA Office"

        # .all() should return ALL placemarks including nested
        all_placemarks = na_folder.placemarks.all()
        assert len(all_placemarks) == 8, (
            f"Expected 8 total placemarks under North America, got {len(all_placemarks)}"
        )

    def test_recursive_collection_from_different_levels(self, nested_kml: KMLFile) -> None:
        """
        Test that recursive collection works correctly from any starting level.

        EXPECTED: Whether starting from root, middle, or deep level, .all()
        should always return all descendants.
        """
        # From root level
        root_placemarks = nested_kml.placemarks.all()
        assert len(root_placemarks) == 12, "Expected 12 total placemarks in entire KML"

        # From middle level (North America)
        na_folder = nested_kml.folders.get(name="North America")
        na_placemarks = na_folder.placemarks.all()
        assert len(na_placemarks) == 8, "Expected 8 placemarks under North America"

        # From deeper level (USA)
        usa_folder = na_folder.folders.get(name="USA")
        usa_placemarks = usa_folder.placemarks.all()
        assert len(usa_placemarks) == 5, "Expected 5 placemarks under USA"

        # From deepest level (California)
        california_folder = usa_folder.folders.get(name="California")
        ca_placemarks = california_folder.placemarks.all()
        assert len(ca_placemarks) == 2, "Expected 2 placemarks under California"

    @pytest.mark.parametrize("folder_name,expected_placemark_count,expected_folder_count", [
        ("North America", 8, 4),  # NA has 8 placemarks, 4 subfolders total
        ("USA", 5, 2),            # USA has 5 placemarks, 2 state subfolders
        ("Canada", 2, 0),         # Canada has 2 placemarks, no subfolders
        ("California", 2, 0),     # California has 2 placemarks, no subfolders
        ("Europe", 2, 1),         # Europe has 2 placemarks, 1 subfolder (UK)
    ])
    def test_parametrized_recursive_counts(
        self,
        nested_kml: KMLFile,
        folder_name: str,
        expected_placemark_count: int,
        expected_folder_count: int
    ) -> None:
        """
        Parametrized test to verify recursive counts for various folders.

        EXPECTED: Each folder should return the correct total count of all
        nested elements, not just direct children.
        """
        # Navigate to the folder (handle nested paths)
        folder = None
        if folder_name in ["North America", "Europe"]:
            folder = nested_kml.folders.get(name=folder_name)
        elif folder_name in ["USA", "Canada"]:
            na_folder = nested_kml.folders.get(name="North America")
            folder = na_folder.folders.get(name=folder_name)
        elif folder_name == "California":
            na_folder = nested_kml.folders.get(name="North America")
            usa_folder = na_folder.folders.get(name="USA")
            folder = usa_folder.folders.get(name=folder_name)

        if folder is None:
            pytest.fail(f"Unknown folder: {folder_name}")

        # Check placemark count
        placemarks = folder.placemarks.all()
        assert len(placemarks) == expected_placemark_count, (
            f"Folder '{folder_name}' expected {expected_placemark_count} placemarks, "
            f"got {len(placemarks)}"
        )

        # Check folder count
        folders = folder.folders.all()
        assert len(folders) == expected_folder_count, (
            f"Folder '{folder_name}' expected {expected_folder_count} subfolders, "
            f"got {len(folders)}"
        )

    def test_points_collection_from_folder_all_sources(self) -> None:
        """
        Test that folder.points.all() returns ALL Points from all sources.

        Points can exist as:
        1. Standalone Points directly in folders
        2. Points inside Placemarks

        EXPECTED: folder.points.all() should return ALL Points from both sources.
        """
        kml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Folder>
                    <name>Region</name>
                    <!-- Standalone point directly in folder -->
                    <Point><coordinates>1,1,0</coordinates></Point>
                    <!-- Placemark with a Point -->
                    <Placemark>
                        <name>Place1</name>
                        <Point><coordinates>4,4,0</coordinates></Point>
                    </Placemark>
                    <Folder>
                        <name>SubRegion</name>
                        <!-- More standalone points in nested folder -->
                        <Point><coordinates>2,2,0</coordinates></Point>
                        <Point><coordinates>3,3,0</coordinates></Point>
                        <!-- Placemark with Point in nested folder -->
                        <Placemark>
                            <name>Place2</name>
                            <Point><coordinates>5,5,0</coordinates></Point>
                        </Placemark>
                    </Folder>
                </Folder>
            </Document>
        </kml>"""

        kml = KMLFile.from_string(kml_content)
        region = kml.folders.get(name="Region")

        # Get ALL points from the region folder (standalone + from placemarks)
        all_points = region.points.all()

        # EXPECTED: Should get all 5 points (3 standalone + 2 from placemarks)
        assert len(all_points) == 5, (
            f"Expected 5 total points under Region folder, got {len(all_points)}"
        )

        # Verify coordinates to ensure we got all points
        coords = [(p.coordinates.longitude, p.coordinates.latitude) for p in all_points if p.coordinates]
        assert (1, 1) in coords, "Missing standalone point at (1,1)"
        assert (2, 2) in coords, "Missing standalone point at (2,2)"
        assert (3, 3) in coords, "Missing standalone point at (3,3)"
        assert (4, 4) in coords, "Missing Point from Place1 at (4,4)"
        assert (5, 5) in coords, "Missing Point from Place2 at (5,5)"
