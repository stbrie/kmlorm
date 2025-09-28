"""
Test spatial calculations with known distances and comprehensive coverage.

This module provides comprehensive testing of the spatial calculations system,
including known distance validation, property-based testing, and unit conversions.
"""

from typing import Tuple
import pytest


from kmlorm.spatial.calculations import SpatialCalculations, DistanceUnit
from kmlorm.models.point import Coordinate, Point
from kmlorm.models.placemark import Placemark


class TestSpatialCalculations:
    """Test spatial calculation accuracy and core functionality."""

    # Known distances for validation (coord1, coord2, expected_km, tolerance_km)
    KNOWN_DISTANCES = [
        # Major city pairs with well-known distances
        ((-74.006, 40.7128), (-0.1276, 51.5074), 5567, 10),  # NYC to London
        ((139.6917, 35.6895), (-122.4194, 37.7749), 8280, 10),  # Tokyo to San Francisco
        ((2.3522, 48.8566), (-87.6298, 41.8781), 6650, 20),  # Paris to Chicago
        ((-43.1729, -22.9068), (151.2093, -33.8688), 13520, 30),  # Rio to Sydney
        # Special cases
        ((0, 0), (0, 0), 0, 0),  # Same point
        ((0, 0), (1, 0), 111.32, 1),  # 1 degree longitude at equator
        ((0, 0), (0, 1), 111.32, 1),  # 1 degree latitude
        ((0, 0), (180, 0), 20037.5, 50),  # Half circumference at equator
        ((0, 90), (0, -90), 20003.9, 50),  # Pole to pole
        # Date line crossing
        ((179, 0), (-179, 0), 222.64, 5),  # Should be small, not half circumference
        # High latitude cases
        ((0, 89), (1, 89), 1.95, 0.5),  # Near north pole
        ((0, -89), (1, -89), 1.95, 0.5),  # Near south pole
    ]

    @pytest.mark.parametrize("coord1,coord2,expected_km,tolerance", KNOWN_DISTANCES)
    def test_known_distances_coordinate_objects(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float],
        expected_km: float,
        tolerance: float,
    ) -> None:
        """Test distance calculations against known values using Coordinate objects."""
        c1 = Coordinate(longitude=coord1[0], latitude=coord1[1])
        c2 = Coordinate(longitude=coord2[0], latitude=coord2[1])

        distance = SpatialCalculations.distance_between(c1, c2)
        assert distance is not None
        assert abs(distance - expected_km) <= tolerance, (
            f"Distance {distance:.2f}km between {coord1} and {coord2} "
            f"should be {expected_km}±{tolerance}km"
        )

    @pytest.mark.parametrize("coord1,coord2,expected_km,tolerance", KNOWN_DISTANCES)
    def test_known_distances_point_objects(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float],
        expected_km: float,
        tolerance: float,
    ) -> None:
        """Test distance calculations using Point objects."""
        p1 = Point(coordinates=coord1)
        p2 = Point(coordinates=coord2)

        distance = SpatialCalculations.distance_between(p1, p2)
        assert distance is not None
        assert abs(distance - expected_km) <= tolerance

    @pytest.mark.parametrize("coord1,coord2,expected_km,tolerance", KNOWN_DISTANCES)
    def test_known_distances_placemark_objects(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float],
        expected_km: float,
        tolerance: float,
    ) -> None:
        """Test distance calculations using Placemark objects."""
        pm1 = Placemark(name="Point1", coordinates=coord1)
        pm2 = Placemark(name="Point2", coordinates=coord2)

        distance = SpatialCalculations.distance_between(pm1, pm2)
        assert distance is not None
        assert abs(distance - expected_km) <= tolerance

    def test_distance_symmetry(self) -> None:
        """Test that distance calculations are symmetric."""
        coords = [
            Coordinate(longitude=0, latitude=0),
            Coordinate(longitude=1, latitude=1),
            Coordinate(longitude=-74.006, latitude=40.7128),  # NYC
            Coordinate(longitude=139.6917, latitude=35.6895),  # Tokyo
        ]

        for i, c1 in enumerate(coords):
            for _, c2 in enumerate(coords[i + 1 :], i + 1):  # noqa: E203
                d1 = SpatialCalculations.distance_between(c1, c2)
                d2 = SpatialCalculations.distance_between(c2, c1)
                assert d1 == pytest.approx(
                    d2, rel=1e-10
                ), f"Distance should be symmetric: {d1} != {d2}"

    def test_distance_to_self(self) -> None:
        """Test that distance to self is zero."""
        coords = [
            Coordinate(longitude=0, latitude=0),
            Coordinate(longitude=-180, latitude=-90),
            Coordinate(longitude=180, latitude=90),
            Coordinate(longitude=-74.006, latitude=40.7128),
        ]

        for coord in coords:
            distance = SpatialCalculations.distance_between(coord, coord)
            assert distance == pytest.approx(0, abs=0.001)

    def test_unit_conversions(self) -> None:
        """Test distance unit conversions."""
        c1 = Coordinate(longitude=0, latitude=0)
        c2 = Coordinate(longitude=1, latitude=0)  # ~111.32 km

        # Test all supported units
        km = SpatialCalculations.distance_between(c1, c2, DistanceUnit.KILOMETERS)
        m = SpatialCalculations.distance_between(c1, c2, DistanceUnit.METERS)
        miles = SpatialCalculations.distance_between(c1, c2, DistanceUnit.MILES)
        nm = SpatialCalculations.distance_between(c1, c2, DistanceUnit.NAUTICAL_MILES)
        feet = SpatialCalculations.distance_between(c1, c2, DistanceUnit.FEET)
        yards = SpatialCalculations.distance_between(c1, c2, DistanceUnit.YARDS)

        assert km is not None and m is not None
        assert m == pytest.approx(km * 1000, rel=1e-6)
        assert miles == pytest.approx(km * 0.621371, rel=1e-4)
        assert nm == pytest.approx(km * 0.539957, rel=1e-4)
        assert feet == pytest.approx(km * 3280.84, rel=1e-4)
        assert yards == pytest.approx(km * 1093.61, rel=1e-4)

    def test_mixed_object_types(self) -> None:
        """Test distance calculations between different object types."""
        coord = Coordinate(longitude=0, latitude=0)
        point = Point(coordinates=(1, 0))
        placemark = Placemark(name="Test", coordinates=(2, 0))

        # All combinations should work
        d1 = SpatialCalculations.distance_between(coord, point)
        d2 = SpatialCalculations.distance_between(point, placemark)
        d3 = SpatialCalculations.distance_between(coord, placemark)

        assert all(d is not None for d in [d1, d2, d3])
        assert d1 == pytest.approx(111.32, rel=0.01)
        assert d2 == pytest.approx(111.32, rel=0.01)
        assert d3 == pytest.approx(222.64, rel=0.01)

    def test_bearing_calculations(self) -> None:
        """Test bearing calculations with known values."""
        # Due east should be 90 degrees
        c1 = Coordinate(longitude=0, latitude=0)
        c2 = Coordinate(longitude=1, latitude=0)
        bearing = SpatialCalculations.bearing_between(c1, c2)
        assert bearing == pytest.approx(90, abs=0.1)

        # Due north should be 0 degrees
        c3 = Coordinate(longitude=0, latitude=1)
        bearing = SpatialCalculations.bearing_between(c1, c3)
        assert bearing == pytest.approx(0, abs=0.1)

        # Due west should be 270 degrees
        c4 = Coordinate(longitude=-1, latitude=0)
        bearing = SpatialCalculations.bearing_between(c1, c4)
        assert bearing == pytest.approx(270, abs=0.1)

        # Due south should be 180 degrees
        c5 = Coordinate(longitude=0, latitude=-1)
        bearing = SpatialCalculations.bearing_between(c1, c5)
        assert bearing == pytest.approx(180, abs=0.1)

    def test_midpoint_calculations(self) -> None:
        """Test midpoint calculations."""
        # Midpoint of equator crossing
        c1 = Coordinate(longitude=0, latitude=0)
        c2 = Coordinate(longitude=2, latitude=0)
        midpoint = SpatialCalculations.midpoint(c1, c2)

        assert midpoint is not None
        assert midpoint.longitude == pytest.approx(1, abs=0.001)
        assert midpoint.latitude == pytest.approx(0, abs=0.001)

        # Midpoint of meridian crossing
        c1 = Coordinate(longitude=0, latitude=0)
        c2 = Coordinate(longitude=0, latitude=2)
        midpoint = SpatialCalculations.midpoint(c1, c2)

        assert midpoint is not None
        assert midpoint.longitude == pytest.approx(0, abs=0.001)
        assert midpoint.latitude == pytest.approx(1, abs=0.001)

    def test_distances_to_many(self) -> None:
        """Test bulk distance calculations."""
        center = Coordinate(longitude=0, latitude=0)
        targets = [
            Coordinate(longitude=1, latitude=0),
            Coordinate(longitude=0, latitude=1),
            Coordinate(longitude=1, latitude=1),
            Point(coordinates=(2, 0)),
            Placemark(name="Test", coordinates=(0, 2)),
        ]

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert len(distances) == len(targets)
        assert all(d is not None for d in distances)

        # Verify individual distances match bulk calculation
        for i, target in enumerate(targets):
            individual = SpatialCalculations.distance_between(center, target)
            assert distances[i] == pytest.approx(individual, rel=1e-10)

    def test_none_coordinates(self) -> None:
        """Test handling of objects with no coordinates."""
        coord = Coordinate(longitude=0, latitude=0)
        point_no_coords = Point()  # No coordinates set

        distance = SpatialCalculations.distance_between(coord, point_no_coords)
        assert distance is None

        distance = SpatialCalculations.distance_between(point_no_coords, coord)
        assert distance is None

    def test_invalid_coordinate_handling(self) -> None:
        """Test handling of invalid coordinate inputs."""

        # Mock objects that don't implement HasCoordinates properly
        # pylint: disable=too-few-public-methods
        class InvalidObject:
            """
            A class representing an invalid spatial object.

            This class is intended for testing purposes and does not provide valid coordinates.
            The `get_coordinates` method always returns None, simulating an object without
            spatial data.
            """

            def get_coordinates(self) -> None:
                """
                Returns the coordinates associated with the object.

                Currently, this method returns None. Override this method to provide actual
                coordinate retrieval logic.

                Returns:
                    None
                """
                return None

        coord = Coordinate(longitude=0, latitude=0)
        invalid = InvalidObject()

        distance = SpatialCalculations.distance_between(coord, invalid)
        assert distance is None

    def test_convenience_methods_coordinate(self) -> None:
        """Test convenience methods on Coordinate objects."""
        c1 = Coordinate(longitude=0, latitude=0)
        c2 = Coordinate(longitude=1, latitude=0)

        # Test distance_to convenience method
        distance = c1.distance_to(c2)
        expected = SpatialCalculations.distance_between(c1, c2)
        assert distance == expected

        # Test bearing_to convenience method
        bearing = c1.bearing_to(c2)
        expected_bearing = SpatialCalculations.bearing_between(c1, c2)
        assert bearing == expected_bearing

        # Test midpoint_to convenience method
        midpoint = c1.midpoint_to(c2)
        expected_midpoint = SpatialCalculations.midpoint(c1, c2)
        assert midpoint == expected_midpoint

    def test_convenience_methods_point(self) -> None:
        """Test convenience methods on Point objects."""
        p1 = Point(coordinates=(0, 0))
        p2 = Point(coordinates=(1, 0))

        distance = p1.distance_to(p2)
        expected = SpatialCalculations.distance_between(p1, p2)
        assert distance == expected

        bearing = p1.bearing_to(p2)
        expected_bearing = SpatialCalculations.bearing_between(p1, p2)
        assert bearing == expected_bearing

    def test_convenience_methods_placemark(self) -> None:
        """Test convenience methods on Placemark objects."""
        pm1 = Placemark(name="Start", coordinates=(0, 0))
        pm2 = Placemark(name="End", coordinates=(1, 0))

        distance = pm1.distance_to(pm2)
        expected = SpatialCalculations.distance_between(pm1, pm2)
        assert distance == expected

        bearing = pm1.bearing_to(pm2)
        expected_bearing = SpatialCalculations.bearing_between(pm1, pm2)
        assert bearing == expected_bearing

    def test_coordinate_tuple_support(self) -> None:
        """Test that coordinate methods accept tuple inputs."""
        c1 = Coordinate(longitude=0, latitude=0)

        # Test distance to tuple
        distance = c1.distance_to((1, 0))
        assert distance is not None
        assert distance == pytest.approx(111.32, rel=0.01)

        # Test bearing to tuple
        bearing = c1.bearing_to((1, 0))
        assert bearing == pytest.approx(90, abs=0.1)

        # Test midpoint to tuple
        midpoint = c1.midpoint_to((2, 0))
        assert midpoint is not None
        assert midpoint.longitude == pytest.approx(1, abs=0.001)

    def test_coordinate_list_support(self) -> None:
        """Test that coordinate methods accept list inputs."""
        c1 = Coordinate(longitude=0, latitude=0)

        # Test distance to list
        distance = c1.distance_to([1, 0])
        assert distance is not None
        assert distance == pytest.approx(111.32, rel=0.01)

        # Test bearing to list
        bearing = c1.bearing_to([1, 0])
        assert bearing == pytest.approx(90, abs=0.1)
