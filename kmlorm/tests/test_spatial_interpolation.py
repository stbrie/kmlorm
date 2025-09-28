"""
Tests for spatial interpolation and bounding box calculations.

This module tests the interpolate method and other spatial calculation features
that were previously uncovered.
"""

from typing import Tuple
import pytest


from kmlorm.models.point import Point, Coordinate
from kmlorm.models.placemark import Placemark
from kmlorm.spatial.calculations import SpatialCalculations


class TestSpatialInterpolation:
    """Test the interpolate method of SpatialCalculations."""

    @pytest.fixture
    def sample_points(self) -> Tuple[Point, Point]:
        """Create sample points for interpolation tests."""
        # San Francisco to New York
        sf = Point()
        sf.coordinates = Coordinate(longitude=-122.4194, latitude=37.7749, altitude=0)
        ny = Point()
        ny.coordinates = Coordinate(longitude=-74.0060, latitude=40.7128, altitude=0)
        return sf, ny

    @pytest.fixture
    def sample_coordinates(self) -> Tuple[Coordinate, Coordinate]:
        """Create sample coordinates for interpolation tests."""
        start = Coordinate(longitude=0.0, latitude=0.0)
        end = Coordinate(longitude=90.0, latitude=0.0)
        return start, end

    def test_interpolate_midpoint(self, sample_points: Tuple[Point, Point]) -> None:
        """Test interpolation at midpoint (fraction=0.5)."""
        sf, ny = sample_points

        midpoint = SpatialCalculations.interpolate(sf, ny, 0.5)
        assert midpoint is not None
        assert isinstance(midpoint, Coordinate)

        # Midpoint should be roughly in the middle of the US
        assert -110 < midpoint.longitude < -85  # Somewhere in central US
        assert 35 < midpoint.latitude < 42  # Between SF and NY latitudes

    def test_interpolate_start_point(self, sample_points: Tuple[Point, Point]) -> None:
        """Test interpolation at start (fraction=0.0)."""
        sf, ny = sample_points

        result = SpatialCalculations.interpolate(sf, ny, 0.0)
        assert result is not None
        assert sf is not None
        assert sf.coordinates is not None
        assert abs(result.longitude - sf.coordinates.longitude) < 0.001
        assert abs(result.latitude - sf.coordinates.latitude) < 0.001

    def test_interpolate_end_point(self, sample_points: Tuple[Point, Point]) -> None:
        """Test interpolation at end (fraction=1.0)."""
        sf, ny = sample_points

        result = SpatialCalculations.interpolate(sf, ny, 1.0)
        assert result is not None
        assert ny is not None
        assert ny.coordinates is not None
        assert abs(result.longitude - ny.coordinates.longitude) < 0.001
        assert abs(result.latitude - ny.coordinates.latitude) < 0.001

    def test_interpolate_quarter_points(self, sample_points: Tuple[Point, Point]) -> None:
        """Test interpolation at quarter points."""
        sf, ny = sample_points

        # Test 25% point
        quarter = SpatialCalculations.interpolate(sf, ny, 0.25)
        assert quarter is not None
        # Should be closer to SF than NY
        dist_to_sf = SpatialCalculations.distance_between(quarter, sf)
        dist_to_ny = SpatialCalculations.distance_between(quarter, ny)
        assert dist_to_sf < dist_to_ny

        # Test 75% point
        three_quarter = SpatialCalculations.interpolate(sf, ny, 0.75)
        assert three_quarter is not None
        # Should be closer to NY than SF
        dist_to_sf = SpatialCalculations.distance_between(three_quarter, sf)
        dist_to_ny = SpatialCalculations.distance_between(three_quarter, ny)
        assert dist_to_ny < dist_to_sf

    def test_interpolate_with_coordinates(
        self, sample_coordinates: Tuple[Coordinate, Coordinate]
    ) -> None:
        """Test interpolation with Coordinate objects."""
        start, end = sample_coordinates

        # Test various fractions
        for fraction in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = SpatialCalculations.interpolate(start, end, fraction)
            assert result is not None
            assert isinstance(result, Coordinate)

            # Longitude should increase linearly for equator points
            expected_lon = start.longitude + (end.longitude - start.longitude) * fraction
            # Allow some tolerance for spherical calculation
            assert abs(result.longitude - expected_lon) < 1.0

    def test_interpolate_same_point(self) -> None:
        """Test interpolation when start and end are the same."""
        point = Point()
        point.coordinates = Coordinate(longitude=10.0, latitude=20.0)

        result = SpatialCalculations.interpolate(point, point, 0.5)
        assert result is not None
        assert abs(result.longitude - 10.0) < 0.001
        assert abs(result.latitude - 20.0) < 0.001

    def test_interpolate_antipodal_points(self) -> None:
        """Test interpolation between antipodal points."""
        # North pole to South pole
        north = Coordinate(longitude=0.0, latitude=89.9)  # Near north pole
        south = Coordinate(longitude=180.0, latitude=-89.9)  # Near south pole

        midpoint = SpatialCalculations.interpolate(north, south, 0.5)
        assert midpoint is not None
        # Midpoint should be near the equator
        assert abs(midpoint.latitude) < 5.0

    def test_interpolate_across_dateline(self) -> None:
        """Test interpolation across the international date line."""
        # Tokyo to San Francisco (crosses Pacific)
        tokyo = Coordinate(longitude=139.6917, latitude=35.6895)
        sf = Coordinate(longitude=-122.4194, latitude=37.7749)

        midpoint = SpatialCalculations.interpolate(tokyo, sf, 0.5)
        assert midpoint is not None
        # Midpoint should be in the Pacific
        assert midpoint.longitude < -150 or midpoint.longitude > 150

    def test_interpolate_invalid_fraction(self, sample_points: Tuple[Point, Point]) -> None:
        """Test interpolation with invalid fractions."""
        sf, ny = sample_points

        # Test fraction < 0
        with pytest.raises(ValueError, match="Fraction must be between 0 and 1"):
            SpatialCalculations.interpolate(sf, ny, -0.1)

        # Test fraction > 1
        with pytest.raises(ValueError, match="Fraction must be between 0 and 1"):
            SpatialCalculations.interpolate(sf, ny, 1.5)

    def test_interpolate_with_tuples(self) -> None:
        """Test interpolation with tuple coordinates."""
        start = (-122.4194, 37.7749)  # SF
        end = (-74.0060, 40.7128)  # NY

        midpoint = SpatialCalculations.interpolate(start, end, 0.5)
        assert midpoint is not None
        assert isinstance(midpoint, Coordinate)
        assert -110 < midpoint.longitude < -85

    def test_interpolate_with_lists(self) -> None:
        """Test interpolation with list coordinates."""
        start = [0.0, 0.0]
        end = [10.0, 10.0]

        result = SpatialCalculations.interpolate(start, end, 0.5)
        assert result is not None
        assert 4 < result.longitude < 6
        assert 4 < result.latitude < 6

    def test_interpolate_with_placemarks(self) -> None:
        """Test interpolation with Placemark objects."""
        pm1 = Placemark(name="Start")
        p = Point()
        p.coordinates = Coordinate(longitude=0.0, latitude=0.0)
        pm1.point = p

        pm2 = Placemark(name="End")
        p = Point()
        p.coordinates = Coordinate(longitude=45.0, latitude=45.0)
        pm2.point = p

        result = SpatialCalculations.interpolate(pm1, pm2, 0.5)
        assert result is not None
        # Great circle midpoint may not be exactly at (22.5, 22.5)
        # Just check it's between the two points
        assert 0 <= result.longitude <= 45
        assert 0 <= result.latitude <= 45

    def test_interpolate_missing_coordinates(self) -> None:
        """Test interpolation with objects missing coordinates."""
        pm1 = Placemark(name="No coords")
        pm2 = Placemark(name="Also no coords")

        result = SpatialCalculations.interpolate(pm1, pm2, 0.5)
        assert result is None

    def test_interpolate_one_missing_coordinate(self, sample_points: Tuple[Point, Point]) -> None:
        """Test interpolation when one object has missing coordinates."""
        sf, _ = sample_points
        pm_no_coords = Placemark(name="No coords")

        result = SpatialCalculations.interpolate(sf, pm_no_coords, 0.5)
        assert result is None

        result = SpatialCalculations.interpolate(pm_no_coords, sf, 0.5)
        assert result is None

    def test_interpolate_multiple_steps(
        self, sample_coordinates: Tuple[Coordinate, Coordinate]
    ) -> None:
        """Test creating multiple interpolation points along a path."""
        start, end = sample_coordinates

        # Create 10 points along the path
        points = []
        for i in range(11):
            fraction = i / 10.0
            point = SpatialCalculations.interpolate(start, end, fraction)
            assert point is not None
            points.append(point)

        # Check that points are in order
        for i in range(len(points) - 1):
            assert points[i].longitude <= points[i + 1].longitude

    def test_interpolate_preserves_great_circle(self) -> None:
        """Test that interpolation follows the great circle path."""
        # London to Tokyo
        london = Coordinate(longitude=-0.1276, latitude=51.5074)
        tokyo = Coordinate(longitude=139.6917, latitude=35.6895)

        # Get multiple points along the path
        points = []
        for i in range(11):
            fraction = i / 10.0
            point = SpatialCalculations.interpolate(london, tokyo, fraction)
            assert point is not None
            points.append(point)

        # The great circle path from London to Tokyo goes north through Russia
        # The middle points should have higher latitudes than both endpoints
        max_lat = max(p.latitude for p in points[1:-1])
        assert max_lat > london.latitude
        assert max_lat > tokyo.latitude


