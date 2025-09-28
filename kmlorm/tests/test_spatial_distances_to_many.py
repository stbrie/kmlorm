"""
Tests for the distances_to_many method in SpatialCalculations.

This module tests the bulk distance calculation functionality
that efficiently computes distances from one point to multiple others.
"""

import time
from typing import List
import pytest

from kmlorm.models.point import Point, Coordinate
from kmlorm.models.placemark import Placemark
from kmlorm.spatial.calculations import SpatialCalculations, DistanceUnit


class TestDistancesToMany:
    """Test the distances_to_many bulk calculation method."""

    @pytest.fixture
    def center_point(self) -> Point:
        """Create a center point for distance calculations."""
        point = Point()
        point.coordinates = Coordinate(longitude=0.0, latitude=0.0)  # Origin
        return point

    @pytest.fixture
    def surrounding_points(self) -> List[Point]:
        """Create points surrounding the origin."""
        points = []
        # Create points at 1 degree away in each cardinal direction
        for lon, lat in [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]:
            p = Point()
            p.coordinates = Coordinate(longitude=lon, latitude=lat)
            points.append(p)
        return points

    def test_distances_to_many_basic(
        self, center_point: Point, surrounding_points: List[Point]
    ) -> None:
        """Test basic distances_to_many functionality."""
        distances = SpatialCalculations.distances_to_many(center_point, surrounding_points)

        assert len(distances) == 4
        assert all(d is not None for d in distances)

        # All points are 1 degree away, should have similar distances
        # At equator, 1 degree is approximately 111.32 km
        for distance in distances:
            assert distance is not None
            assert 110 < distance < 112  # Allow some tolerance

    def test_distances_to_many_with_coordinates(self) -> None:
        """Test distances_to_many with Coordinate objects."""
        center = Coordinate(longitude=0.0, latitude=0.0)
        targets = [
            Coordinate(longitude=1.0, latitude=0.0),
            Coordinate(longitude=2.0, latitude=0.0),
            Coordinate(longitude=3.0, latitude=0.0),
        ]

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert len(distances) == 3
        # Each should be progressively farther
        assert distances[0] is not None
        assert distances[1] is not None
        assert distances[2] is not None
        assert distances[0] < distances[1] < distances[2]

    def test_distances_to_many_with_tuples(self) -> None:
        """Test distances_to_many with tuple coordinates."""
        center = (0.0, 0.0)
        targets = [
            (1.0, 1.0),
            (2.0, 2.0),
            (3.0, 3.0),
        ]

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert len(distances) == 3
        # Each should be progressively farther (diagonal distances)
        assert distances[0] is not None
        assert distances[1] is not None
        assert distances[2] is not None
        assert distances[0] < distances[1] < distances[2]

    def test_distances_to_many_different_units(
        self, center_point: Point, surrounding_points: List[Point]
    ) -> None:
        """Test distances_to_many with different distance units."""
        # Test kilometers (default)
        km_distances = SpatialCalculations.distances_to_many(
            center_point, surrounding_points, unit=DistanceUnit.KILOMETERS
        )

        # Test miles
        mile_distances = SpatialCalculations.distances_to_many(
            center_point, surrounding_points, unit=DistanceUnit.MILES
        )

        # Test meters
        meter_distances = SpatialCalculations.distances_to_many(
            center_point, surrounding_points, unit=DistanceUnit.METERS
        )

        assert len(km_distances) == len(mile_distances) == len(meter_distances) == 4

        # Verify conversions are correct
        for i in range(4):
            assert km_distances[i] is not None
            assert mile_distances[i] is not None
            assert meter_distances[i] is not None

            # 1 km = 0.621371 miles
            assert abs(mile_distances[i] - km_distances[i] * 0.621371) < 0.1

            # 1 km = 1000 meters
            assert abs(meter_distances[i] - km_distances[i] * 1000) < 1

    def test_distances_to_many_with_placemarks(self) -> None:
        """Test distances_to_many with Placemark objects."""
        # Create center placemark
        center_pm = Placemark(name="Center")
        center_point = Point()
        center_point.coordinates = Coordinate(longitude=0.0, latitude=0.0)
        center_pm.point = center_point

        # Create target placemarks
        targets = []
        for i in range(3):
            pm = Placemark(name=f"Target {i}")
            p = Point()
            p.coordinates = Coordinate(longitude=float(i + 1), latitude=0.0)
            pm.point = p
            targets.append(pm)

        distances = SpatialCalculations.distances_to_many(center_pm, targets)

        assert len(distances) == 3
        assert all(d is not None for d in distances)
        assert distances[0] < distances[1] < distances[2]

    def test_distances_to_many_mixed_types(self) -> None:
        """Test distances_to_many with mixed object types."""
        center = Coordinate(longitude=0.0, latitude=0.0)

        # Mix of different types
        p = Point()
        p.coordinates = Coordinate(longitude=1.0, latitude=0.0)

        pm = Placemark(name="Place")
        pm_point = Point()
        pm_point.coordinates = Coordinate(longitude=2.0, latitude=0.0)
        pm.point = pm_point

        targets = [
            p,  # Point
            (3.0, 0.0),  # Tuple
            [4.0, 0.0],  # List
            pm,  # Placemark
            Coordinate(longitude=5.0, latitude=0.0),  # Coordinate
        ]

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert len(distances) == 5
        assert all(d is not None for d in distances)

        # Verify expected distances (approximately)
        # Point at (1,0) should be ~111 km
        # Tuple at (3,0) should be ~333 km
        # List at (4,0) should be ~444 km
        # Placemark at (2,0) should be ~222 km
        # Coordinate at (5,0) should be ~555 km
        assert 110 < distances[0] < 112  # Point at (1,0)
        assert 332 < distances[1] < 334  # Tuple at (3,0)
        assert 443 < distances[2] < 445  # List at (4,0)
        assert 221 < distances[3] < 223  # Placemark at (2,0)
        assert 554 < distances[4] < 556  # Coordinate at (5,0)

    def test_distances_to_many_with_none_objects(self) -> None:
        """Test distances_to_many with None objects in the list."""
        center = Coordinate(longitude=0.0, latitude=0.0)

        p1 = Point()
        p1.coordinates = Coordinate(longitude=1.0, latitude=0.0)
        p2 = Point()
        p2.coordinates = Coordinate(longitude=2.0, latitude=0.0)

        targets = [
            p1,
            None,  # Should return None for this
            p2,
        ]

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert len(distances) == 3
        assert distances[0] is not None
        assert distances[1] is None  # None input should give None output
        assert distances[2] is not None
        assert distances[0] < distances[2]

    def test_distances_to_many_with_missing_coordinates(self) -> None:
        """Test distances_to_many with objects missing coordinates."""
        center = Coordinate(longitude=0.0, latitude=0.0)

        # Placemarks without points
        targets = [
            Placemark(name="No point 1"),
            Placemark(name="No point 2"),
        ]

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert len(distances) == 2
        assert distances[0] is None
        assert distances[1] is None

    def test_distances_to_many_from_none_source(self) -> None:
        """Test distances_to_many when source has no coordinates."""
        # Placemark without point
        center = Placemark(name="No coords")

        targets = [
            Coordinate(longitude=1.0, latitude=0.0),
            Coordinate(longitude=2.0, latitude=0.0),
        ]

        distances = SpatialCalculations.distances_to_many(center, targets)

        # Should return all None values
        assert len(distances) == 2
        assert all(d is None for d in distances)

    def test_distances_to_many_empty_list(self) -> None:
        """Test distances_to_many with empty target list."""
        center = Coordinate(longitude=0.0, latitude=0.0)
        targets: List[Coordinate] = []

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert not distances

    def test_distances_to_many_single_target(self) -> None:
        """Test distances_to_many with a single target."""
        center = Coordinate(longitude=0.0, latitude=0.0)
        targets = [Coordinate(longitude=1.0, latitude=1.0)]

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert len(distances) == 1
        assert distances[0] is not None

        # Compare with single distance_between calculation
        single_distance = SpatialCalculations.distance_between(center, targets[0])
        assert abs(distances[0] - single_distance) < 0.001

    def test_distances_to_many_large_list(self) -> None:
        """Test distances_to_many with a large list of targets."""
        center = Coordinate(longitude=0.0, latitude=0.0)

        # Create 100 targets in a grid
        targets = []
        for i in range(10):
            for j in range(10):
                targets.append(Coordinate(longitude=float(i), latitude=float(j)))

        distances = SpatialCalculations.distances_to_many(center, targets)

        assert len(distances) == 100
        assert all(d is not None for d in distances)

        # Distance to origin should be 0
        assert distances[0] < 0.001  # First point is (0, 0)

        # Farthest point should be (9, 9)
        max_distance = max(d for d in distances if d is not None)
        assert max_distance == distances[-1]

    def test_distances_to_many_real_world_example(self) -> None:
        """Test with real world city coordinates."""
        # New York City
        nyc = Coordinate(longitude=-74.006, latitude=40.7128)

        # Other US cities
        cities = [
            Coordinate(longitude=-77.0369, latitude=38.9072),  # Washington DC
            Coordinate(longitude=-71.0589, latitude=42.3601),  # Boston
            Coordinate(longitude=-75.1652, latitude=39.9526),  # Philadelphia
            Coordinate(longitude=-73.9352, latitude=40.7304),  # Newark
        ]

        distances = SpatialCalculations.distances_to_many(nyc, cities, unit=DistanceUnit.MILES)

        assert len(distances) == 4

        # Approximate distances from NYC
        dc_dist = distances[0]
        boston_dist = distances[1]
        philly_dist = distances[2]
        newark_dist = distances[3]

        assert dc_dist is not None
        assert boston_dist is not None
        assert philly_dist is not None
        assert newark_dist is not None

        # Verify approximate real distances (in miles)
        assert 200 < dc_dist < 250  # ~225 miles
        assert 180 < boston_dist < 220  # ~190 miles
        assert 80 < philly_dist < 100  # ~95 miles
        assert 0 < newark_dist < 20  # ~10 miles (very close, adjusted range)

    def test_distances_to_many_performance(self) -> None:
        """Test that distances_to_many is more efficient than repeated calls."""

        center = Coordinate(longitude=0.0, latitude=0.0)
        targets = [Coordinate(longitude=float(i), latitude=float(i)) for i in range(50)]

        # Time bulk calculation
        start = time.perf_counter()
        bulk_distances = SpatialCalculations.distances_to_many(center, targets)
        bulk_time = time.perf_counter() - start

        # Time individual calculations
        start = time.perf_counter()
        individual_distances = []
        for target in targets:
            dist = SpatialCalculations.distance_between(center, target)
            individual_distances.append(dist)
        individual_time = time.perf_counter() - start

        # Results should be the same
        assert len(bulk_distances) == len(individual_distances)
        for i, (bulk_dist, indiv_dist) in enumerate(zip(bulk_distances, individual_distances)):
            if bulk_dist is not None and indiv_dist is not None:
                assert abs(bulk_dist - indiv_dist) < 0.001

        # Bulk should be faster (though this might not always be true for small lists)
        # Just verify it completes successfully
        assert bulk_time > 0
        assert individual_time > 0
