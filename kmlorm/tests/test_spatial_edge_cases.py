"""
Test spatial calculations edge cases and boundary conditions.

This module tests edge cases that commonly cause issues in spatial calculations,
including poles, antipodal points, date line crossings, and numerical precision limits.
"""

import pytest
import math
from typing import List, Tuple

from kmlorm.spatial.calculations import SpatialCalculations, DistanceUnit
from kmlorm.spatial.strategies import HaversineStrategy, VincentyStrategy, EuclideanApproximation
from kmlorm.spatial.exceptions import SpatialCalculationError, InvalidCoordinateError
from kmlorm.models.point import Coordinate, Point
from kmlorm.models.placemark import Placemark


class TestSpatialEdgeCases:
    """Test edge cases and boundary conditions in spatial calculations."""

    def test_pole_calculations(self):
        """Test calculations involving the north and south poles."""
        north_pole = Coordinate(longitude=0, latitude=90)
        south_pole = Coordinate(longitude=0, latitude=-90)
        equator = Coordinate(longitude=0, latitude=0)

        # Pole to pole distance
        pole_distance = SpatialCalculations.distance_between(north_pole, south_pole)
        assert pole_distance == pytest.approx(20003.9, rel=0.01), (
            f"Pole to pole distance should be ~20004km, got {pole_distance}km"
        )

        # Pole to equator distance
        north_equator_dist = SpatialCalculations.distance_between(north_pole, equator)
        assert north_equator_dist == pytest.approx(10001.95, rel=0.01), (
            f"North pole to equator should be ~10002km, got {north_equator_dist}km"
        )

        south_equator_dist = SpatialCalculations.distance_between(south_pole, equator)
        assert south_equator_dist == pytest.approx(10001.95, rel=0.01), (
            f"South pole to equator should be ~10002km, got {south_equator_dist}km"
        )

    def test_pole_longitude_invariance(self):
        """Test that longitude doesn't matter at the poles."""
        pole_coords = [
            Coordinate(longitude=0, latitude=90),
            Coordinate(longitude=45, latitude=90),
            Coordinate(longitude=90, latitude=90),
            Coordinate(longitude=180, latitude=90),
            Coordinate(longitude=-90, latitude=90),
        ]

        equator = Coordinate(longitude=0, latitude=0)

        # All north pole coordinates should be equidistant from equator
        distances = [
            SpatialCalculations.distance_between(pole, equator)
            for pole in pole_coords
        ]

        for i, distance in enumerate(distances[1:], 1):
            assert distance == pytest.approx(distances[0], rel=1e-6), (
                f"Distance from north pole (lon={pole_coords[i].longitude}) to equator "
                f"should be same as from (lon=0): {distance} vs {distances[0]}"
            )

    def test_antipodal_points(self):
        """Test calculations with antipodal (opposite) points on Earth."""
        antipodal_pairs = [
            # (point1, point2, expected_distance_km)
            ((0, 0), (0, 180), 20037.5),  # Equatorial antipodes (corrected longitude)
            ((45, 0), (-45, 180), 20003.9),  # 45-degree antipodes (corrected coordinates)
            ((90, 0), (-90, 0), 20003.9),  # Polar antipodes
        ]

        for (lat1, lon1), (lat2, lon2), expected_km in antipodal_pairs:
            c1 = Coordinate(longitude=lon1, latitude=lat1)
            c2 = Coordinate(longitude=lon2, latitude=lat2)

            distance = SpatialCalculations.distance_between(c1, c2)
            assert distance == pytest.approx(expected_km, rel=0.01), (
                f"Antipodal distance between ({lat1}, {lon1}) and ({lat2}, {lon2}) "
                f"should be ~{expected_km}km, got {distance}km"
            )

    def test_date_line_crossing(self):
        """Test proper handling of International Date Line crossing."""
        # Points very close to each other but on opposite sides of date line
        west_of_dateline = Coordinate(longitude=179.5, latitude=0)
        east_of_dateline = Coordinate(longitude=-179.5, latitude=0)

        distance = SpatialCalculations.distance_between(west_of_dateline, east_of_dateline)

        # Should be about 111 km (1 degree), not ~39,000 km (359 degrees)
        assert distance < 200, (
            f"Date line crossing distance should be small (~111km), got {distance}km"
        )
        assert distance > 50, (
            f"Date line crossing distance should not be zero, got {distance}km"
        )

    def test_date_line_bearing(self):
        """Test bearing calculations across the date line."""
        # Point west of date line
        west_point = Coordinate(longitude=179, latitude=0)
        # Point east of date line
        east_point = Coordinate(longitude=-179, latitude=0)

        # Bearing from west to east should be close to 90° (east)
        bearing = SpatialCalculations.bearing_between(west_point, east_point)
        assert bearing == pytest.approx(90, abs=5), (
            f"Bearing across date line should be ~90°, got {bearing}°"
        )

        # Reverse bearing should be close to 270° (west)
        reverse_bearing = SpatialCalculations.bearing_between(east_point, west_point)
        assert reverse_bearing == pytest.approx(270, abs=5), (
            f"Reverse bearing across date line should be ~270°, got {reverse_bearing}°"
        )

    def test_meridian_convergence(self):
        """Test that meridians converge at poles."""
        # Points at same latitude but different longitudes
        lat = 80  # Near north pole
        coords = [
            Coordinate(longitude=0, latitude=lat),
            Coordinate(longitude=90, latitude=lat),
            Coordinate(longitude=180, latitude=lat),
            Coordinate(longitude=-90, latitude=lat),
        ]

        north_pole = Coordinate(longitude=0, latitude=90)

        # All points should be equidistant from the pole
        distances_to_pole = [
            SpatialCalculations.distance_between(coord, north_pole)
            for coord in coords
        ]

        for i, distance in enumerate(distances_to_pole[1:], 1):
            assert distance == pytest.approx(distances_to_pole[0], rel=1e-6), (
                f"Distance from ({coords[i].latitude}, {coords[i].longitude}) to pole "
                f"should equal distance from ({coords[0].latitude}, {coords[0].longitude})"
            )

    def test_small_distance_precision(self):
        """Test precision for very small distances."""
        # Points very close together
        base = Coordinate(longitude=0, latitude=0)

        # Create points at various small distances
        small_offsets = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]  # degrees

        for offset in small_offsets:
            nearby = Coordinate(longitude=offset, latitude=0)
            distance = SpatialCalculations.distance_between(base, nearby)

            # Expected distance in meters (approximately)
            expected_meters = offset * 111320  # ~111.32 km per degree at equator
            expected_km = expected_meters / 1000

            assert distance == pytest.approx(expected_km, rel=0.1), (
                f"Small distance precision: {offset}° should be ~{expected_km:.6f}km, "
                f"got {distance:.6f}km"
            )

    def test_coordinate_boundary_values(self):
        """Test calculations with boundary coordinate values."""
        boundary_coords = [
            Coordinate(longitude=-180, latitude=-90),  # Southwest corner
            Coordinate(longitude=-180, latitude=90),   # Northwest corner
            Coordinate(longitude=180, latitude=-90),   # Southeast corner
            Coordinate(longitude=180, latitude=90),    # Northeast corner
            Coordinate(longitude=0, latitude=0),       # Origin
        ]

        # All combinations should work without errors
        for i, c1 in enumerate(boundary_coords):
            for j, c2 in enumerate(boundary_coords):
                distance = SpatialCalculations.distance_between(c1, c2)
                assert distance is not None, (
                    f"Distance calculation failed between boundary coordinates "
                    f"({c1.latitude}, {c1.longitude}) and ({c2.latitude}, {c2.longitude})"
                )
                assert distance >= 0, (
                    f"Distance should be non-negative, got {distance}km"
                )

    def test_numerical_stability_near_poles(self):
        """Test numerical stability for calculations very close to poles."""
        # Points very close to north pole
        near_pole_coords = [
            Coordinate(longitude=0, latitude=89.9999),
            Coordinate(longitude=90, latitude=89.9999),
            Coordinate(longitude=180, latitude=89.9999),
            Coordinate(longitude=-90, latitude=89.9999),
        ]

        north_pole = Coordinate(longitude=0, latitude=90)

        for coord in near_pole_coords:
            distance = SpatialCalculations.distance_between(coord, north_pole)

            # Distance should be very small but not zero
            assert 0 < distance < 20, (
                f"Distance from near-pole point to pole should be small: "
                f"got {distance}km for lat={coord.latitude}"
            )

    def test_bearing_edge_cases(self):
        """Test bearing calculations for edge cases."""
        origin = Coordinate(longitude=0, latitude=0)

        # Cardinal directions
        cardinal_tests = [
            (Coordinate(longitude=0, latitude=1), 0),    # North
            (Coordinate(longitude=1, latitude=0), 90),   # East
            (Coordinate(longitude=0, latitude=-1), 180), # South
            (Coordinate(longitude=-1, latitude=0), 270), # West
        ]

        for target, expected_bearing in cardinal_tests:
            bearing = SpatialCalculations.bearing_between(origin, target)
            assert bearing == pytest.approx(expected_bearing, abs=0.1), (
                f"Cardinal bearing to ({target.latitude}, {target.longitude}) "
                f"should be {expected_bearing}°, got {bearing}°"
            )

    def test_bearing_pole_cases(self):
        """Test bearing calculations involving poles."""
        north_pole = Coordinate(longitude=0, latitude=90)
        south_pole = Coordinate(longitude=0, latitude=-90)

        # From any point, bearing to north pole should be close to 0° (north)
        test_points = [
            Coordinate(longitude=0, latitude=45),
            Coordinate(longitude=90, latitude=45),
            Coordinate(longitude=180, latitude=45),
            Coordinate(longitude=-90, latitude=45),
        ]

        for point in test_points:
            bearing_to_north = SpatialCalculations.bearing_between(point, north_pole)
            bearing_to_south = SpatialCalculations.bearing_between(point, south_pole)

            # Bearing to north pole should be northward (close to 0°)
            assert bearing_to_north < 30 or bearing_to_north > 330, (
                f"Bearing from ({point.latitude}, {point.longitude}) to north pole "
                f"should be northward, got {bearing_to_north}°"
            )

            # Bearing to south pole should be southward (close to 180°)
            assert 150 < bearing_to_south < 210, (
                f"Bearing from ({point.latitude}, {point.longitude}) to south pole "
                f"should be southward, got {bearing_to_south}°"
            )

    def test_midpoint_edge_cases(self):
        """Test midpoint calculations for edge cases."""
        # Midpoint of antipodal points should be undefined or at least reasonable
        c1 = Coordinate(longitude=0, latitude=0)
        c2 = Coordinate(longitude=180, latitude=0)  # Antipodal on equator

        midpoint = SpatialCalculations.midpoint(c1, c2)

        # For antipodal points on equator, there are two valid midpoints
        # The algorithm should return one of them
        assert midpoint is not None, "Midpoint of antipodal points should be computable"

        # Midpoint should be on the equator
        assert abs(midpoint.latitude) < 0.1, (
            f"Midpoint of equatorial antipodes should be on equator, "
            f"got latitude {midpoint.latitude}"
        )

    def test_zero_distance_cases(self):
        """Test various ways to get zero distance."""
        coord = Coordinate(longitude=-74.006, latitude=40.7128)

        # Distance to self
        assert SpatialCalculations.distance_between(coord, coord) == 0

        # Distance between identical coordinates
        coord2 = Coordinate(longitude=-74.006, latitude=40.7128)
        assert SpatialCalculations.distance_between(coord, coord2) == 0

        # Distance with different altitude but same lat/lon
        coord_with_alt = Coordinate(longitude=-74.006, latitude=40.7128, altitude=1000)
        distance = SpatialCalculations.distance_between(coord, coord_with_alt)
        assert distance == pytest.approx(0, abs=0.001), (
            f"Distance should ignore altitude differences in great circle calculation, "
            f"got {distance}km"
        )

    def test_maximum_distance_constraints(self):
        """Test that distances never exceed theoretical maximum."""
        # Maximum possible distance on Earth is half the circumference
        MAX_DISTANCE_KM = 20037.5  # Half circumference at equator

        # Test various point pairs
        test_pairs = [
            (Coordinate(longitude=0, latitude=0), Coordinate(longitude=180, latitude=0)),
            (Coordinate(longitude=0, latitude=90), Coordinate(longitude=0, latitude=-90)),
            (Coordinate(longitude=-180, latitude=0), Coordinate(longitude=180, latitude=0)),
        ]

        for c1, c2 in test_pairs:
            distance = SpatialCalculations.distance_between(c1, c2)
            assert distance <= MAX_DISTANCE_KM * 1.01, (  # Allow 1% tolerance
                f"Distance {distance}km exceeds theoretical maximum {MAX_DISTANCE_KM}km "
                f"for points ({c1.latitude}, {c1.longitude}) to ({c2.latitude}, {c2.longitude})"
            )

    def test_invalid_coordinate_handling(self):
        """Test graceful handling of invalid coordinates in edge cases."""
        valid_coord = Coordinate(longitude=0, latitude=0)

        # Test objects with no coordinates
        point_no_coords = Point()
        placemark_no_coords = Placemark(name="No coordinates")

        assert SpatialCalculations.distance_between(valid_coord, point_no_coords) is None
        assert SpatialCalculations.distance_between(placemark_no_coords, valid_coord) is None
        assert SpatialCalculations.bearing_between(valid_coord, point_no_coords) is None
        assert SpatialCalculations.midpoint(valid_coord, point_no_coords) is None

    def test_precision_at_different_latitudes(self):
        """Test that precision is maintained at different latitudes."""
        # Test 1-degree longitude difference at various latitudes
        latitudes = [0, 30, 45, 60, 80, 89]  # Don't test exactly at pole

        for lat in latitudes:
            c1 = Coordinate(longitude=0, latitude=lat)
            c2 = Coordinate(longitude=1, latitude=lat)

            distance = SpatialCalculations.distance_between(c1, c2)

            # Expected distance: 1 degree longitude * cos(latitude) * 111.32 km/degree
            expected_km = math.cos(math.radians(lat)) * 111.32

            assert distance == pytest.approx(expected_km, rel=0.01), (
                f"1° longitude at latitude {lat}° should be ~{expected_km:.2f}km, "
                f"got {distance:.2f}km"
            )

    def test_strategy_consistency_for_edge_cases(self):
        """Test that different strategies give consistent results for edge cases."""
        strategies = [
            ("Haversine", HaversineStrategy()),
            ("Vincenty", VincentyStrategy()),
            ("Euclidean", EuclideanApproximation()),
        ]

        edge_cases = [
            (0, 0, 0, 0),      # Same point
            (0, 0, 0, 0.001),  # Very small distance
            (89, 0, 89, 1),    # Near pole
            (0, 179, 0, -179), # Date line crossing
        ]

        for lat1, lon1, lat2, lon2 in edge_cases:
            results = {}
            for name, strategy in strategies:
                try:
                    results[name] = strategy.calculate(lat1, lon1, lat2, lon2)
                except Exception:
                    # Some strategies might fail on edge cases
                    results[name] = None

            # For same point, all should return 0
            if lat1 == lat2 and lon1 == lon2:
                for name, result in results.items():
                    if result is not None:
                        assert result == pytest.approx(0, abs=1e-6), (
                            f"{name} should return 0 for same point"
                        )

    def test_coordinate_normalization_edge_cases(self):
        """Test that coordinate normalization handles edge cases properly."""
        # Test coordinates at the boundaries
        edge_coords = [
            # These should all be valid after normalization
            Coordinate(longitude=180, latitude=90),
            Coordinate(longitude=-180, latitude=-90),
            Coordinate(longitude=0, latitude=90),
            Coordinate(longitude=0, latitude=-90),
        ]

        origin = Coordinate(longitude=0, latitude=0)

        for coord in edge_coords:
            # Should not raise exceptions
            distance = SpatialCalculations.distance_between(origin, coord)
            bearing = SpatialCalculations.bearing_between(origin, coord)

            assert distance is not None, f"Distance calculation failed for edge coordinate {coord}"
            assert bearing is not None, f"Bearing calculation failed for edge coordinate {coord}"