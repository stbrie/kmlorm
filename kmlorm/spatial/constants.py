"""
Spatial calculation constants.

This module defines constants used in spatial calculations, including
Earth parameters, coordinate system definitions, and conversion factors.
"""

import math

# WGS84 Ellipsoid Parameters
# These are the official WGS84 constants as defined by the National Geospatial-Intelligence Agency
WGS84_A = 6378137.0  # Semi-major axis in meters
WGS84_B = 6356752.314245  # Semi-minor axis in meters
WGS84_F = 1 / 298.257223563  # Flattening factor
WGS84_E2 = 0.00669437999014  # First eccentricity squared

# Earth Radius Values (in kilometers)
EARTH_RADIUS_MEAN_KM = 6371.0088  # Mean radius
EARTH_RADIUS_EQUATORIAL_KM = 6378.137  # Equatorial radius
EARTH_RADIUS_POLAR_KM = 6356.752  # Polar radius

# Conversions
DEGREES_TO_RADIANS = math.pi / 180.0
RADIANS_TO_DEGREES = 180.0 / math.pi
KM_TO_METERS = 1000.0
METERS_TO_KM = 1.0 / 1000.0

# Distance Unit Conversion Factors (relative to kilometers)
DISTANCE_CONVERSIONS = {
    'meters': 1000.0,
    'kilometers': 1.0,
    'miles': 0.621371,
    'nautical_miles': 0.539957,
    'feet': 3280.84,
    'yards': 1093.61,
}

# Angular Constants
FULL_CIRCLE_DEGREES = 360.0
HALF_CIRCLE_DEGREES = 180.0
RIGHT_ANGLE_DEGREES = 90.0

# Coordinate Bounds
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0
MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0

# Precision and Tolerance
DEFAULT_COORDINATE_PRECISION = 1e-6  # ~0.11 meters at equator
DEFAULT_DISTANCE_TOLERANCE = 1e-3  # 1 meter tolerance for distance comparisons
ANTIPODAL_THRESHOLD = 179.99  # Degrees - threshold for detecting antipodal points

# Performance Constants
LRU_CACHE_SIZE = 1024  # Size of LRU cache for repeated calculations
BULK_OPERATION_THRESHOLD = 1000  # Element count threshold for spatial indexing
