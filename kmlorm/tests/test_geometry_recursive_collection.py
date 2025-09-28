"""
Tests for comprehensive recursive collection of all geometry types.

According to KML 2.2 specification:
- Folders can contain: Placemarks, other Folders, and standalone geometries
- Placemarks can contain: Point, LineString, Polygon, or MultiGeometry
- MultiGeometry can contain: Points, LineStrings, Polygons, and other MultiGeometries

These tests ensure that folder.points.all(), folder.paths.all(), etc. return ALL
instances of those geometry types regardless of how deeply nested they are.
"""

import pytest
from kmlorm import KMLFile, Point, Path, Polygon


class TestGeometryRecursiveCollection:
    """Test that all geometry types are collected recursively from all containers."""

    @pytest.fixture
    def comprehensive_kml(self) -> KMLFile:
        """Create a KML with all possible geometry nesting scenarios."""
        kml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <name>Comprehensive Geometry Test</name>

                <!-- Root level standalone geometries -->
                <Point><coordinates>0,0,0</coordinates></Point>
                <LineString><coordinates>0,0,0 1,0,0</coordinates></LineString>
                <Polygon>
                    <outerBoundaryIs>
                        <LinearRing>
                            <coordinates>0,0,0 1,0,0 1,1,0 0,1,0 0,0,0</coordinates>
                        </LinearRing>
                    </outerBoundaryIs>
                </Polygon>

                <Folder>
                    <name>TestFolder</name>

                    <!-- Standalone geometries directly in folder -->
                    <Point><coordinates>10,10,0</coordinates></Point>
                    <LineString><coordinates>10,10,0 11,10,0</coordinates></LineString>
                    <Polygon>
                        <outerBoundaryIs>
                            <LinearRing>
                                <coordinates>10,10,0 11,10,0 11,11,0 10,11,0 10,10,0</coordinates>
                            </LinearRing>
                        </outerBoundaryIs>
                    </Polygon>

                    <!-- Placemark with Point -->
                    <Placemark>
                        <name>PM with Point</name>
                        <Point><coordinates>20,20,0</coordinates></Point>
                    </Placemark>

                    <!-- Placemark with LineString -->
                    <Placemark>
                        <name>PM with LineString</name>
                        <LineString><coordinates>20,20,0 21,20,0</coordinates></LineString>
                    </Placemark>

                    <!-- Placemark with Polygon -->
                    <Placemark>
                        <name>PM with Polygon</name>
                        <Polygon>
                            <outerBoundaryIs>
                                <LinearRing>
                                    <coordinates>20,20,0 21,20,0 21,21,0 20,21,0 20,20,0</coordinates>
                                </LinearRing>
                            </outerBoundaryIs>
                        </Polygon>
                    </Placemark>

                    <!-- Placemark with MultiGeometry -->
                    <Placemark>
                        <name>PM with MultiGeometry</name>
                        <MultiGeometry>
                            <Point><coordinates>30,30,0</coordinates></Point>
                            <Point><coordinates>31,31,0</coordinates></Point>
                            <LineString><coordinates>30,30,0 31,30,0</coordinates></LineString>
                            <Polygon>
                                <outerBoundaryIs>
                                    <LinearRing>
                                        <coordinates>30,30,0 31,30,0 31,31,0 30,31,0 30,30,0</coordinates>
                                    </LinearRing>
                                </outerBoundaryIs>
                            </Polygon>
                        </MultiGeometry>
                    </Placemark>

                    <!-- Nested Folder -->
                    <Folder>
                        <name>NestedFolder</name>

                        <!-- More standalone geometries in nested folder -->
                        <Point><coordinates>40,40,0</coordinates></Point>
                        <LineString><coordinates>40,40,0 41,40,0</coordinates></LineString>
                        <Polygon>
                            <outerBoundaryIs>
                                <LinearRing>
                                    <coordinates>40,40,0 41,40,0 41,41,0 40,41,0 40,40,0</coordinates>
                                </LinearRing>
                            </outerBoundaryIs>
                        </Polygon>

                        <!-- Placemark with geometries in nested folder -->
                        <Placemark>
                            <name>Nested PM</name>
                            <Point><coordinates>50,50,0</coordinates></Point>
                        </Placemark>

                        <!-- Deeply nested folder -->
                        <Folder>
                            <name>DeeplyNestedFolder</name>
                            <Point><coordinates>60,60,0</coordinates></Point>
                            <Placemark>
                                <name>Deep PM</name>
                                <MultiGeometry>
                                    <Point><coordinates>70,70,0</coordinates></Point>
                                    <LineString><coordinates>70,70,0 71,70,0</coordinates></LineString>
                                </MultiGeometry>
                            </Placemark>
                        </Folder>
                    </Folder>
                </Folder>
            </Document>
        </kml>"""
        return KMLFile.from_string(kml_content)

    def test_points_collected_from_all_sources(self, comprehensive_kml: KMLFile) -> None:
        """
        Test that folder.points.all() returns ALL Points from:
        1. Standalone Points directly in folders
        2. Points inside Placemarks
        3. Points inside MultiGeometry (in Placemarks)
        4. Points in nested folders at any depth
        """
        test_folder = comprehensive_kml.folders.get(name="TestFolder")
        all_points = test_folder.points.all()

        # Get coordinates for easier checking
        coords = {(p.coordinates.longitude, p.coordinates.latitude)
                 for p in all_points if p.coordinates}

        # Expected Points:
        # - Standalone in TestFolder: (10,10)
        # - In "PM with Point": (20,20)
        # - In "PM with MultiGeometry": (30,30), (31,31)
        # - Standalone in NestedFolder: (40,40)
        # - In "Nested PM": (50,50)
        # - Standalone in DeeplyNestedFolder: (60,60)
        # - In "Deep PM" MultiGeometry: (70,70)
        expected_coords = {
            (10, 10),  # Standalone in TestFolder
            (20, 20),  # PM with Point
            (30, 30),  # PM with MultiGeometry - point 1
            (31, 31),  # PM with MultiGeometry - point 2
            (40, 40),  # Standalone in NestedFolder
            (50, 50),  # Nested PM
            (60, 60),  # Standalone in DeeplyNestedFolder
            (70, 70),  # Deep PM MultiGeometry
        }

        assert coords == expected_coords, (
            f"Missing points: {expected_coords - coords}, "
            f"Extra points: {coords - expected_coords}"
        )
        assert len(all_points) == 8, f"Expected 8 points, got {len(all_points)}"

    def test_paths_collected_from_all_sources(self, comprehensive_kml: KMLFile) -> None:
        """
        Test that folder.paths.all() returns ALL LineStrings/Paths from:
        1. Standalone LineStrings directly in folders
        2. LineStrings inside Placemarks
        3. LineStrings inside MultiGeometry
        4. LineStrings in nested folders at any depth
        """
        test_folder = comprehensive_kml.folders.get(name="TestFolder")
        all_paths = test_folder.paths.all()

        # Count paths by checking their first coordinate
        path_starts = []
        for path in all_paths:
            if path.coordinates and len(path.coordinates) > 0:
                first_coord = path.coordinates[0]
                path_starts.append((first_coord[0], first_coord[1]))

        # Expected LineStrings (by starting coordinate):
        # - Standalone in TestFolder: starts at (10,10)
        # - In "PM with LineString": starts at (20,20)
        # - In "PM with MultiGeometry": starts at (30,30)
        # - Standalone in NestedFolder: starts at (40,40)
        # - In "Deep PM" MultiGeometry: starts at (70,70)
        expected_starts = {
            (10, 10),  # Standalone in TestFolder
            (20, 20),  # PM with LineString
            (30, 30),  # PM with MultiGeometry
            (40, 40),  # Standalone in NestedFolder
            (70, 70),  # Deep PM MultiGeometry
        }

        path_starts_set = set(path_starts)
        assert path_starts_set == expected_starts, (
            f"Missing paths: {expected_starts - path_starts_set}, "
            f"Extra paths: {path_starts_set - expected_starts}"
        )
        assert len(all_paths) == 5, f"Expected 5 paths, got {len(all_paths)}"

    def test_polygons_collected_from_all_sources(self, comprehensive_kml: KMLFile) -> None:
        """
        Test that folder.polygons.all() returns ALL Polygons from:
        1. Standalone Polygons directly in folders
        2. Polygons inside Placemarks
        3. Polygons inside MultiGeometry
        4. Polygons in nested folders at any depth
        """
        test_folder = comprehensive_kml.folders.get(name="TestFolder")
        all_polygons = test_folder.polygons.all()

        # Count polygons by checking their first boundary coordinate
        polygon_starts = []
        for polygon in all_polygons:
            if polygon.outer_boundary and len(polygon.outer_boundary) > 0:
                first_coord = polygon.outer_boundary[0]
                polygon_starts.append((first_coord[0], first_coord[1]))

        # Expected Polygons (by first boundary coordinate):
        # - Standalone in TestFolder: starts at (10,10)
        # - In "PM with Polygon": starts at (20,20)
        # - In "PM with MultiGeometry": starts at (30,30)
        # - Standalone in NestedFolder: starts at (40,40)
        expected_starts = {
            (10, 10),  # Standalone in TestFolder
            (20, 20),  # PM with Polygon
            (30, 30),  # PM with MultiGeometry
            (40, 40),  # Standalone in NestedFolder
        }

        polygon_starts_set = set(polygon_starts)
        assert polygon_starts_set == expected_starts, (
            f"Missing polygons: {expected_starts - polygon_starts_set}, "
            f"Extra polygons: {polygon_starts_set - expected_starts}"
        )
        assert len(all_polygons) == 4, f"Expected 4 polygons, got {len(all_polygons)}"

    def test_root_level_geometries(self, comprehensive_kml: KMLFile) -> None:
        """Test that root-level standalone geometries are collected."""
        # Root level should have standalone geometries
        root_points = comprehensive_kml.points.all()
        root_paths = comprehensive_kml.paths.all()
        root_polygons = comprehensive_kml.polygons.all()

        # Should get the root standalone geometry plus all from folders
        assert len(root_points) >= 1, "Should have at least root point"
        assert len(root_paths) >= 1, "Should have at least root path"
        assert len(root_polygons) >= 1, "Should have at least root polygon"

        # Check root point
        root_point_coords = [(p.coordinates.longitude, p.coordinates.latitude)
                            for p in root_points if p.coordinates]
        assert (0, 0) in root_point_coords, "Root point at (0,0) not found"

    def test_empty_folders_return_empty_collections(self) -> None:
        """Test that folders with no geometries return empty collections."""
        kml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Folder>
                    <name>EmptyFolder</name>
                    <Folder>
                        <name>EmptyNested</name>
                    </Folder>
                </Folder>
            </Document>
        </kml>"""

        kml = KMLFile.from_string(kml_content)
        empty_folder = kml.folders.get(name="EmptyFolder")

        assert len(empty_folder.points.all()) == 0
        assert len(empty_folder.paths.all()) == 0
        assert len(empty_folder.polygons.all()) == 0
        assert len(empty_folder.placemarks.all()) == 0

    @pytest.mark.parametrize("geometry_type,expected_count", [
        ("points", 8),
        ("paths", 5),
        ("polygons", 4),
    ])
    def test_parametrized_geometry_counts(
        self,
        comprehensive_kml: KMLFile,
        geometry_type: str,
        expected_count: int
    ) -> None:
        """Parametrized test for different geometry type counts."""
        test_folder = comprehensive_kml.folders.get(name="TestFolder")
        manager = getattr(test_folder, geometry_type)
        all_elements = manager.all()

        assert len(all_elements) == expected_count, (
            f"Expected {expected_count} {geometry_type}, got {len(all_elements)}"
        )