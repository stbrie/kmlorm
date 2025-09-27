"""
Test suite for the Path class in kmlorm.models.path.
This module contains tests that verify the correct behavior of the Path class, including:
- Initialization from coordinate tuples and strings.
- Property assignment and retrieval (tessellate, altitude_mode, element_id, name).
- Parsing and handling of 2D and 3D coordinates, including mixed whitespace and
    missing altitude values.
- Error handling for invalid coordinate inputs, such as too few components, non-numeric
    values, or invalid types.
Classes:
    TestPath: Contains unit tests for the Path class.
Test Cases:
    - test_path_from_tuples_and_properties: Verifies correct creation and property handling
        of Path objects from tuples.
    - test_path_from_strings_and_mixed_whitespace: Checks parsing of coordinate strings with
        mixed whitespace and optional altitude.
    - test_parse_coordinates_raises_on_bad_input: Ensures KMLInvalidCoordinates is raised
        for invalid coordinate inputs.
"""

from typing import Any, List, Tuple, Union

import pytest

from kmlorm.models.path import Path
from kmlorm.core.exceptions import KMLInvalidCoordinates


class TestPath:
    """Test suite for the Path class, verifying its initialization, property handling,
    coordinate parsing, and error handling for invalid inputs.

    This class contains tests that:
    - Ensure correct creation of Path objects from tuples and strings representing coordinates.
    - Verify the correct assignment and retrieval of properties such as tessellate,
        altitude_mode, element_id, and name.
    - Check the correct parsing and handling of 2D and 3D coordinates, including mixed
        whitespace and missing altitude values.
    - Confirm that the Path class raises KMLInvalidCoordinates for invalid coordinate
        inputs, such as too few components, non-numeric values, or invalid types.
    """

    def test_path_from_tuples_and_properties(self) -> None:
        """
        Test the creation of a Path object from coordinate tuples and verify its properties.

        This test ensures that:
        - The Path object is correctly initialized with a list of 2D and 3D coordinate tuples.
        - The tessellate and altitude_mode properties are set as expected.
        - The element_id and name are correctly assigned and reflected in the string representation.
        - The point_count and coordinates properties return the correct values.
        - The to_dict() method returns a dictionary with the correct structure and values.
        """
        coords: List[Union[Tuple[float, ...], str]] = [
            (10.0, 20.0),
            (11.0, 21.0),
            (12.5, 22.5, 100.0),
        ]
        p = Path(
            coordinates=coords,
            tessellate=True,
            altitude_mode="absolute",
            element_id="p1",
            name="Route",
        )

        assert p.point_count == 3
        assert len(p.coordinates) == 3
        assert p.tessellate is True
        assert p.altitude_mode == "absolute"
        assert "Route" in str(p)

        d = p.to_dict()
        assert d["id"] == "p1"
        assert d["point_count"] == 3
        assert d["coordinates"] == [(10.0, 20.0), (11.0, 21.0), (12.5, 22.5, 100.0)]

    def test_path_from_strings_and_mixed_whitespace(self) -> None:
        """
        Test that the Path class correctly parses a list of coordinate strings with
        mixed whitespace and optional altitude values.

        This test verifies:
        - The Path object correctly counts the number of coordinate points.
        - The coordinates are parsed into tuples of floats, handling both 2D and 3D coordinates.
        - Whitespace and missing altitude values are handled gracefully.
        """
        scoords: List[Union[Tuple[float, ...], str]] = ["10.0, 20.0", "11.0,21.0", "12.5, 22.5,100"]
        p = Path(coordinates=scoords)
        assert p.point_count == 3
        assert p.coordinates[0] == (10.0, 20.0)
        assert p.coordinates[2] == (12.5, 22.5, 100.0)

    def test_parse_coordinates_raises_on_bad_input(self) -> None:
        """
        Test that Path raises KMLInvalidCoordinates when given invalid coordinate inputs.

        This test covers the following invalid cases:
        - Too few components in a coordinate (e.g., only longitude provided).
        - Non-numeric coordinate values.
        - Invalid coordinate type (e.g., integer instead of tuple or list).
        """
        # too few components
        with pytest.raises(KMLInvalidCoordinates):
            Path(coordinates=["10.0"])  # only longitude

        # non-numeric
        with pytest.raises(KMLInvalidCoordinates):
            invalid_coords: Any = [("a", "b")]
            Path(coordinates=invalid_coords)

        # invalid type
        with pytest.raises(KMLInvalidCoordinates):
            invalid_coords_int: Any = [123]
            Path(coordinates=invalid_coords_int)
