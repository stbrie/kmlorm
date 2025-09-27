"""Unit tests for the Coordinate and Point classes in the kmlorm.models.point module.

Test Cases:
- Coordinate.from_tuple raises KMLValidationError for tuples of invalid length.
- Coordinate.from_any raises TypeError for unsupported types.
- Coordinate.from_string propagates KMLValidationError from from_tuple.
- Coordinate constructor raises KMLValidationError for non-numeric longitude, latitude,
    or altitude, as well as for NaN or infinite altitude values.
- Point.coordinates setter raises ValueError if Coordinate.from_any fails to parse input.
- Point string representation, repr, and property accessors behave as expected.
- Point.validate calls parent validation and coordinate validation, raising
    KMLValidationError for invalid data.
"""

from typing import Any

import pytest

from kmlorm.models.point import Coordinate, Point
from kmlorm.core.exceptions import KMLValidationError


class TestPointExtra:
    """Test suite for validating the behavior of the Coordinate and Point classes, focusing on:

    - Ensuring Coordinate.from_tuple raises KMLValidationError for tuples of invalid length.
    - Verifying Coordinate.from_any raises TypeError for unsupported types.
    - Testing that Coordinate.from_string propagates exceptions from from_tuple.
    - Validating that Coordinate raises KMLValidationError for non-numeric or invalid altitude
        values.
    - Checking that Point.coordinates setter raises ValueError on coordinate parsing errors.
    - Asserting correct string representations and property behaviors of Point instances.
    - Confirming that Point.validate calls parent validation and coordinate validation,
        raising errors as appropriate.
    """

    def test_coordinate_from_tuple_invalid_length_raises(self) -> None:
        """
        Test that Coordinate.from_tuple raises a KMLValidationError when provided with a tuple
        of invalid length.
        """
        with pytest.raises(KMLValidationError):
            Coordinate.from_tuple((10.0,))

    def test_coordinate_from_any_unsupported_type_raises(self) -> None:
        """
        Test that Coordinate.from_any raises a TypeError when called with an unsupported input type.
        """
        with pytest.raises(TypeError):
            invalid_dict: Any = {"lon": 1}
            Coordinate.from_any(invalid_dict)

    def test_coordinate_from_string_propagates_from_tuple_exception(self, monkeypatch: Any) -> None:
        """
        Test that Coordinate.from_string propagates exceptions raised by Coordinate.from_tuple.

        This test uses monkeypatching to force Coordinate.from_tuple to raise a KMLValidationError.
        It then verifies that calling Coordinate.from_string with a string input also raises a
        KMLValidationError, and that the exception message contains either "Could not parse"
            or "boom".
        """

        # Force from_tuple to raise KMLValidationError so the from_string except branch runs
        def fake_from_tuple(t: Any) -> None:
            """
            Raises a KMLValidationError with the message "boom" regardless of the input tuple.

            Args:
                t (tuple): Input tuple (not used).

            Raises:
                KMLValidationError: Always raised with the message "boom".
            """
            raise KMLValidationError("boom")

        monkeypatch.setattr(Coordinate, "from_tuple", staticmethod(fake_from_tuple))

        with pytest.raises(KMLValidationError) as exc:
            Coordinate.from_string("1,2")
        assert "Could not parse" in str(exc.value) or "boom" in str(exc.value)

    def test_validate_non_numeric_and_altitude_errors(self) -> None:
        """
        Test that the Coordinate class raises KMLValidationError when provided with
            invalid input values:
        - Non-numeric longitude and latitude.
        - Non-numeric altitude.
        - Altitude set to NaN (not a number).
        - Altitude set to infinity.
        """
        # Non-numeric lon/lat
        with pytest.raises(KMLValidationError):
            invalid_lon: Any = "a"
            invalid_lat: Any = "b"
            Coordinate(longitude=invalid_lon, latitude=invalid_lat)

        # Non-numeric altitude
        with pytest.raises(KMLValidationError):
            invalid_alt: Any = "high"
            Coordinate(longitude=0.0, latitude=0.0, altitude=invalid_alt)

        # Altitude NaN
        with pytest.raises(KMLValidationError):
            Coordinate(longitude=0.0, latitude=0.0, altitude=float("nan"))

        # Altitude infinity
        with pytest.raises(KMLValidationError):
            Coordinate(longitude=0.0, latitude=0.0, altitude=float("inf"))

    def test_point_coordinates_setter_raises_on_parse_error(self, monkeypatch: Any) -> None:
        """
        Test that assigning invalid coordinates to a Point instance raises a ValueError.

        This test uses monkeypatching to replace the Coordinate.from_any method with
            a fake implementation
        that always raises a TypeError. It then verifies that setting the 'coordinates'
             attribute of a Point
        instance with invalid data results in a ValueError being raised.
        """
        p = Point(id="x")

        def fake_from_any(val: Any) -> None:
            """
            Raises a TypeError with the message "bad" regardless of the input value.

            Args:
                val: Any input value (not used).

            Raises:
                TypeError: Always raised with the message "bad".
            """
            raise TypeError("bad")

        monkeypatch.setattr(Coordinate, "from_any", staticmethod(fake_from_any))

        with pytest.raises(ValueError):
            p.coordinates = (1.0, 2.0)

    def test_point_str_repr_and_properties(self) -> None:
        """
        Test the string representation, repr, and coordinate-related properties of the Point class.

        This test verifies:
        - The default string representation of a Point without coordinates or name.
        - The repr output includes the Point's id.
        - The string representation updates when the name is set.
        - The correct handling of coordinates, including the has_coordinates method and
            property accessors for longitude, latitude, and altitude.
        - The string representation when coordinates are present but no name is set.
        """
        p = Point(id="p1")
        assert str(p) == "Point: (no coordinates)"
        assert "Point(id='p1'" in repr(p)

        p.name = "Home"
        assert str(p) == "Point: Home"

        p = Point(id="p2", coordinates=(10.0, 20.0, 5.0))
        assert p.has_coordinates() is True
        assert p.longitude == 10.0
        assert p.latitude == 20.0
        assert p.altitude == 5.0
        # string format for coordinates branch of __str__ (no name)
        p.name = None
        s = str(p)
        assert "Point: (" in s and "10.0" in s

    def test_point_validate_calls_parent_and_coord_validate(self) -> None:
        """
        Tests that the Point.validate() method:
        - Returns True when both parent and coordinate validations pass.
        - Raises KMLValidationError when parent validation fails due to invalid name.
        """
        p = Point(id="v1", name="ok", coordinates=(0.0, 0.0))
        assert p.validate() is True

        # invalid name should cause parent validation to raise
        p_bad = Point(id="v2", name=123)
        with pytest.raises(KMLValidationError):
            p_bad.validate()

    def test_coordinate_to_dict_method(self) -> None:
        """
        Test that Coordinate.to_dict() returns correct dictionary representation.

        This test verifies:
        - Dictionary contains longitude, latitude, and altitude keys
        - Values match the coordinate properties
        - Default altitude (0) is included
        - Custom altitude values are preserved
        """
        # Test with default altitude
        coord1 = Coordinate(longitude=-76.5, latitude=39.3)
        result1 = coord1.to_dict()

        expected1 = {"longitude": -76.5, "latitude": 39.3, "altitude": 0}
        assert result1 == expected1

        # Test with custom altitude
        coord2 = Coordinate(longitude=180.0, latitude=-90.0, altitude=1500.75)
        result2 = coord2.to_dict()

        expected2 = {"longitude": 180.0, "latitude": -90.0, "altitude": 1500.75}
        assert result2 == expected2

        # Test with negative altitude
        coord3 = Coordinate(longitude=0.0, latitude=0.0, altitude=-100.0)
        result3 = coord3.to_dict()

        expected3 = {"longitude": 0.0, "latitude": 0.0, "altitude": -100.0}
        assert result3 == expected3

    def test_point_to_dict_method(self) -> None:
        """
        Test that Point.to_dict() returns correct dictionary representation.

        This test verifies:
        - Dictionary contains all point properties
        - Coordinate data is properly nested
        - None coordinates are handled correctly
        - All point-specific properties are included
        """
        # Test point with coordinates
        coord = Coordinate(longitude=-76.5, latitude=39.3, altitude=100.0)
        point = Point(
            id="test_point",
            name="Test Location",
            description="A test point",
            coordinates=coord,
            extrude=True,
            altitude_mode="absolute",
            tessellate=True,
        )

        result = point.to_dict()

        # Verify coordinate data is nested correctly
        assert result["coordinates"] == {"longitude": -76.5, "latitude": 39.3, "altitude": 100.0}

        # Verify individual coordinate properties
        assert result["longitude"] == -76.5
        assert result["latitude"] == 39.3
        assert result["altitude"] == 100.0

        # Verify point-specific properties
        assert result["id"] == "test_point"
        assert result["name"] == "Test Location"
        assert result["description"] == "A test point"
        assert result["extrude"] is True
        assert result["altitude_mode"] == "absolute"
        assert result["tessellate"] is True

        # Test point without coordinates
        point_no_coords = Point(id="no_coords", name="No Coordinates")
        result_no_coords = point_no_coords.to_dict()

        assert result_no_coords["coordinates"] is None
        assert result_no_coords["longitude"] is None
        assert result_no_coords["latitude"] is None
        assert result_no_coords["altitude"] is None
        assert result_no_coords["id"] == "no_coords"
        assert result_no_coords["name"] == "No Coordinates"
