"""
Unit tests for the MultiGeometry class and its interactions with Point, Path, and Polygon
    geometries.

Classes:
    TestMultiGeometry: Contains tests for basic operations and nested usage of MultiGeometry.

Test Methods:
    test_multigeometry_basic_operations:
        - Tests adding Point, Path, and Polygon objects to a MultiGeometry.
        - Verifies length, indexing, and iteration.
        - Checks retrieval of specific geometry types (points, paths, polygons).
        - Asserts correct geometry counts and dictionary serialization.
        - Confirms presence of coordinates.

    test_multigeometry_nested:
        - Tests nesting of MultiGeometry instances.
        - Verifies recursive retrieval of points from nested structures.
        - Checks retrieval of nested MultiGeometry objects.
        - Asserts correct geometry counts in nested scenarios.
"""

from kmlorm.models.multigeometry import MultiGeometry
from kmlorm.models.point import Point
from kmlorm.models.path import Path
from kmlorm.models.polygon import Polygon


class TestMultiGeometry:
    """
    Test suite for the MultiGeometry class, verifying its basic operations and nested
    geometry handling.

    Tests:
    - test_multigeometry_basic_operations:
        Validates adding, retrieving, and counting different geometry types (Point, Path,
            Polygon) within a MultiGeometry instance.
        Checks correct behavior of methods such as add_geometry, get_points, get_paths,
            get_polygons, geometry_counts, has_coordinates, and to_dict.

    - test_multigeometry_nested:
        Ensures MultiGeometry supports nested MultiGeometry instances.
        Verifies recursive retrieval of points, detection of nested MultiGeometry objects, and
            correct geometry counting in nested structures.
    """

    def test_multigeometry_basic_operations(self) -> None:
        """
        Test basic operations of the MultiGeometry class.

        This test verifies:
        - Initialization of an empty MultiGeometry.
        - Adding Point, Path, and Polygon geometries.
        - Correct length and indexing after adding geometries.
        - Retrieval of specific geometry types (points, paths, polygons).
        - Accurate geometry counts for each type and total.
        - Presence of coordinates in the MultiGeometry.
        - Correct dictionary serialization including geometry counts.
        """
        mg = MultiGeometry()
        assert len(mg) == 0
        assert list(mg) == []  # pylint: disable=use-implicit-booleaness-not-comparison

        p = Point(coordinates=(10.0, 20.0))
        path = Path(coordinates=[(0.0, 0.0), (1.0, 1.0)])
        poly = Polygon(outer_boundary=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)])

        mg.add_geometry(p)
        mg.add_geometry(path)
        mg.add_geometry(poly)

        assert len(mg) == 3
        assert mg[0] is p
        assert mg[1] is path
        assert mg[2] is poly

        pts = mg.get_points()
        assert pts == [p]

        paths = mg.get_paths()
        assert paths == [path]

        polygons = mg.get_polygons()
        assert polygons == [poly]

        counts = mg.geometry_counts()
        assert counts["points"] == 1
        assert counts["paths"] == 1
        assert counts["polygons"] == 1
        assert counts["multigeometries"] == 0
        assert counts["total"] == 3

        assert mg.has_coordinates() is True

        d = mg.to_dict()
        assert "geometries" in d
        assert d["geometry_counts"]["total"] == 3

    def test_multigeometry_nested(self) -> None:
        """
        Test the behavior of nested MultiGeometry objects.

        This test verifies that:
        - Points can be nested within MultiGeometry instances, including nested
            MultiGeometry objects.
        - The `get_points()` method retrieves all points from both the parent and
            nested MultiGeometry objects.
        - The `get_multigeometries()` method returns nested MultiGeometry instances.
        - The `geometry_counts()` method correctly counts the number of points and
            MultiGeometry objects, including nested ones.
        """
        p1 = Point(coordinates=(0.0, 0.0))
        p2 = Point(coordinates=(1.0, 1.0))

        child = MultiGeometry([p2])
        parent = MultiGeometry([p1, child])

        # nested retrieval
        assert parent.get_points() == [p1, p2]

        # nested multigeometries
        multigeoms = parent.get_multigeometries()
        assert any(isinstance(m, MultiGeometry) for m in multigeoms)

        counts = parent.geometry_counts()
        assert counts["points"] == 2
        assert counts["multigeometries"] >= 1
