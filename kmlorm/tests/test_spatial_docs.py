"""
Tests that validate every example in docs/source/api/spatial.rst works as documented.

This test suite ensures that all code examples in the spatial documentation
are functional and produce the expected results.
"""

# pylint: disable=duplicate-code
import pytest
from kmlorm.models import Placemark
from kmlorm.models.point import Coordinate, Point
from kmlorm.spatial import DistanceUnit
from kmlorm.spatial.calculations import SpatialCalculations
from kmlorm.parsers.kml_file import KMLFile


class TestSpatialDocsExamples:
    """Test cases that validate spatial.rst documentation examples."""

    @pytest.fixture
    def nyc_coord(self) -> Coordinate:
        """NYC coordinate for testing."""
        return Coordinate(longitude=-74.006, latitude=40.7128)

    @pytest.fixture
    def london_coord(self) -> Coordinate:
        """London coordinate for testing."""
        return Coordinate(longitude=-0.1276, latitude=51.5074)

    @pytest.fixture
    def nyc_placemark(self) -> Placemark:
        """NYC placemark for testing."""
        return Placemark(name="NYC", coordinates=(-74.006, 40.7128))

    @pytest.fixture
    def london_placemark(self) -> Placemark:
        """London placemark for testing."""
        return Placemark(name="London", coordinates=(-0.1276, 51.5074))

    def test_quick_example_from_docs(
        self, nyc_placemark: Placemark, london_placemark: Placemark
    ) -> None:
        """Test the quick example from the overview section."""
        # From lines 28-52 of spatial.rst

        # Calculate distance (default: kilometers)
        distance_km = nyc_placemark.distance_to(london_placemark)
        # Documentation shows 5570.2 km
        assert distance_km == pytest.approx(5570.2, abs=0.5)

        # Calculate in different units
        distance_miles = nyc_placemark.distance_to(london_placemark, unit=DistanceUnit.MILES)
        # Documentation shows 3461.0 miles
        assert distance_miles == pytest.approx(3461.0, abs=1.0)

        # Calculate bearing
        bearing = nyc_placemark.bearing_to(london_placemark)
        # Documentation shows 51.2°
        assert bearing == pytest.approx(51.2, abs=0.5)

        # Find midpoint
        midpoint = nyc_placemark.midpoint_to(london_placemark)
        assert midpoint is not None
        # Verify it's approximately in the middle of the Atlantic
        # Documentation shows (-41.29, 52.37)
        assert midpoint.longitude == pytest.approx(-41.29, abs=0.5)
        assert midpoint.latitude == pytest.approx(52.37, abs=0.5)

    def test_distance_units_example(
        self, nyc_placemark: Placemark, london_placemark: Placemark
    ) -> None:
        """Test the distance units example from lines 113-121."""
        # Calculate distance in different units
        distance_km = nyc_placemark.distance_to(london_placemark)
        distance_m = nyc_placemark.distance_to(london_placemark, unit=DistanceUnit.METERS)
        distance_mi = nyc_placemark.distance_to(london_placemark, unit=DistanceUnit.MILES)

        # Verify unit conversions
        assert distance_km is not None
        assert distance_m is not None
        assert distance_mi is not None
        assert distance_m == pytest.approx(distance_km * 1000, rel=0.01)
        assert distance_mi == pytest.approx(distance_km * 0.621371, rel=0.01)

    def test_spatial_calculations_class_example(
        self, nyc_coord: Coordinate, london_coord: Coordinate
    ) -> None:
        """Test the SpatialCalculations class example from lines 142-152."""
        # Example from documentation
        distance = SpatialCalculations.distance_between(nyc_coord, london_coord)
        assert distance is not None
        assert distance == pytest.approx(5570.2, abs=0.5)

    def test_bearing_calculation_example(
        self, nyc_coord: Coordinate, london_coord: Coordinate
    ) -> None:
        """Test the bearing calculation example from lines 165-168."""
        bearing = SpatialCalculations.bearing_between(nyc_coord, london_coord)
        assert bearing is not None
        # Should be approximately northeast direction
        assert 45 < bearing < 60  # Northeast quadrant

    def test_distances_to_many_example(self) -> None:
        """Test the bulk distance calculation example from lines 190-199."""
        center = Coordinate(longitude=0, latitude=0)
        coord1 = Coordinate(longitude=-74.006, latitude=40.7128)
        coord2 = Coordinate(longitude=-0.1276, latitude=51.5074)
        coord3 = Coordinate(longitude=139.6917, latitude=35.6895)  # Tokyo
        coord4 = Coordinate(longitude=-122.4194, latitude=37.7749)  # San Francisco

        targets = [coord1, coord2, coord3, coord4]

        distances = SpatialCalculations.distances_to_many(center, targets)

        # Verify we got distances for all targets
        assert len(distances) == 4
        for dist in distances:
            assert dist is not None
            assert dist > 0

    def test_basic_distance_calculations_example(self) -> None:
        """Test the basic distance calculations example from lines 246-269."""
        # Distance between Coordinate objects
        coord1 = Coordinate(longitude=-74.006, latitude=40.7128)  # NYC
        coord2 = Coordinate(longitude=-0.1276, latitude=51.5074)  # London
        distance = coord1.distance_to(coord2)
        assert distance == pytest.approx(5570.2, abs=0.5)

        # Distance between Points
        point1 = Point(coordinates=(-74.006, 40.7128))
        point2 = Point(coordinates=(-0.1276, 51.5074))
        distance = point1.distance_to(point2)
        assert distance == pytest.approx(5570.2, abs=0.5)

        # Distance between Placemarks
        place1 = Placemark(name="NYC", coordinates=(-74.006, 40.7128))
        place2 = Placemark(name="London", coordinates=(-0.1276, 51.5074))
        distance = place1.distance_to(place2)
        assert distance == pytest.approx(5570.2, abs=0.5)

        # Mixed types - all work together
        distance = coord1.distance_to(place2)
        assert distance == pytest.approx(5570.2, abs=0.5)

        distance = point1.distance_to(coord2)
        assert distance == pytest.approx(5570.2, abs=0.5)

    def test_working_with_different_units_example(
        self, nyc_placemark: Placemark, london_placemark: Placemark
    ) -> None:
        """Test the different units example from lines 273-288."""
        # Default is kilometers
        km = nyc_placemark.distance_to(london_placemark)

        # Other units
        meters = nyc_placemark.distance_to(london_placemark, unit=DistanceUnit.METERS)
        miles = nyc_placemark.distance_to(london_placemark, unit=DistanceUnit.MILES)
        nautical = nyc_placemark.distance_to(london_placemark, unit=DistanceUnit.NAUTICAL_MILES)
        feet = nyc_placemark.distance_to(london_placemark, unit=DistanceUnit.FEET)
        yards = nyc_placemark.distance_to(london_placemark, unit=DistanceUnit.YARDS)

        # Verify conversions
        assert km is not None
        assert meters is not None
        assert miles is not None
        assert nautical is not None
        assert feet is not None
        assert yards is not None
        assert meters == pytest.approx(km * 1000, rel=0.01)
        assert miles == pytest.approx(km * 0.621371, rel=0.01)
        assert nautical == pytest.approx(km * 0.539957, rel=0.01)
        assert feet == pytest.approx(km * 3280.84, rel=0.01)
        assert yards == pytest.approx(km * 1093.61, rel=0.01)

    def test_bearing_and_navigation_example(
        self, nyc_placemark: Placemark, london_placemark: Placemark
    ) -> None:
        """Test the bearing and navigation example from lines 293-317."""
        # Calculate bearing (initial heading)
        bearing = nyc_placemark.bearing_to(london_placemark)
        assert bearing is not None

        # Bearing interpretation
        if bearing < 22.5 or bearing >= 337.5:
            direction = "North"
        elif bearing < 67.5:
            direction = "Northeast"
        elif bearing < 112.5:
            direction = "East"
        elif bearing < 157.5:
            direction = "Southeast"
        elif bearing < 202.5:
            direction = "South"
        elif bearing < 247.5:
            direction = "Southwest"
        elif bearing < 292.5:
            direction = "West"
        else:
            direction = "Northwest"

        # NYC to London should be Northeast
        assert direction == "Northeast"
        assert 45 < bearing < 60

    def test_finding_midpoints_example(
        self, nyc_placemark: Placemark, london_placemark: Placemark
    ) -> None:
        """Test the finding midpoints example from lines 321-335."""
        # Find geographic midpoint
        midpoint = nyc_placemark.midpoint_to(london_placemark)

        assert midpoint is not None
        # Verify midpoint is in the Atlantic Ocean
        # Documentation shows (-41.29, 52.37)
        assert midpoint.longitude == pytest.approx(-41.29, abs=0.5)
        assert midpoint.latitude == pytest.approx(52.37, abs=0.5)

        # Create a new placemark at the midpoint
        midpoint_place = Placemark(
            name="Atlantic Midpoint", coordinates=(midpoint.longitude, midpoint.latitude)
        )

        assert midpoint_place.longitude == midpoint.longitude
        assert midpoint_place.latitude == midpoint.latitude

    def test_bulk_distance_operations_example(self) -> None:
        """Test the bulk distance operations example from lines 339-361."""
        # Efficient bulk distance calculations
        center = Coordinate(longitude=0, latitude=0)

        # Many target locations
        targets = [
            Placemark(name="North", coordinates=(0, 10)),
            Placemark(name="South", coordinates=(0, -10)),
            Placemark(name="East", coordinates=(10, 0)),
            Placemark(name="West", coordinates=(-10, 0)),
            Placemark(name="Northeast", coordinates=(10, 10)),
        ]

        # Calculate all distances at once
        distances = SpatialCalculations.distances_to_many(center, targets)

        # Verify distances
        assert len(distances) == 5

        # All should be valid distances
        for distance in distances:
            assert distance is not None
            assert distance > 0

        # Verify approximate distances (at equator, 1 degree ≈ 111 km)
        # North and South should be approximately equal
        assert distances[0] == pytest.approx(distances[1], abs=1.0)
        # East and West should be approximately equal
        assert distances[2] == pytest.approx(distances[3], abs=1.0)
        # Northeast should be further (diagonal)
        assert distances[4] > distances[0]

    def test_date_line_crossing_example(self) -> None:
        """Test the date line crossing example from lines 398-405."""
        # Points on opposite sides of the International Date Line
        west_of_date_line = Coordinate(longitude=179.5, latitude=0)
        east_of_date_line = Coordinate(longitude=-179.5, latitude=0)

        # Correctly calculates ~111 km, not ~39,000 km
        distance = west_of_date_line.distance_to(east_of_date_line)
        assert distance == pytest.approx(111, abs=5)  # Should be about 111 km

    def test_polar_regions_example(self) -> None:
        """Test the polar regions example from lines 410-418."""
        north_pole = Coordinate(longitude=0, latitude=90)
        south_pole = Coordinate(longitude=0, latitude=-90)

        # Pole to pole distance
        distance = north_pole.distance_to(south_pole)
        # Documentation shows ~20,004 km (half Earth's circumference)
        assert distance == pytest.approx(20004, abs=50)

    def test_coordinate_validation_example(self) -> None:
        """Test the coordinate validation example from lines 423-433."""
        # Placemark without coordinates
        place_no_coords = Placemark(name="Unknown Location")
        north_pole = Coordinate(longitude=0, latitude=90)

        # Returns None for objects without valid coordinates
        distance = place_no_coords.distance_to(north_pole)
        assert distance is None

    def test_integration_with_querysets_example(self) -> None:
        """Test the integration with QuerySets example from lines 367-388."""
        # Create sample KML content with stores
        kml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Store A</name>
                    <Point>
                        <coordinates>-74.0, 40.7, 0</coordinates>
                    </Point>
                </Placemark>
                <Placemark>
                    <name>Store B</name>
                    <Point>
                        <coordinates>-73.95, 40.75, 0</coordinates>
                    </Point>
                </Placemark>
                <Placemark>
                    <name>Store C</name>
                    <Point>
                        <coordinates>-74.1, 40.6, 0</coordinates>
                    </Point>
                </Placemark>
            </Document>
        </kml>"""

        # Load KML
        kml = KMLFile.from_string(kml_content)

        # Find all stores within 50km of a location
        center_lat, center_lon = 40.7128, -74.006  # NYC

        nearby_stores = kml.placemarks.near(longitude=center_lon, latitude=center_lat, radius_km=50)

        # All three stores should be within 50km of NYC
        assert len(nearby_stores) == 3

        for store in nearby_stores:
            # Each store has distance methods available
            distance = store.distance_to((center_lon, center_lat))
            bearing = store.bearing_to((center_lon, center_lat))
            assert distance is not None
            assert distance < 50  # Within radius
            assert bearing is not None
            assert 0 <= bearing <= 360

    @pytest.mark.parametrize(
        "coord1,coord2,expected_km,tolerance",
        [
            ((-74.006, 40.7128), (-0.1276, 51.5074), 5567, 10),  # NYC to London
            ((139.6917, 35.6895), (-122.4194, 37.7749), 8280, 10),  # Tokyo to SF
            ((0, 0), (0, 0), 0, 0),  # Same point
        ],
    )
    def test_parametrized_distance_examples(
        self, coord1: tuple, coord2: tuple, expected_km: float, tolerance: float
    ) -> None:
        """Test distance calculation with various city pairs (pattern from instructions)."""
        c1 = Coordinate(longitude=coord1[0], latitude=coord1[1])
        c2 = Coordinate(longitude=coord2[0], latitude=coord2[1])

        distance = c1.distance_to(c2)
        assert distance is not None
        assert abs(distance - expected_km) <= tolerance

    def test_caching_behavior_example(
        self, nyc_placemark: Placemark, london_placemark: Placemark
    ) -> None:
        """Test the caching behavior mentioned in lines 443-447."""
        # These repeated calculations should be cached automatically
        # Just verify they work and produce consistent results
        distances = []
        for _ in range(10):
            distance = nyc_placemark.distance_to(london_placemark)
            distances.append(distance)

        # All distances should be identical (cached)
        assert all(d == distances[0] for d in distances)
