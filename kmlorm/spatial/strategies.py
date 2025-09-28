"""
Distance calculation strategies for spatial operations.

This module provides different strategies for calculating distances between
coordinates, each with different trade-offs between accuracy and performance.

Available Strategies:
    - HaversineStrategy: Good balance of speed and accuracy (default)
    - VincentyStrategy: High accuracy for oblate spheroid (slower)
    - EuclideanApproximation: Fast approximation for small distances

Usage:
    >>> from kmlorm.spatial.strategies import HaversineStrategy, VincentyStrategy
    >>> strategy = HaversineStrategy()
    >>> distance = strategy.calculate(40.7128, -74.006, 51.5074, -0.1276)
"""

import math
from abc import ABC, abstractmethod
from typing import Optional

from .constants import (
    EARTH_RADIUS_MEAN_KM,
    WGS84_A,
    WGS84_F,
    DEGREES_TO_RADIANS,
    DEFAULT_COORDINATE_PRECISION,
)


class DistanceStrategy(ABC):
    """
    Abstract base class for distance calculation strategies.

    All strategies should implement the calculate method to compute
    distance between two points in decimal degrees.
    """

    @abstractmethod
    def calculate(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points.

        Args:
            lat1, lon1: First point coordinates in decimal degrees
            lat2, lon2: Second point coordinates in decimal degrees

        Returns:
            Distance in kilometers

        Raises:
            ValueError: If coordinates are invalid
        """
        pass

    def _validate_coordinates(self, lat1: float, lon1: float, lat2: float, lon2: float) -> None:
        """Validate that coordinates are within valid ranges."""
        if not (-90 <= lat1 <= 90) or not (-90 <= lat2 <= 90):
            raise ValueError(f"Latitude must be between -90 and 90 degrees")
        if not (-180 <= lon1 <= 180) or not (-180 <= lon2 <= 180):
            raise ValueError(f"Longitude must be between -180 and 180 degrees")


class HaversineStrategy(DistanceStrategy):
    """
    Great circle distance using Haversine formula.

    This is a good balance of speed and accuracy for most applications.
    Assumes a spherical Earth with mean radius of 6371.0088 km.

    Accuracy: ±0.5% for most distances
    Performance: Fast (O(1) with simple trigonometric operations)
    Best for: General purpose distance calculations

    Formula:
        a = sin²(Δφ/2) + cos(φ1) * cos(φ2) * sin²(Δλ/2)
        c = 2 * atan2(√a, √(1−a))
        d = R * c

    Where φ is latitude, λ is longitude, R is Earth's radius.
    """

    def calculate(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance using Haversine formula.

        Args:
            lat1, lon1: First point coordinates in decimal degrees
            lat2, lon2: Second point coordinates in decimal degrees

        Returns:
            Distance in kilometers

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self._validate_coordinates(lat1, lon1, lat2, lon2)

        # Convert to radians
        lat1_r, lon1_r, lat2_r, lon2_r = map(
            lambda x: x * DEGREES_TO_RADIANS,
            [lat1, lon1, lat2, lon2]
        )

        # Haversine formula
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        return EARTH_RADIUS_MEAN_KM * c


class VincentyStrategy(DistanceStrategy):
    """
    Vincenty's formulae for accurate distance on oblate spheroid.

    This strategy uses Vincenty's inverse formula for calculating distances
    on an oblate spheroid (WGS84 ellipsoid). More accurate than Haversine
    but significantly slower.

    Accuracy: ±0.5mm for distances up to ~20,000 km
    Performance: Slower (iterative algorithm)
    Best for: High-precision applications requiring maximum accuracy

    Reference: T. Vincenty, "Direct and Inverse Solutions of Geodesics on the
               Ellipsoid with application of nested equations", Survey Review,
               vol XXIII no 176, 1975
    """

    def __init__(self, max_iterations: int = 100, tolerance: float = 1e-12):
        """
        Initialize Vincenty strategy.

        Args:
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance in radians
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def calculate(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance using Vincenty's inverse formula.

        Args:
            lat1, lon1: First point coordinates in decimal degrees
            lat2, lon2: Second point coordinates in decimal degrees

        Returns:
            Distance in kilometers

        Raises:
            ValueError: If coordinates are invalid or calculation doesn't converge
        """
        self._validate_coordinates(lat1, lon1, lat2, lon2)

        # Check for identical points
        if abs(lat1 - lat2) < DEFAULT_COORDINATE_PRECISION and abs(lon1 - lon2) < DEFAULT_COORDINATE_PRECISION:
            return 0.0

        # Convert to radians
        lat1_r = lat1 * DEGREES_TO_RADIANS
        lat2_r = lat2 * DEGREES_TO_RADIANS
        lon1_r = lon1 * DEGREES_TO_RADIANS
        lon2_r = lon2 * DEGREES_TO_RADIANS

        # WGS84 ellipsoid parameters
        a = WGS84_A / 1000.0  # Convert to kilometers
        f = WGS84_F
        b = (1 - f) * a

        L = lon2_r - lon1_r  # Difference in longitude
        U1 = math.atan((1 - f) * math.tan(lat1_r))  # Reduced latitude
        U2 = math.atan((1 - f) * math.tan(lat2_r))  # Reduced latitude

        sin_U1 = math.sin(U1)
        cos_U1 = math.cos(U1)
        sin_U2 = math.sin(U2)
        cos_U2 = math.cos(U2)

        antipodal = abs(L) > math.pi / 2 or abs(lat2_r - lat1_r) > math.pi / 4

        lambda_val = L  # Initial value
        lambda_prev = 2 * math.pi

        iteration = 0
        while abs(lambda_val - lambda_prev) > self.tolerance and iteration < self.max_iterations:
            sin_lambda = math.sin(lambda_val)
            cos_lambda = math.cos(lambda_val)

            sin_sigma = math.sqrt(
                (cos_U2 * sin_lambda) ** 2 +
                (cos_U1 * sin_U2 - sin_U1 * cos_U2 * cos_lambda) ** 2
            )

            if sin_sigma == 0:
                return 0.0  # Co-incident points

            cos_sigma = sin_U1 * sin_U2 + cos_U1 * cos_U2 * cos_lambda
            sigma = math.atan2(sin_sigma, cos_sigma)

            sin_alpha = cos_U1 * cos_U2 * sin_lambda / sin_sigma
            cos2_alpha = 1 - sin_alpha ** 2

            if cos2_alpha == 0:
                # Equatorial line
                cos_2sigma_m = 0
            else:
                cos_2sigma_m = cos_sigma - 2 * sin_U1 * sin_U2 / cos2_alpha

            C = f / 16 * cos2_alpha * (4 + f * (4 - 3 * cos2_alpha))

            lambda_prev = lambda_val
            lambda_val = (L + (1 - C) * f * sin_alpha *
                         (sigma + C * sin_sigma *
                          (cos_2sigma_m + C * cos_sigma *
                           (-1 + 2 * cos_2sigma_m ** 2))))

            if antipodal and iteration > 50:
                # Handle antipodal case
                lambda_val = math.pi - abs(lambda_val)

            iteration += 1

        if iteration >= self.max_iterations:
            # Fall back to Haversine for non-convergent cases
            haversine = HaversineStrategy()
            return haversine.calculate(lat1, lon1, lat2, lon2)

        u2 = cos2_alpha * (a ** 2 - b ** 2) / (b ** 2)
        A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
        B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))

        delta_sigma = (B * sin_sigma *
                      (cos_2sigma_m + B / 4 *
                       (cos_sigma * (-1 + 2 * cos_2sigma_m ** 2) -
                        B / 6 * cos_2sigma_m * (-3 + 4 * sin_sigma ** 2) *
                        (-3 + 4 * cos_2sigma_m ** 2))))

        s = b * A * (sigma - delta_sigma)

        return s  # Distance in kilometers


class EuclideanApproximation(DistanceStrategy):
    """
    Fast Euclidean approximation for small distances.

    Uses equirectangular projection (plate carrée) to approximate distances.
    Very fast but only accurate for small distances (typically <100km).

    Accuracy: Good for distances <100km, decreases with distance and latitude
    Performance: Very fast (O(1) with minimal operations)
    Best for: Quick approximations, filtering, when speed is critical

    Formula:
        x = Δλ * cos(φm)
        y = Δφ
        d = R * √(x² + y²)

    Where φm is the mean latitude.
    """

    def calculate(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance using Euclidean approximation.

        Args:
            lat1, lon1: First point coordinates in decimal degrees
            lat2, lon2: Second point coordinates in decimal degrees

        Returns:
            Distance in kilometers

        Note:
            This is an approximation and becomes less accurate for:
            - Large distances (>100km)
            - High latitudes (near poles)
            - Distances crossing large longitude differences
        """
        self._validate_coordinates(lat1, lon1, lat2, lon2)

        # Convert to radians
        lat1_r = lat1 * DEGREES_TO_RADIANS
        lat2_r = lat2 * DEGREES_TO_RADIANS
        lon1_r = lon1 * DEGREES_TO_RADIANS
        lon2_r = lon2 * DEGREES_TO_RADIANS

        # Mean latitude for projection
        lat_mean = (lat1_r + lat2_r) / 2

        # Differences
        dx = (lon2_r - lon1_r) * math.cos(lat_mean)
        dy = lat2_r - lat1_r

        # Euclidean distance on the sphere
        distance = EARTH_RADIUS_MEAN_KM * math.sqrt(dx * dx + dy * dy)

        return distance


class AdaptiveStrategy(DistanceStrategy):
    """
    Adaptive strategy that selects the best algorithm based on distance and requirements.

    This strategy automatically chooses between different algorithms based on
    the characteristics of the calculation:
    - Euclidean for very small distances (<50km)
    - Haversine for medium distances (50km - 10,000km)
    - Vincenty for long distances (>10,000km) when high accuracy is needed

    This provides a good balance of performance and accuracy for mixed workloads.
    """

    def __init__(self, high_accuracy: bool = False):
        """
        Initialize adaptive strategy.

        Args:
            high_accuracy: Whether to prefer accuracy over speed for long distances
        """
        self.high_accuracy = high_accuracy
        self.euclidean = EuclideanApproximation()
        self.haversine = HaversineStrategy()
        self.vincenty = VincentyStrategy() if high_accuracy else None

    def calculate(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance using the most appropriate strategy.

        Args:
            lat1, lon1: First point coordinates in decimal degrees
            lat2, lon2: Second point coordinates in decimal degrees

        Returns:
            Distance in kilometers
        """
        # Quick Euclidean approximation to determine strategy
        approx_distance = self.euclidean.calculate(lat1, lon1, lat2, lon2)

        if approx_distance < 50:  # Small distance - use Euclidean
            return approx_distance
        elif approx_distance < 10000 or not self.high_accuracy:  # Medium distance - use Haversine
            return self.haversine.calculate(lat1, lon1, lat2, lon2)
        else:  # Long distance and high accuracy required - use Vincenty
            if self.vincenty:
                return self.vincenty.calculate(lat1, lon1, lat2, lon2)
            else:
                return self.haversine.calculate(lat1, lon1, lat2, lon2)


# Default strategy for the spatial calculations module
DEFAULT_STRATEGY = HaversineStrategy()
