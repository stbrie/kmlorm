"""
Unit tests for the Polygon class in kmlorm.models.polygon.

Test cases:
- Creation of Polygon with outer boundary from tuples.
- Creation of Polygon with outer boundary from strings.
- Creation of Polygon with inner boundaries (holes).
- Validation that invalid coordinate strings raise KMLInvalidCoordinates.
- Validation that invalid coordinate tuples raise KMLInvalidCoordinates.
"""

from typing import List, Tuple, Union

import pytest

from kmlorm.models.polygon import Polygon
from kmlorm.core.exceptions import KMLInvalidCoordinates


class TestPolygon:
    """
    Test suite for the Polygon class.

    This class contains unit tests to verify the correct behavior of the Polygon class, including:
    - Creating polygons from tuples and string representations of coordinates.
    - Ensuring correct boundary point and hole counts.
    - Serializing polygons to dictionaries.
    - Handling of inner boundaries (holes).
    - Raising appropriate exceptions for invalid coordinate inputs.

    Tested methods and behaviors:
    - Construction from tuples and strings.
    - Attribute correctness: boundary_point_count, hole_count.
    - Serialization via to_dict().
    - Exception handling for invalid coordinates.
    """

    def test_polygon_outer_boundary_from_tuples(self) -> None:
        """
        Test that a Polygon object can be created from a list of coordinate tuples as its
        outer boundary, and that its properties such as boundary point count, hole count,
        and string representation are correct.
        """
        poly = Polygon(outer_boundary=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)], name="A")
        assert poly.boundary_point_count == 3
        assert poly.hole_count == 0
        assert "Polygon" in str(poly)

    def test_polygon_outer_boundary_from_strings(self) -> None:
        """
        Test that a Polygon object correctly initializes its outer boundary from a list
        of coordinate strings, and that the boundary point count and dictionary
        representation are as expected.
        """
        poly = Polygon(outer_boundary=["0.0,0.0", "1.0,0.0", "1.0,1.0"])
        assert poly.boundary_point_count == 3
        d = poly.to_dict()
        assert isinstance(d["outer_boundary"], list)
        assert d["boundary_point_count"] == 3

    def test_polygon_with_inner_boundaries(self) -> None:
        """
        Test that a Polygon object with specified outer and inner boundaries correctly reports
        the number of points in its outer boundary and the number of inner boundaries (holes).

        This test creates a polygon with:
        - An outer boundary defined by three points.
        - One inner boundary (hole) defined by three points.

        Asserts:
            - The boundary_point_count property equals 3 (number of points in the outer boundary).
            - The hole_count property equals 1 (number of inner boundaries).
        """
        outer: List[Union[Tuple[float, ...], str]] = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)]
        inner: List[List[Union[Tuple[float, ...], str]]] = [[(0.5, 0.5), (1.0, 0.5), (1.0, 1.0)]]
        poly = Polygon(outer_boundary=outer, inner_boundaries=inner)
        assert poly.boundary_point_count == 3
        assert poly.hole_count == 1

    def test_invalid_coordinate_string_raises(self) -> None:
        """
        Test that creating a Polygon with an invalid coordinate string in the outer_boundary
        raises a KMLInvalidCoordinates exception.
        """
        with pytest.raises(KMLInvalidCoordinates):
            Polygon(outer_boundary=["invalid"])

    def test_invalid_coordinate_tuple_raises(self) -> None:
        """
        Test that creating a Polygon with an invalid coordinate tuple (e.g., a tuple
        with insufficient elements) raises a KMLInvalidCoordinates exception.
        """
        with pytest.raises(KMLInvalidCoordinates):
            Polygon(outer_boundary=[(1.0,)])
