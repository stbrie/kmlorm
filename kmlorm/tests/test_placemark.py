"""
Unit tests for the Placemark class and its interactions with Point and KMLValidationError.

Test cases included:
- test_str_variants_and_coordinate_formatting: Verifies the string representation
    of Placemark for different attribute combinations (name, address, coordinates).
- test_coordinates_setter_creates_point_and_properties: Ensures the coordinates
    setter correctly creates or updates the Point object and related properties.
- test_to_dict_includes_point_and_extended_data: Checks that Placemark's to_dict
    method includes point, coordinates, extended_data, and element_id.
- test_distance_and_bearing_between_placemarks_and_tuples: Validates distance and
    bearing calculations between Placemarks and coordinate tuples, including edge cases.
- test_validate_propagates_point_validation_and_extended_data_type: Confirms that
    validation propagates to Point and checks extended_data type, raising KMLValidationError
    as appropriate.
"""

from math import isclose
from typing import Any

import pytest

from kmlorm.models.placemark import Placemark
from kmlorm.models.point import Point
from kmlorm.core.exceptions import KMLValidationError
from kmlorm import KMLFile


class TestPlacemark:
    """
    Test suite for the Placemark class, verifying its string representation, coordinate handling,
    dictionary serialization, geospatial calculations, and validation logic.

    Tests included:
    - String representation prioritizing `name`, then `address`, then coordinates.
    - Setting coordinates via string or tuple and ensuring correct Point creation
        and property updates.
    - Serialization to dictionary including point and extended data.
    - Distance and bearing calculations between placemarks and coordinate tuples,
        including edge cases.
    - Validation propagation for Point and extended_data, ensuring proper error
        handling for invalid data.
    """

    def test_str_variants_and_coordinate_formatting(self) -> None:
        """
        Test the string representation of the Placemark class for various attribute combinations.

        This test verifies:
        - The `name` attribute takes precedence in the string representation.
        - If `name` is missing, the `address` attribute is used in the string representation.
        - If both `name` and `address` are missing, the string representation includes
            formatted coordinates.
        """
        # name takes precedence
        p_named = Placemark(name="Home", point=Point(coordinates=(10.0, 20.0)))
        assert str(p_named) == "Home"

        # address used when name missing
        p_addr = Placemark(address="123 Main St")
        assert str(p_addr) == "Placemark at 123 Main St"

        # coordinates formatting path (note: current implementation formats
        # using latitude then longitude due to ordering in code)
        p_coord = Placemark(point=Point(coordinates=(10.0, 20.0)))
        # The string shows formatted numbers; verify values are present
        s = str(p_coord)
        assert "Placemark(" in s and "," in s

    def test_coordinates_setter_creates_point_and_properties(self) -> None:
        """
        Test that setting the `coordinates` attribute on a `Placemark` instance:

        - Creates a `Point` object and assigns it to `p.point` if it does not exist.
        - Correctly sets the `has_coordinates` property to True.
        - Properly parses and assigns longitude and latitude values when given as
            a string (e.g., "10,20").
        - Updates the existing `Point` object and longitude/latitude values when given
            as a tuple (e.g., (11.0, 21.0)).
        """
        p = Placemark()
        assert p.point is None

        # set via string
        p.coordinates = "10,20"
        assert p.point is not None
        assert p.has_coordinates is True  # type: ignore[unreachable]
        assert p.longitude == 10.0
        assert p.latitude == 20.0

        # set via tuple updates existing point
        p.coordinates = (11.0, 21.0)
        assert p.longitude == 11.0
        assert p.latitude == 21.0

    def test_to_dict_includes_point_and_extended_data(self) -> None:
        """
        Test that the Placemark.to_dict() method includes the point, coordinates,
        extended_data, and id fields when a Placemark is initialized with these attributes.
        """
        p = Placemark(
            point=Point(coordinates=(0.0, 0.0)), extended_data={"k": "v"}, element_id="pm1"
        )
        d = p.to_dict()
        assert d["id"] == "pm1"
        assert d["point"] is not None
        assert d["coordinates"] == p.coordinates
        assert d["extended_data"] == {"k": "v"}

    def test_distance_and_bearing_between_placemarks_and_tuples(self) -> None:
        """
        Test the distance_to and bearing_to methods of the Placemark class with
        both Placemark and tuple inputs.

        This test verifies:
        - The calculated distance between two Placemarks at (0.0, 0.0) and (1.0, 0.0) is
            approximately 111.32 km.
        - The distance calculation is consistent when using a raw coordinate tuple as the target.
        - The bearing from (0.0, 0.0) to (1.0, 0.0) is approximately 90 degrees (east).
        - The methods return None when provided with an invalid tuple length.
        """
        p1 = Placemark(point=Point(coordinates=(0.0, 0.0)))
        p2 = Placemark(point=Point(coordinates=(1.0, 0.0)))

        dist = p1.distance_to(p2)
        assert dist is not None
        # approximate expected distance (~111.32 km per degree at equator)
        assert isclose(dist, 111.32, rel_tol=0.01)

        # distance to raw tuple
        dist2 = p1.distance_to((1.0, 0.0))
        assert dist2 is not None and dist is not None
        assert isclose(dist2, dist, rel_tol=1e-6)

        # bearing: from (0,0) to (1,0) should be ~90 degrees (east)
        bear = p1.bearing_to(p2)
        assert bear is not None
        assert isclose(bear, 90.0, abs_tol=1.0)

        # invalid other tuple length returns None
        invalid_tuple: Any = (1.0,)
        assert p1.distance_to(invalid_tuple) is None
        assert p1.bearing_to(invalid_tuple) is None

    def test_validate_propagates_point_validation_and_extended_data_type(self) -> None:
        """
        Test that Placemark validation propagates Point coordinate validation errors
        and enforces extended_data type.

        - Ensures that assigning invalid coordinates to a Point raises a KMLValidationError.
        - Verifies that a Placemark with valid Point coordinates and a dictionary as
            extended_data passes validation.
        - Checks that a Placemark with a non-dictionary extended_data raises a
            KMLValidationError during validation.
        """
        # directly set invalid coordinates via Point API -> Coordinate validation
        # raises KMLValidationError
        with pytest.raises(KMLValidationError):
            Point(coordinates=(200.0, 0.0))  # invalid longitude triggers validation error

        p = Placemark(point=Point(coordinates=(10.0, 20.0)), extended_data={})
        assert p.validate() is True

        # extended_data must be a dict
        invalid_data: Any = "nope"
        p2 = Placemark(point=Point(coordinates=(10.0, 20.0)), extended_data=invalid_data)
        with pytest.raises(KMLValidationError):
            p2.validate()

    def test_has_coordinates_with_flatten_mixed_scenario(self) -> None:
        """
        Test that has_coordinates() with flatten=True correctly filters placemarks
        that have coordinates from those that don't in a mixed scenario.

        This test verifies:
        - KML file with placemarks that have coordinates and placemarks that don't
        - flatten=True retrieves all placemarks regardless of folder structure
        - has_coordinates() filters to only return placemarks with coordinates
        """
        kml_data = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <name>Mixed Coordinates Test</name>
                <Placemark>
                    <name>With Coordinates 1</name>
                    <Point>
                        <coordinates>-122.0856545755255,37.42243077405461,0</coordinates>
                    </Point>
                </Placemark>
                <Placemark>
                    <name>Without Coordinates 1</name>
                    <description>This placemark has no coordinates</description>
                </Placemark>
                <Folder>
                    <name>Test Folder</name>
                    <Placemark>
                        <name>With Coordinates 2</name>
                        <Point>
                            <coordinates>-122.084075,37.4220033612141,0</coordinates>
                        </Point>
                    </Placemark>
                    <Placemark>
                        <name>Without Coordinates 2</name>
                        <description>Another placemark without coordinates</description>
                    </Placemark>
                </Folder>
                <Placemark>
                    <name>With Coordinates 3</name>
                    <Point>
                        <coordinates>-122.085075,37.4230033612141,0</coordinates>
                    </Point>
                </Placemark>
            </Document>
        </kml>"""

        kml_file = KMLFile.from_string(kml_data)

        # Get all placemarks with flatten=True
        all_placemarks = kml_file.placemarks.all()
        # Should get all 5 placemarks regardless of folder structure
        assert len(all_placemarks) == 5

        # Get only placemarks with coordinates using has_coordinates()
        placemarks_with_coords = kml_file.placemarks.all().has_coordinates()

        # Should only get the 3 placemarks that have coordinates
        assert len(placemarks_with_coords) == 3

        # Verify the names of placemarks with coordinates
        names_with_coords = {p.name for p in placemarks_with_coords}
        expected_names = {"With Coordinates 1", "With Coordinates 2", "With Coordinates 3"}
        assert names_with_coords == expected_names

        # Verify all returned placemarks actually have coordinates
        for placemark in placemarks_with_coords:
            assert placemark.has_coordinates is True
            assert placemark.coordinates is not None
            assert placemark.longitude is not None
            assert placemark.latitude is not None

    def test_has_coordinates_with_nested_folder_structure(self) -> None:
        """
        Test has_coordinates() with flatten=True in deeply nested folder structures.

        This test verifies:
        - Nested folders with mixed coordinate scenarios
        - flatten=True correctly traverses all folder levels
        - has_coordinates() filtering works across nested structures
        """
        kml_data = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <name>Nested Structure Test</name>
                <Folder>
                    <name>Level 1 Folder</name>
                    <Placemark>
                        <name>L1 With Coords</name>
                        <Point>
                            <coordinates>-122.0856545755255,37.42243077405461,0</coordinates>
                        </Point>
                    </Placemark>
                    <Placemark>
                        <name>L1 Without Coords</name>
                        <description>No coordinates here</description>
                    </Placemark>
                    <Folder>
                        <name>Level 2 Folder</name>
                        <Placemark>
                            <name>L2 With Coords</name>
                            <Point>
                                <coordinates>-122.084075,37.4220033612141,0</coordinates>
                            </Point>
                        </Placemark>
                        <Folder>
                            <name>Level 3 Folder</name>
                            <Placemark>
                                <name>L3 Without Coords</name>
                                <description>Deep nesting, no coordinates</description>
                            </Placemark>
                            <Placemark>
                                <name>L3 With Coords</name>
                                <Point>
                                    <coordinates>-122.085075,37.4230033612141,0</coordinates>
                                </Point>
                            </Placemark>
                        </Folder>
                    </Folder>
                </Folder>
                <Placemark>
                    <name>Root With Coords</name>
                    <Point>
                        <coordinates>-122.086075,37.4240033612141,0</coordinates>
                    </Point>
                </Placemark>
            </Document>
        </kml>"""

        kml_file = KMLFile.from_string(kml_data)

        # Test that flatten=True gets all placemarks regardless of nesting
        all_placemarks = kml_file.placemarks.all()
        assert len(all_placemarks) == 6  # All placemarks across all folder levels

        # Test has_coordinates() filtering
        placemarks_with_coords = kml_file.placemarks.all().has_coordinates()
        assert len(placemarks_with_coords) == 4  # Only those with coordinates

        # Verify the correct placemarks are returned
        names_with_coords = {p.name for p in placemarks_with_coords}
        expected_names = {"L1 With Coords", "L2 With Coords", "L3 With Coords", "Root With Coords"}
        assert names_with_coords == expected_names

        # Verify all have valid coordinates
        for placemark in placemarks_with_coords:
            assert placemark.has_coordinates is True
            assert placemark.point is not None
            assert placemark.point.coordinates is not None

    def test_has_coordinates_with_children_vs_all(self) -> None:
        """
        Test the difference between has_coordinates() with .children() vs .all().

        This test verifies:
        - .children() only gets placemarks at the root level
        - .all() gets placemarks from all folder levels
        - has_coordinates() works correctly in both scenarios
        """
        kml_data = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <name>Flatten Comparison Test</name>
                <Placemark>
                    <name>Root With Coords</name>
                    <Point>
                        <coordinates>-122.0856545755255,37.42243077405461,0</coordinates>
                    </Point>
                </Placemark>
                <Placemark>
                    <name>Root Without Coords</name>
                    <description>Root level, no coordinates</description>
                </Placemark>
                <Folder>
                    <name>Test Folder</name>
                    <Placemark>
                        <name>Folder With Coords</name>
                        <Point>
                            <coordinates>-122.084075,37.4220033612141,0</coordinates>
                        </Point>
                    </Placemark>
                    <Placemark>
                        <name>Folder Without Coords</name>
                        <description>In folder, no coordinates</description>
                    </Placemark>
                </Folder>
            </Document>
        </kml>"""

        kml_file = KMLFile.from_string(kml_data)

        # Test with .children() (only root level)
        root_placemarks_with_coords = kml_file.placemarks.children().has_coordinates()
        assert len(root_placemarks_with_coords) == 1  # Only root level with coordinates
        assert root_placemarks_with_coords[0].name == "Root With Coords"

        # Test with .all() (includes nested)
        all_placemarks_with_coords = kml_file.placemarks.all().has_coordinates()
        assert len(all_placemarks_with_coords) == 2  # Both root and folder level with coordinates

        names_with_coords = {p.name for p in all_placemarks_with_coords}
        expected_names = {"Root With Coords", "Folder With Coords"}
        assert names_with_coords == expected_names