class TestBoundingBox:
    """Test the bounding_box method."""

    def test_bounding_box_single_point(self) -> None:
        """Test bounding box for a single point."""
        point = Point()
        point.coordinates = Coordinate(longitude=10.0, latitude=20.0)
        bbox = SpatialCalculations.bounding_box([point])

        assert bbox is not None
        min_lon, min_lat, max_lon, max_lat = bbox
        assert min_lon == 10.0
        assert max_lon == 10.0
        assert min_lat == 20.0
        assert max_lat == 20.0

    def test_bounding_box_multiple_points(self) -> None:
        """Test bounding box for multiple points."""
        point1 = Point()
        point1.coordinates = Coordinate(longitude=0.0, latitude=0.0)
        point2 = Point()
        point2.coordinates = Coordinate(longitude=10.0, latitude=5.0)
        point3 = Point()
        point3.coordinates = Coordinate(longitude=-5.0, latitude=15.0)
        point4 = Point()
        point4.coordinates = Coordinate(longitude=7.0, latitude=-10.0)
        points = [point1, point2, point3, point4]

        bbox = SpatialCalculations.bounding_box(points)
        assert bbox is not None
        min_lon, min_lat, max_lon, max_lat = bbox

        assert min_lon == -5.0
        assert max_lon == 10.0
        assert min_lat == -10.0
        assert max_lat == 15.0

    def test_bounding_box_with_placemarks(self) -> None:
        """Test bounding box with Placemark objects."""
        placemarks = []
        for i in range(3):
            pm = Placemark(name=f"Place {i}")
            p = Point()
            p.coordinates = Coordinate(longitude=float(i * 10), latitude=float(i * 5))
            pm.point = p
            placemarks.append(pm)

        bbox = SpatialCalculations.bounding_box(placemarks)
        assert bbox is not None
        min_lon, min_lat, max_lon, max_lat = bbox

        assert min_lon == 0.0
        assert max_lon == 20.0
        assert min_lat == 0.0
        assert max_lat == 10.0

    def test_bounding_box_mixed_objects(self) -> None:
        """Test bounding box with mixed object types."""
        point = Point()
        point.coordinates = Coordinate(longitude=0.0, latitude=0.0)
        objects = [
            point,
            Coordinate(longitude=10.0, latitude=10.0),
            (-5.0, -5.0),  # Tuple
            [15.0, 15.0],  # List
        ]

        bbox = SpatialCalculations.bounding_box(objects)
        assert bbox is not None
        min_lon, min_lat, max_lon, max_lat = bbox

        assert min_lon == -5.0
        assert max_lon == 15.0
        assert min_lat == -5.0
        assert max_lat == 15.0

    def test_bounding_box_empty_list(self) -> None:
        """Test bounding box with empty list."""
        bbox = SpatialCalculations.bounding_box([])
        assert bbox is None

    def test_bounding_box_no_valid_coordinates(self) -> None:
        """Test bounding box with objects having no valid coordinates."""
        placemarks = [
            Placemark(name="No coords 1"),
            Placemark(name="No coords 2"),
        ]

        bbox = SpatialCalculations.bounding_box(placemarks)
        assert bbox is None

    def test_bounding_box_some_invalid_coordinates(self) -> None:
        """Test bounding box with mix of valid and invalid coordinates."""
        point = Point()
        point.coordinates = Coordinate(longitude=5.0, latitude=5.0)
        objects = [
            point,
            Placemark(name="No coords"),  # Invalid
            Point(),
            Coordinate(longitude=15.0, latitude=15.0),
        ]

        bbox = SpatialCalculations.bounding_box(objects)
        assert bbox is not None
        min_lon, min_lat, max_lon, max_lat = bbox

        # Should only consider valid points
        assert min_lon == 5.0
        assert max_lon == 15.0
        assert min_lat == 5.0
        assert max_lat == 15.0

    def test_bounding_box_crossing_dateline(self) -> None:
        """Test bounding box for points crossing the date line."""
        point1 = Point()
        point1.coordinates = Coordinate(longitude=170.0, latitude=0.0)
        point2 = Point()
        point2.coordinates = Coordinate(longitude=-170.0, latitude=0.0)
        point3 = Point()
        point3.coordinates = Coordinate(longitude=180.0, latitude=10.0)
        point4 = Point()
        point4.coordinates = Coordinate(longitude=-180.0, latitude=-10.0)
        points = [point1, point2, point3, point4]

        bbox = SpatialCalculations.bounding_box(points)
        assert bbox is not None
        min_lon, min_lat, max_lon, max_lat = bbox

        # The bounding box calculation doesn't handle date line specially
        # So we get the raw min/max values
        assert min_lon == -180.0
        assert max_lon == 180.0
        assert min_lat == -10.0
        assert max_lat == 10.0

    def test_bounding_box_global_coverage(self) -> None:
        """Test bounding box with global point coverage."""
        point1 = Point()
        point1.coordinates = Coordinate(longitude=-180.0, latitude=-90.0)
        point2 = Point()
        point2.coordinates = Coordinate(longitude=180.0, latitude=90.0)
        point3 = Point()
        point3.coordinates = Coordinate(longitude=0.0, latitude=0.0)
        points = [point1, point2, point3]

        bbox = SpatialCalculations.bounding_box(points)
        assert bbox is not None
        min_lon, min_lat, max_lon, max_lat = bbox

        assert min_lon == -180.0
        assert max_lon == 180.0
        assert min_lat == -90.0
        assert max_lat == 90.0


