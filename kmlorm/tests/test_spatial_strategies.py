"""
Test spatial calculation strategies and their accuracy characteristics.

This module tests the different distance calculation strategies available
in the spatial module, comparing their accuracy and performance characteristics.
"""

import time
import pytest

from kmlorm.spatial.strategies import (
    HaversineStrategy,
    VincentyStrategy,
    EuclideanApproximation,
    AdaptiveStrategy,
)


class TestDistanceStrategies:
    """Test different distance calculation strategies."""

    # Test coordinates with expected distances for validation
    TEST_COORDINATES = [
        # (lat1, lon1, lat2, lon2, expected_haversine_km, tolerance_km)
        (0, 0, 0, 0, 0, 0),  # Same point
        (0, 0, 0, 1, 111.32, 1),  # 1 degree longitude at equator
        (0, 0, 1, 0, 111.32, 1),  # 1 degree latitude
        (40.7128, -74.006, 51.5074, -0.1276, 5567, 10),  # NYC to London
        (0, 0, 0, 180, 20037.5, 50),  # Half circumference
        (90, 0, -90, 0, 20003.9, 50),  # Pole to pole
    ]

    def test_haversine_strategy_known_distances(self) -> None:
        """Test Haversine strategy against known distances."""
        strategy = HaversineStrategy()

        for lat1, lon1, lat2, lon2, expected_km, tolerance in self.TEST_COORDINATES:
            distance = strategy.calculate(lat1, lon1, lat2, lon2)
            assert abs(distance - expected_km) <= tolerance, (
                f"Haversine distance {distance:.2f}km should be {expected_km}±{tolerance}km "
                f"for ({lat1}, {lon1}) to ({lat2}, {lon2})"
            )

    def test_haversine_strategy_properties(self) -> None:
        """Test mathematical properties of Haversine strategy."""
        strategy = HaversineStrategy()

        # Symmetry
        d1 = strategy.calculate(0, 0, 1, 1)
        d2 = strategy.calculate(1, 1, 0, 0)
        assert d1 == pytest.approx(d2, rel=1e-10)

        # Distance to self is zero
        assert strategy.calculate(40.7, -74.0, 40.7, -74.0) == pytest.approx(0, abs=1e-10)

        # Triangle inequality (approximately)
        # For small distances, sum of two sides > third side
        d_ab = strategy.calculate(0, 0, 0, 1)
        d_bc = strategy.calculate(0, 1, 1, 1)
        d_ac = strategy.calculate(0, 0, 1, 1)
        assert (d_ab + d_bc) >= d_ac * 0.99  # Allow small numerical error

    def test_vincenty_strategy_accuracy(self) -> None:
        """Test Vincenty strategy for high accuracy."""
        vincenty = VincentyStrategy()
        haversine = HaversineStrategy()

        # For short distances, Vincenty should be very close to Haversine
        short_distance_cases = [
            (0, 0, 0.1, 0.1),  # Very short distance
            (51.5074, -0.1276, 51.5500, -0.1000),  # Short distance in London
        ]

        for lat1, lon1, lat2, lon2 in short_distance_cases:
            v_dist = vincenty.calculate(lat1, lon1, lat2, lon2)
            h_dist = haversine.calculate(lat1, lon1, lat2, lon2)

            # Vincenty should be within 0.5% of Haversine for short distances
            assert abs(v_dist - h_dist) / h_dist < 0.005, (
                f"Vincenty {v_dist:.6f} and Haversine {h_dist:.6f} should be very close "
                f"for short distance ({lat1}, {lon1}) to ({lat2}, {lon2})"
            )

    def test_vincenty_strategy_convergence(self) -> None:
        """Test Vincenty strategy convergence behavior."""
        strategy = VincentyStrategy(max_iterations=10, tolerance=1e-6)

        # Normal case should converge
        distance = strategy.calculate(40.7128, -74.006, 51.5074, -0.1276)
        assert distance > 0

        # Test with very strict tolerance - should still work
        strict_strategy = VincentyStrategy(max_iterations=200, tolerance=1e-15)
        strict_distance = strict_strategy.calculate(0, 0, 1, 1)
        assert strict_distance > 0

    def test_vincenty_fallback_to_haversine(self) -> None:
        """Test that Vincenty falls back to Haversine for non-convergent cases."""
        # Use very low iteration limit to force fallback
        strategy = VincentyStrategy(max_iterations=1, tolerance=1e-15)
        haversine = HaversineStrategy()

        lat1, lon1, lat2, lon2 = 40.7128, -74.006, 51.5074, -0.1276
        v_dist = strategy.calculate(lat1, lon1, lat2, lon2)
        h_dist = haversine.calculate(lat1, lon1, lat2, lon2)

        # Should fall back to Haversine result
        assert v_dist == pytest.approx(h_dist, rel=1e-6)

    def test_euclidean_approximation_accuracy(self) -> None:
        """Test Euclidean approximation accuracy for small distances."""
        euclidean = EuclideanApproximation()
        haversine = HaversineStrategy()

        # Test cases with small distances where Euclidean should be reasonably accurate
        small_distance_cases = [
            (40.7128, -74.006, 40.7200, -74.000),  # ~1.5 km
            (0, 0, 0.01, 0.01),  # ~1.6 km
            (51.5074, -0.1276, 51.5100, -0.1200),  # ~0.8 km
        ]

        for lat1, lon1, lat2, lon2 in small_distance_cases:
            e_dist = euclidean.calculate(lat1, lon1, lat2, lon2)
            h_dist = haversine.calculate(lat1, lon1, lat2, lon2)

            # Euclidean should be within 5% of Haversine for small distances
            error_percent = abs(e_dist - h_dist) / h_dist * 100
            assert error_percent < 5, (
                f"Euclidean approximation error {error_percent:.2f}% too high "
                f"for small distance: Euclidean {e_dist:.3f}km vs Haversine {h_dist:.3f}km"
            )

    def test_euclidean_approximation_degradation(self) -> None:
        """Test that Euclidean approximation degrades gracefully for large distances."""
        euclidean = EuclideanApproximation()
        haversine = HaversineStrategy()

        # Large distance case where Euclidean should be less accurate
        lat1, lon1, lat2, lon2 = 0, 0, 10, 10  # ~1570 km

        e_dist = euclidean.calculate(lat1, lon1, lat2, lon2)
        h_dist = haversine.calculate(lat1, lon1, lat2, lon2)

        # Euclidean may over or underestimate, but should be in reasonable ballpark
        error_percent = abs(e_dist - h_dist) / h_dist * 100
        assert (
            error_percent < 50
        ), f"Euclidean error {error_percent:.1f}% should not exceed 50% even for large distances"

    def test_adaptive_strategy_selection(self) -> None:
        """Test that adaptive strategy selects appropriate algorithms."""
        adaptive_fast = AdaptiveStrategy(high_accuracy=False)
        adaptive_accurate = AdaptiveStrategy(high_accuracy=True)

        # Small distance - should use Euclidean for both
        small_dist_fast = adaptive_fast.calculate(0, 0, 0.1, 0.1)  # ~16 km
        small_dist_accurate = adaptive_accurate.calculate(0, 0, 0.1, 0.1)

        # Should be the same for small distances
        assert small_dist_fast == pytest.approx(small_dist_accurate, rel=1e-6)

        # Medium distance - should use Haversine for both
        med_dist_fast = adaptive_fast.calculate(0, 0, 1, 1)  # ~157 km
        med_dist_accurate = adaptive_accurate.calculate(0, 0, 1, 1)

        # Should be the same for medium distances
        assert med_dist_fast == pytest.approx(med_dist_accurate, rel=1e-6)

        # Large distance - fast should use Haversine, accurate should use Vincenty
        large_dist_fast = adaptive_fast.calculate(0, 0, 45, 45)  # ~7071 km
        large_dist_accurate = adaptive_accurate.calculate(0, 0, 45, 45)

        # May be slightly different due to algorithm choice
        # But should be within reasonable bounds
        assert abs(large_dist_fast - large_dist_accurate) / large_dist_fast < 0.01

    def test_strategy_coordinate_validation(self) -> None:
        """Test that strategies validate coordinate ranges."""
        strategy = HaversineStrategy()

        # Valid coordinates should work
        distance = strategy.calculate(0, 0, 1, 1)
        assert distance > 0

        # Invalid latitudes should raise ValueError
        with pytest.raises(ValueError, match="Latitude must be between"):
            strategy.calculate(91, 0, 0, 0)  # Latitude > 90

        with pytest.raises(ValueError, match="Latitude must be between"):
            strategy.calculate(-91, 0, 0, 0)  # Latitude < -90

        # Invalid longitudes should raise ValueError
        with pytest.raises(ValueError, match="Longitude must be between"):
            strategy.calculate(0, 181, 0, 0)  # Longitude > 180

        with pytest.raises(ValueError, match="Longitude must be between"):
            strategy.calculate(0, -181, 0, 0)  # Longitude < -180

    def test_all_strategies_consistent_for_same_point(self) -> None:
        """Test that all strategies return 0 for distance to same point."""
        strategies = [
            HaversineStrategy(),
            VincentyStrategy(),
            EuclideanApproximation(),
            AdaptiveStrategy(high_accuracy=False),
            AdaptiveStrategy(high_accuracy=True),
        ]

        test_points = [
            (0, 0),
            (40.7128, -74.006),
            (90, 0),  # North pole
            (-90, 0),  # South pole
            (0, 180),  # Date line
        ]

        for strategy in strategies:
            for lat, lon in test_points:
                distance = strategy.calculate(lat, lon, lat, lon)
                assert distance == pytest.approx(
                    0, abs=1e-6
                ), f"{strategy.__class__.__name__} should return 0 for same point ({lat}, {lon})"

    def test_strategy_performance_ordering(self) -> None:
        """Test relative performance characteristics of strategies."""

        strategies = [
            ("Euclidean", EuclideanApproximation()),
            ("Haversine", HaversineStrategy()),
            ("Vincenty", VincentyStrategy()),
        ]

        # Test coordinates
        coords = [(40.7128, -74.006, 51.5074, -0.1276)] * 100

        times = {}
        for name, strategy in strategies:
            start_time = time.perf_counter()
            for lat1, lon1, lat2, lon2 in coords:
                strategy.calculate(lat1, lon1, lat2, lon2)
            times[name] = time.perf_counter() - start_time

        # Euclidean should be fastest, Vincenty slowest
        assert times["Euclidean"] <= times["Haversine"], "Euclidean should be faster than Haversine"
        assert times["Haversine"] <= times["Vincenty"], "Haversine should be faster than Vincenty"

    def test_strategy_extreme_coordinates(self) -> None:
        """Test strategies with extreme but valid coordinates."""
        # Separate strategies by their expected accuracy
        accurate_strategies = [
            HaversineStrategy(),
            VincentyStrategy(),
        ]

        # EuclideanApproximation is expected to fail on extreme cases
        euclidean = EuclideanApproximation()

        extreme_cases = [
            (89.9, 179.9, -89.9, -179.9),  # Nearly antipodal
            (0, 0, 0, 179.9),  # Nearly half circumference longitude
            (89.9, 0, -89.9, 0),  # Nearly pole to pole
            (0, -179.9, 0, 179.9),  # Date line crossing
        ]

        # Test accurate strategies - should handle extreme cases well
        for strategy in accurate_strategies:
            for lat1, lon1, lat2, lon2 in extreme_cases:
                try:
                    distance = strategy.calculate(lat1, lon1, lat2, lon2)
                    assert (
                        distance >= 0
                    ), f"{strategy.__class__.__name__} returned negative distance"
                    assert (
                        distance <= 20100
                    ), f"{strategy.__class__.__name__} returned impossible distance {distance}km"
                except Exception as e:  # pylint: disable=broad-exception-caught
                    pytest.fail(f"{strategy.__class__.__name__} failed on extreme coordinates: {e}")

        # Test EuclideanApproximation separately - it's expected to be
        # inaccurate for large distances
        for lat1, lon1, lat2, lon2 in extreme_cases:
            try:
                distance = euclidean.calculate(lat1, lon1, lat2, lon2)
                assert distance >= 0, "EuclideanApproximation returned negative distance"
                # Don't enforce maximum distance for Euclidean - it's
                # expected to be wrong for large distances
            except Exception as e:  # pylint: disable=broad-exception-caught
                pytest.fail(
                    f"EuclideanApproximation failed to calculate (should at least not crash): {e}"
                )

    def test_strategy_date_line_handling(self) -> None:
        """Test proper handling of date line crossing."""
        # Separate strategies by their expected accuracy for date line crossing
        accurate_strategies = [
            HaversineStrategy(),
            VincentyStrategy(),
        ]

        euclidean = EuclideanApproximation()

        # Points very close across the date line
        lat1, lon1 = 0, 179.5
        lat2, lon2 = 0, -179.5

        # Test accurate strategies - should handle date line correctly
        for strategy in accurate_strategies:
            distance = strategy.calculate(lat1, lon1, lat2, lon2)

            # Distance should be small (about 111 km), not large (about 20000 km)
            assert distance < 200, (
                f"{strategy.__class__.__name__} incorrectly calculated date line crossing: "
                f"{distance:.2f}km (should be ~111km)"
            )

        # Test EuclideanApproximation separately - it's expected to fail on date line crossing
        euclidean_distance = euclidean.calculate(lat1, lon1, lat2, lon2)
        # Just verify it doesn't crash and returns a positive number
        # (EuclideanApproximation is not expected to handle date line correctly)
        assert (
            euclidean_distance >= 0
        ), "EuclideanApproximation should at least return a positive distance"

    def test_adaptive_strategy_thresholds(self) -> None:
        """Test that adaptive strategy respects distance thresholds."""
        adaptive = AdaptiveStrategy(high_accuracy=True)
        euclidean = EuclideanApproximation()
        haversine = HaversineStrategy()
        vincenty = VincentyStrategy()

        # Very small distance - should match Euclidean
        small_dist = adaptive.calculate(0, 0, 0.1, 0.1)  # ~16 km
        euclidean_dist = euclidean.calculate(0, 0, 0.1, 0.1)
        assert small_dist == pytest.approx(euclidean_dist, rel=1e-10)

        # Medium distance - should match Haversine
        med_dist = adaptive.calculate(0, 0, 5, 0)  # ~556 km
        haversine_dist = haversine.calculate(0, 0, 5, 0)
        assert med_dist == pytest.approx(haversine_dist, rel=1e-10)

        # Large distance with high accuracy - should match Vincenty (within reasonable tolerance)
        large_dist = adaptive.calculate(0, 0, 45, 45)  # ~7071 km
        vincenty_dist = vincenty.calculate(0, 0, 45, 45)
        # Allow for reasonable precision differences between strategies
        assert large_dist == pytest.approx(vincenty_dist, rel=0.01)
