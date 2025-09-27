"""
Tests that validate every example in docs/source/api/coordinates.rst works as documented.

This test suite ensures that all code examples in the coordinates documentation
are functional and produce the expected results.
"""

import unittest
from kmlorm.models.point import Coordinate, Point
from kmlorm.core.exceptions import KMLValidationError
from kmlorm import Placemark


class TestCoordinateDocsExamples(unittest.TestCase):
    """Test cases that validate coordinates.rst documentation examples."""

    def test_creating_coordinates_from_tuple(self) -> None:
        """Test the 'From tuple' example from Creating Coordinates section."""
        # Example: coord1 = Coordinate.from_tuple((-76.5, 39.3, 100))
        coord1 = Coordinate.from_tuple((-76.5, 39.3, 100))

        self.assertEqual(coord1.longitude, -76.5)
        self.assertEqual(coord1.latitude, 39.3)
        self.assertEqual(coord1.altitude, 100)

    def test_creating_coordinates_from_string(self) -> None:
        """Test the 'From string' example from Creating Coordinates section."""
        # Example: coord2 = Coordinate.from_string("-76.5,39.3,100")
        coord2 = Coordinate.from_string("-76.5,39.3,100")

        self.assertEqual(coord2.longitude, -76.5)
        self.assertEqual(coord2.latitude, 39.3)
        self.assertEqual(coord2.altitude, 100)

    def test_creating_coordinates_direct_creation(self) -> None:
        """Test the 'Direct creation' example from Creating Coordinates section."""
        # Example: coord3 = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)
        coord3 = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)

        self.assertEqual(coord3.longitude, -76.5)
        self.assertEqual(coord3.latitude, 39.3)
        self.assertEqual(coord3.altitude, 100)

    def test_creating_coordinates_from_any_tuple(self) -> None:
        """Test the 'From various formats' tuple example from Creating Coordinates section."""
        # Example: coord4 = Coordinate.from_any((-76.5, 39.3))
        coord4 = Coordinate.from_any((-76.5, 39.3))

        self.assertEqual(coord4.longitude, -76.5)
        self.assertEqual(coord4.latitude, 39.3)
        self.assertEqual(coord4.altitude, 0)  # Default altitude

    def test_creating_coordinates_from_any_string(self) -> None:
        """Test the 'From various formats' string example from Creating Coordinates section."""
        # Example: coord5 = Coordinate.from_any("-76.5,39.3")
        coord5 = Coordinate.from_any("-76.5,39.3")

        self.assertEqual(coord5.longitude, -76.5)
        self.assertEqual(coord5.latitude, 39.3)
        self.assertEqual(coord5.altitude, 0)  # Default altitude

    def test_creating_coordinates_from_any_list(self) -> None:
        """Test the 'From various formats' list example from Creating Coordinates section."""
        # Example: coord6 = Coordinate.from_any([-76.5, 39.3, 0])
        coord6 = Coordinate.from_any([-76.5, 39.3, 0])

        self.assertEqual(coord6.longitude, -76.5)
        self.assertEqual(coord6.latitude, 39.3)
        self.assertEqual(coord6.altitude, 0)

    def test_accessing_properties_example(self) -> None:
        """Test the complete 'Accessing Properties' example."""
        # Example from documentation:
        # coord = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)
        # print(f"Longitude: {coord.longitude}")
        # print(f"Latitude: {coord.latitude}")
        # print(f"Altitude: {coord.altitude}")

        coord = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)

        # Verify the properties can be accessed as shown in documentation
        longitude_str = f"Longitude: {coord.longitude}"
        latitude_str = f"Latitude: {coord.latitude}"
        altitude_str = f"Altitude: {coord.altitude}"

        self.assertEqual(longitude_str, "Longitude: -76.5")
        self.assertEqual(latitude_str, "Latitude: 39.3")
        self.assertEqual(altitude_str, "Altitude: 100")

    def test_validation_valid_coordinate_example(self) -> None:
        """Test the valid coordinate example from Validation section."""
        # Example from documentation:
        # valid_coord = Coordinate(longitude=-76.5, latitude=39.3)
        # if valid_coord.validate():
        #     print("Coordinate is valid")

        valid_coord = Coordinate(longitude=-76.5, latitude=39.3)
        validation_result = valid_coord.validate()

        self.assertTrue(validation_result)
        # Verify the coordinate was created successfully
        self.assertEqual(valid_coord.longitude, -76.5)
        self.assertEqual(valid_coord.latitude, 39.3)

    def test_validation_invalid_coordinate_example(self) -> None:
        """Test the invalid coordinate example from Validation section."""
        # Example from documentation:
        # try:
        #     invalid_coord = Coordinate(longitude=200, latitude=100)  # Raises on __post_init__
        # except KMLValidationError as e:
        #     print(f"Invalid coordinate: {e}")

        with self.assertRaises(KMLValidationError) as context:
            _ = Coordinate(longitude=200, latitude=100)

        # Verify that a KMLValidationError was raised
        self.assertIsInstance(context.exception, KMLValidationError)
        # Verify the error message format can be used as shown in docs
        error_message = f"Invalid coordinate: {context.exception}"
        self.assertIn("Invalid coordinate:", error_message)

    def test_integration_with_placemark_creation_example(self) -> None:
        """Test the Placemark creation example from Integration with Placemark section."""
        # Example from documentation:
        # placemark = Placemark(
        #     name="Test Location",
        #     coordinates=(-76.5, 39.3, 100)  # Automatically converted to Coordinate
        # )

        placemark = Placemark(name="Test Location", coordinates=(-76.5, 39.3, 100.0))

        self.assertEqual(placemark.name, "Test Location")
        # Verify coordinates were automatically converted
        self.assertIsNotNone(placemark.coordinates)
        assert placemark.coordinates is not None  # For mypy
        self.assertEqual(placemark.coordinates.longitude, -76.5)  # pylint: disable=E1101
        self.assertEqual(placemark.coordinates.latitude, 39.3)  # pylint: disable=E1101
        self.assertEqual(placemark.coordinates.altitude, 100)  # pylint: disable=E1101

    def test_integration_with_placemark_access_properties_example(self) -> None:
        """Test the coordinate properties access example from Integration with Placemark section."""
        # Example from documentation:
        # print(f"Location: {placemark.longitude}, {placemark.latitude}")

        placemark = Placemark(name="Test Location", coordinates=(-76.5, 39.3, 100.0))

        # Test the property access as shown in documentation
        location_str = f"Location: {placemark.longitude}, {placemark.latitude}"
        self.assertEqual(location_str, "Location: -76.5, 39.3")

    def test_integration_with_placemark_full_coordinate_access_example(self) -> None:
        """Test the full coordinate object access example from Integration with
        Placemark section."""
        # Example from documentation:
        # coord = placemark.coordinates
        # if coord:
        #     print(f"Full coordinates: {coord.longitude}, {coord.latitude}, {coord.altitude}")
        # pylint: disable=E1101
        placemark = Placemark(name="Test Location", coordinates=(-76.5, 39.3, 100.0))

        coord = placemark.coordinates
        self.assertIsNotNone(coord)

        if coord:
            full_coords_str = (
                f"Full coordinates: {coord.longitude}, {coord.latitude}, {coord.altitude}"
            )
            self.assertEqual(full_coords_str, "Full coordinates: -76.5, 39.3, 100.0")

    def test_coordinate_validation_rules_longitude_bounds(self) -> None:
        """Test longitude validation rules as specified in documentation."""
        # Documentation states: Longitude: Must be between -180.0 and 180.0 degrees

        # Test valid longitude bounds
        valid_min = Coordinate(longitude=-180.0, latitude=0.0)
        valid_max = Coordinate(longitude=180.0, latitude=0.0)
        self.assertEqual(valid_min.longitude, -180.0)
        self.assertEqual(valid_max.longitude, 180.0)

        # Test invalid longitude bounds
        with self.assertRaises(KMLValidationError):
            Coordinate(longitude=-180.1, latitude=0.0)

        with self.assertRaises(KMLValidationError):
            Coordinate(longitude=180.1, latitude=0.0)

    def test_coordinate_validation_rules_latitude_bounds(self) -> None:
        """Test latitude validation rules as specified in documentation."""
        # Documentation states: Latitude: Must be between -90.0 and 90.0 degrees

        # Test valid latitude bounds
        valid_min = Coordinate(longitude=0.0, latitude=-90.0)
        valid_max = Coordinate(longitude=0.0, latitude=90.0)
        self.assertEqual(valid_min.latitude, -90.0)
        self.assertEqual(valid_max.latitude, 90.0)

        # Test invalid latitude bounds
        with self.assertRaises(KMLValidationError):
            Coordinate(longitude=0.0, latitude=-90.1)

        with self.assertRaises(KMLValidationError):
            Coordinate(longitude=0.0, latitude=90.1)

    def test_coordinate_validation_rules_altitude_finite(self) -> None:
        """Test altitude validation rules as specified in documentation."""
        # Documentation states: Altitude: Must be a finite numeric value (if provided)

        # Test valid finite altitude values
        valid_positive = Coordinate(longitude=0.0, latitude=0.0, altitude=100.5)
        valid_negative = Coordinate(longitude=0.0, latitude=0.0, altitude=-50.0)
        valid_zero = Coordinate(longitude=0.0, latitude=0.0, altitude=0.0)

        self.assertEqual(valid_positive.altitude, 100.5)
        self.assertEqual(valid_negative.altitude, -50.0)
        self.assertEqual(valid_zero.altitude, 0.0)

    def test_default_altitude_behavior(self) -> None:
        """Test that altitude defaults to 0 as mentioned in documentation."""
        # Documentation mentions: "altitude defaults to 0 if not provided"

        coord_no_altitude = Coordinate(longitude=-76.5, latitude=39.3)
        self.assertEqual(coord_no_altitude.altitude, 0)

    def test_automatic_validation_on_creation(self) -> None:
        """Test that validation happens automatically on creation as stated in documentation."""
        # Documentation note states: "Coordinate objects are automatically validated upon creation"

        # This should work without explicit validation call
        coord = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)
        self.assertIsNotNone(coord)

        # This should raise KMLValidationError immediately on creation
        with self.assertRaises(KMLValidationError):
            Coordinate(longitude=200, latitude=39.3)

    def test_coordinate_to_dict_export_example(self) -> None:
        """Test coordinate dictionary export functionality for documentation."""
        # Example for documentation: Converting coordinates to dictionary format
        coord = Coordinate(longitude=-76.5294, latitude=39.2904, altitude=100.5)

        # Export to dictionary
        coord_dict = coord.to_dict()

        # Verify dictionary structure and values
        expected_dict = {"longitude": -76.5294, "latitude": 39.2904, "altitude": 100.5}
        self.assertEqual(coord_dict, expected_dict)

        # Verify individual dictionary access
        self.assertEqual(coord_dict["longitude"], -76.5294)
        self.assertEqual(coord_dict["latitude"], 39.2904)
        self.assertEqual(coord_dict["altitude"], 100.5)

    def test_placemark_coordinate_to_dict_integration_example(self) -> None:
        """Test accessing coordinate dictionary from placemark for documentation."""
        # Example for documentation: Getting coordinate data from placemark
        # pylint: disable=E1101

        placemark = Placemark(name="Distribution Center", coordinates=(-76.5294, 39.2904, 100.5))

        # Access coordinate dictionary from placemark
        coord_dict = placemark.coordinates.to_dict() if placemark.coordinates else None

        # Verify the result
        self.assertIsNotNone(coord_dict)
        expected_dict = {"longitude": -76.5294, "latitude": 39.2904, "altitude": 100.5}
        self.assertEqual(coord_dict, expected_dict)

        # Test with placemark without coordinates
        empty_placemark = Placemark(name="No Location")
        assert empty_placemark is not None
        empty_placemark.point = Point(name="No Points")
        assert empty_placemark.point is not None
        empty_placemark.point.coordinates = None
        empty_coord_dict = (
            empty_placemark.coordinates.to_dict() if empty_placemark.coordinates else None
        )
        self.assertIsNone(empty_coord_dict)


if __name__ == "__main__":
    unittest.main()