class TestSpatialCalculationsEdgeCases:
    """Test edge cases and error handling in spatial calculations."""

    def test_interpolate_with_None_objects(self) -> None:  # pylint: disable=invalid-name
        """Test interpolation with None objects."""
        point = Point()
        point.coordinates = Coordinate(longitude=0.0, latitude=0.0)

        result = SpatialCalculations.interpolate(None, point, 0.5)
        assert result is None

        result = SpatialCalculations.interpolate(point, None, 0.5)
        assert result is None

        result = SpatialCalculations.interpolate(None, None, 0.5)
        assert result is None

    def test_interpolate_with_invalid_coordinates(self) -> None:
        """Test interpolation with invalid coordinate values."""
        # This should handle invalid coordinates gracefully
        # Currently the function returns None for invalid inputs rather than raising
        valid_point = Point()
        valid_point.coordinates = Coordinate(longitude=10.0, latitude=20.0)
        invalid_point = None

        result = SpatialCalculations.interpolate(invalid_point, valid_point, 0.5)
        assert result is None

    def test_bounding_box_with_None(self) -> None:  # pylint:disable=invalid-name
        """Test bounding box calculation with None in list."""
        point1 = Point()
        point1.coordinates = Coordinate(longitude=10.0, latitude=10.0)
        point2 = Point()
        point2.coordinates = Coordinate(longitude=0.0, latitude=0.0)
        objects = [point1, None, point2]

        bbox = SpatialCalculations.bounding_box(objects)
        assert bbox is not None
        min_lon, _min_lat, max_lon, _max_lat = bbox
        assert min_lon == 0.0
        assert max_lon == 10.0

    def test_interpolate_precision(self) -> None:
        """Test interpolation maintains reasonable precision."""
        start = Coordinate(longitude=0.123456789, latitude=0.987654321)
        end = Coordinate(longitude=1.123456789, latitude=1.987654321)

        result = SpatialCalculations.interpolate(start, end, 0.5)
        assert result is not None
        # pylint: disable=use-maxsplit-arg
        # Check that we maintain at least 6 decimal places of precision
        assert len(str(result.longitude).split(".")[-1]) >= 6
        assert len(str(result.latitude).split(".")[-1]) >= 6
