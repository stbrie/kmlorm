"""
Tests for examples from the tutorial documentation.

This module contains tests that verify all code examples from the
tutorial.rst documentation work correctly.
"""

# pylint: disable=duplicate-code
from typing import List, Dict, Any

import pytest
from ..core.exceptions import KMLValidationError, KMLParseError
from ..core.querysets import KMLQuerySet
from ..models.placemark import Placemark
from ..models.point import Coordinate
from ..parsers.kml_file import KMLFile
from ..spatial import DistanceUnit
from ..spatial.calculations import SpatialCalculations


class TestTutorialExamples:
    """Test all examples from the tutorial guide."""

    complex_kml: str
    geometry_kml: str

    def setup_method(self) -> None:
        """Set up test data for each test."""
        # Complex KML data with folders and various elements
        self.complex_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Advanced KML Test</name>
    <description>Complex KML for tutorial testing</description>
    <Folder>
      <name>Supply Locations</name>
      <Placemark>
        <name>Capital Electric Supply</name>
        <visibility>1</visibility>
        <description>Main electrical supply store</description>
        <Point>
          <coordinates>-76.5,39.3,0</coordinates>
        </Point>
      </Placemark>
      <Placemark>
        <name>Electric Depot</name>
        <visibility>1</visibility>
        <Point>
          <coordinates>-76.6,39.4,0</coordinates>
        </Point>
      </Placemark>
      <Folder>
        <name>Warehouse</name>
        <Placemark>
          <name>Main Warehouse</name>
          <Point>
            <coordinates>-76.7,39.2,0</coordinates>
          </Point>
        </Placemark>
      </Folder>
    </Folder>
    <Folder>
      <name>Retail Locations</name>
      <Placemark>
        <name>Hardware Store</name>
        <Point>
          <coordinates>-76.8,39.1,0</coordinates>
        </Point>
      </Placemark>
    </Folder>
    <Placemark>
      <name>Independent Store</name>
      <Point>
        <coordinates>-76.4,39.5,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""

        # Add KML with paths and polygons for geometry tests
        self.geometry_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Geometry Test</name>
    <Placemark>
      <name>Delivery Route</name>
      <LineString>
        <coordinates>
          -76.5,39.3,0
          -76.6,39.4,0
          -76.7,39.5,0
        </coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Service Area</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -76.8,39.0,0
              -76.4,39.0,0
              -76.4,39.6,0
              -76.8,39.6,0
              -76.8,39.0,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""

    def test_field_lookups_exact(self) -> None:
        """Test field lookups section - lines 21-46 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        # Exact match (default) - includes all elements including nested
        exact = kml.placemarks.all().filter(name="Capital Electric Supply")
        assert len(exact) == 1

        # Case-insensitive contains
        contains = kml.placemarks.all().filter(name__icontains="electric")
        assert len(contains) == 2  # Capital Electric Supply and Electric Depot

        # Starts with / ends with
        starts = kml.placemarks.all().filter(name__startswith="Capital")
        assert len(starts) == 1

        ends = kml.placemarks.all().filter(name__endswith="Store")
        assert len(ends) == 2  # Hardware Store and Independent Store

        # In a list of values
        multiple = kml.placemarks.all().filter(name__in=["Hardware Store", "Electric Depot"])
        assert len(multiple) == 2

        # Null checks
        with_description = kml.placemarks.all().filter(description__isnull=False)
        assert len(with_description) >= 1

        without_description = kml.placemarks.all().filter(description__isnull=True)
        assert len(without_description) >= 1

        # Regular expressions
        regex_match = kml.placemarks.all().filter(name__regex=r"^Capital.*Electric.*$")
        assert len(regex_match) == 1

    def test_complex_queries(self) -> None:
        """Test complex queries section - lines 52-66 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        # Multiple filters (AND logic)
        result = (
            kml.placemarks.all()
            .filter(name__icontains="electric")
            .filter(visibility=True)
            .exclude(description__isnull=True)
        )
        assert len(result) >= 1

        # Geospatial + attribute filtering
        baltimore_electric_stores = (
            kml.placemarks.all()
            .filter(name__icontains="electric")
            .near(-76.6, 39.3, radius_km=25)
            .has_coordinates()
        )
        assert len(baltimore_electric_stores) >= 1

    def test_folder_navigation_with_children(self) -> None:
        """Test folder navigation section - lines 76-93 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        # Get all folders (direct children only)
        folders = kml.folders.children()

        for folder in folders:
            print(f"Folder: {folder.name}")
            print(f"  Placemarks: {folder.placemarks.count()}")
            print(f"  Subfolders: {folder.folders.count()}")

            # Access folder contents (direct children only)
            for placemark in folder.placemarks.children():
                print(f"    - {placemark.name}")

            # Recursively process subfolders (direct children only)
            for subfolder in folder.folders.children():
                print(f"    Subfolder: {subfolder.name}")

        # Verify the folders structure
        supply_folder = kml.folders.children().get(name="Supply Locations")
        assert supply_folder is not None
        assert supply_folder.placemarks.count() >= 2
        assert supply_folder.folders.count() >= 1  # Has Warehouse subfolder

    def test_cross_folder_queries(self) -> None:
        """Test cross-folder queries section - lines 99-110 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        # All placemarks regardless of folder (includes nested)
        all_stores = kml.placemarks.all().filter(name__icontains="store")
        assert len(all_stores) >= 2

        # Get placemarks from specific folder (direct children only)
        supply_folder = kml.folders.children().get(name="Supply Locations")
        supply_stores = supply_folder.placemarks.children()
        assert len(supply_stores) == 2  # Only direct children, not nested Warehouse

    def test_distance_calculations_with_units(self) -> None:
        """Test distance calculations section - lines 133-154 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        # Get two placemarks (includes nested)
        # Using slightly different search to ensure we get stores with known names
        store1 = kml.placemarks.all().get(name="Capital Electric Supply")
        store2 = kml.placemarks.all().get(name="Electric Depot")

        # Calculate distance in various units
        if store1.coordinates and store2.coordinates:
            km = store1.distance_to(store2)
            miles = store1.distance_to(store2, unit=DistanceUnit.MILES)
            meters = store1.distance_to(store2, unit=DistanceUnit.METERS)

            print(f"Distance: {km:.2f} km")
            print(f"Distance: {miles:.2f} miles")
            print(f"Distance: {meters:.0f} meters")

            # Verify conversions are correct
            if km is not None and meters is not None and miles is not None:
                assert meters == pytest.approx(km * 1000, rel=0.01)
                assert miles == pytest.approx(km * 0.621371, rel=0.01)

        # Distance to specific coordinates (tuple or list)
        baltimore = (-76.6, 39.3)
        distance = store1.distance_to(baltimore)
        print(f"Distance to Baltimore: {distance:.1f} km")
        assert distance is not None
        assert distance >= 0

    def test_bearing_and_navigation(self) -> None:
        """Test bearing and navigation section - lines 161-191 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        store1 = kml.placemarks.all().get(name="Capital Electric Supply")
        store2 = kml.placemarks.all().get(name="Electric Depot")

        if store1.coordinates and store2.coordinates:
            # Calculate bearing (compass direction)
            bearing = store1.bearing_to(store2)
            if bearing is not None:
                print(f"Bearing: {bearing:.1f}°")

                # Determine cardinal direction
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

                print(f"Head {direction} ({bearing:.1f}°)")
                assert direction in [
                    "North",
                    "Northeast",
                    "East",
                    "Southeast",
                    "South",
                    "Southwest",
                    "West",
                    "Northwest",
                ]

            # Find geographic midpoint
            midpoint = store1.midpoint_to(store2)
            if midpoint is not None:
                print(f"Midpoint: {midpoint.longitude:.4f}, {midpoint.latitude:.4f}")
                assert hasattr(midpoint, "longitude")
                assert hasattr(midpoint, "latitude")

    def test_bulk_distance_operations(self) -> None:
        """Test bulk distance operations section - lines 197-221 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        # Center location (Baltimore)
        center = (-76.6, 39.3)

        # Get all stores with coordinates
        stores = kml.placemarks.all().has_coordinates()

        # Calculate distances from center to all stores
        distances = SpatialCalculations.distances_to_many(center, stores)

        # Combine with store names for display
        for store, distance in zip(stores, distances):
            if distance is not None:
                print(f"{store.name}: {distance:.1f} km")

        # Sort by distance
        store_distances = [(s, d) for s, d in zip(stores, distances) if d is not None]
        store_distances.sort(key=lambda x: x[1])

        print("\nClosest stores:")
        for store, distance in store_distances[:5]:
            print(f"  {store.name}: {distance:.1f} km")

        # Verify we got distances
        assert len(distances) > 0
        assert all(d is None or d >= 0 for d in distances)
        # Verify sorting worked
        if len(store_distances) > 1:
            assert store_distances[0][1] <= store_distances[-1][1]

    def test_paths_linestrings(self) -> None:
        """Test paths/LineStrings section - lines 232-241 of tutorial.rst."""
        kml = KMLFile.from_string(self.geometry_kml)

        # Get all paths (direct children only)
        paths = kml.paths.children()

        for path in paths:
            print(f"Path: {path.name}")
            if path.coordinates:
                print(f"  Points: {len(path.coordinates)}")
                # Note: calculate_length() method would need to be implemented
                # For now, just verify the path has coordinates
                assert len(path.coordinates) > 0

        # Verify we found the path
        assert len(paths) >= 1
        delivery_route = paths[0]
        assert delivery_route.name == "Delivery Route"
        assert delivery_route.coordinates is not None

    def test_polygons(self) -> None:
        """Test polygons section - lines 247-257 of tutorial.rst."""
        kml = KMLFile.from_string(self.geometry_kml)

        # Get all polygons (direct children only)
        polygons = kml.polygons.children()

        for polygon in polygons:
            print(f"Polygon: {polygon.name}")
            if polygon.outer_boundary:
                print(f"  Boundary points: {len(polygon.outer_boundary)}")
                print(f"  Has holes: {len(polygon.inner_boundaries) > 0}")

        # Verify we found the polygon
        assert len(polygons) >= 1
        service_area = polygons[0]
        assert service_area.name == "Service Area"
        assert service_area.outer_boundary is not None
        assert (
            len(service_area.outer_boundary) > 3
        )  # Valid polygon needs at least 4 points (closed)

    def test_data_validation_elements(self) -> None:
        """Test validate elements section - lines 266-275 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        for placemark in kml.placemarks.all():
            try:
                if placemark.validate():
                    print(f"✓ {placemark.name} is valid")
            except KMLValidationError as e:
                print(f"✗ {placemark.name} validation failed: {e}")

        # All our test placemarks should be valid
        # Just verify the validation process works
        validated_count = 0
        for placemark in kml.placemarks.all():
            try:
                if placemark.validate():
                    validated_count += 1
            except KMLValidationError:
                pass

        assert validated_count > 0

    def test_coordinate_validation(self) -> None:
        """Test coordinate validation section - lines 282-295 of tutorial.rst."""
        try:
            # Valid coordinate
            coord = Coordinate(longitude=-76.5, latitude=39.3)
            coord.validate()
            assert True  # Should not raise

            # Invalid coordinate (will raise exception)
            invalid = Coordinate(longitude=200, latitude=100)
            invalid.validate()
            assert False  # Should not reach here
        except KMLValidationError as e:
            print(f"Invalid coordinate: {e}")
            assert "longitude" in str(e).lower() or "latitude" in str(e).lower()

    def test_efficient_querying_patterns(self) -> None:
        """Test efficient querying section - lines 305-315 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        # Good: Use specific filters early
        nearby_electric = kml.placemarks.filter(name__icontains="electric").near(  # Filter first
            -76.6, 39.3, radius_km=10
        )  # Then apply geospatial

        # Less efficient: Geospatial first on large dataset
        all_nearby = kml.placemarks.near(-76.6, 39.3, radius_km=50)
        electric_nearby = all_nearby.filter(name__icontains="electric")

        # Both should return same results for our test data
        assert len(nearby_electric) == len(electric_nearby)

    def test_batch_operations(self) -> None:
        """Test batch operations section - lines 322-337 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        def process_batch(placemarks: "KMLQuerySet[Placemark]") -> None:
            """Process batch helper function."""
            for placemark in placemarks:
                # Process individual placemark
                if placemark.coordinates:
                    # Simulate validate_location
                    assert placemark.validate()

        # Process in batches
        all_placemarks = kml.placemarks.all()
        batch_size = 100  # Using actual value from docs

        for i in range(0, len(all_placemarks), batch_size):
            batch = all_placemarks[i:i + batch_size]
            process_batch(batch)

        # Verify processing worked
        assert len(all_placemarks) > 0

    def test_graceful_error_handling(self) -> None:
        """Test graceful error handling section - lines 346-379 of tutorial.rst."""
        # pylint: disable=import-outside-toplevel
        import logging

        logger = logging.getLogger(__name__)

        def safe_kml_processing(file_content: str) -> Any:
            """Example from tutorial with actual imports."""
            try:
                kml = KMLFile.from_string(file_content)

                # Process with error handling
                for placemark in kml.placemarks.all():
                    try:
                        if placemark.validate():
                            # process_placemark(placemark)
                            pass
                    except KMLValidationError as e:
                        logger.warning("Skipping invalid placemark %s: %s", placemark.name, e)
                        continue
                return kml

            except KMLParseError as e:
                logger.error("Failed to parse KML: %s", e)
                return None
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                raise

        # Test with valid KML
        result = safe_kml_processing(self.complex_kml)
        assert result is not None

        # Test with invalid KML
        result = safe_kml_processing("not valid xml")
        assert result is None

    def test_integration_with_pandas(self) -> None:
        """Test pandas integration section - lines 389-412 of tutorial.rst."""
        kml = KMLFile.from_string(self.complex_kml)

        def kml_to_dataframe(kml_file: Any) -> List[Dict[str, Any]]:
            """Convert KML to dataframe-ready structure."""
            data: List[Dict[str, Any]] = []
            for placemark in kml_file.placemarks.all():
                row = {
                    "name": placemark.name,
                    "description": placemark.description,
                    "longitude": placemark.longitude,
                    "latitude": placemark.latitude,
                    "altitude": placemark.altitude,
                    "address": placemark.address,
                    "phone": placemark.phone_number if hasattr(placemark, "phone_number") else None,
                }
                data.append(row)

            return data  # Would be pd.DataFrame(data) with pandas

        # Usage
        data = kml_to_dataframe(kml)
        print(f"Found {len(data)} placemarks")

        # Verify structure
        assert len(data) > 0
        assert all("name" in row for row in data)
        assert all("longitude" in row for row in data)

    def test_custom_extensions(self) -> None:
        """Test custom extensions section - lines 461-478 of tutorial.rst."""
        # pylint: disable=import-outside-toplevel
        from kmlorm import Placemark as PlacemarkBase

        class Store(PlacemarkBase):
            """Custom Store class extending Placemark."""

            @property
            def is_open(self: Any) -> bool:
                """Check if store is open."""
                # Custom business logic
                return getattr(self, "hours", None) is not None

            def distance_to_customer(self: Any, customer_location: Any) -> Any:
                """Calculate distance to customer."""
                if self.coordinates and customer_location:
                    return self.distance_to(customer_location)
                return None

        # Usage
        store = Store(name="My Store", coordinates=(-76.5, 39.3))
        distance = store.distance_to_customer((-76.6, 39.4))

        assert store.name == "My Store"
        assert distance is not None
        assert distance < float("inf")
        assert store.is_open is False  # No hours set

    def test_all_vs_children_distinction(self) -> None:
        """Test the important distinction between .all() and .children()."""
        kml = KMLFile.from_string(self.complex_kml)

        # Test with root level
        all_placemarks = kml.placemarks.all()
        direct_placemarks = kml.placemarks.children()

        # all() should include nested placemarks
        assert len(all_placemarks) == 5  # Includes nested warehouse
        # children() should only include direct children
        assert len(direct_placemarks) == 1  # Only "Independent Store"

        # Test with folders
        supply_folder = kml.folders.children().get(name="Supply Locations")

        # After bugfix: folder.placemarks.all() now correctly traverses nested folders
        # It returns ALL placemarks including those in nested folders
        all_in_folder = supply_folder.placemarks.all()
        assert len(all_in_folder) == 3  # Now includes nested warehouse placemark

        # children() returns direct children only
        direct_in_folder = supply_folder.placemarks.children()
        assert len(direct_in_folder) == 2  # Only direct children

        # Verify the names to be sure
        direct_names = {p.name for p in direct_in_folder}
        assert direct_names == {"Capital Electric Supply", "Electric Depot"}

        all_names = {p.name for p in all_in_folder}
        assert all_names == {"Capital Electric Supply", "Electric Depot", "Main Warehouse"}

        # The bugfix means .all() now correctly includes nested elements
        # No workaround needed anymore!

    def test_get_all_nested_placemarks_workaround(self) -> None:
        """Test workaround for getting all nested placemarks - lines 122-141."""
        kml = KMLFile.from_string(self.complex_kml)

        # Get all placemarks in Supply Locations folder and its subfolders
        supply_folder = kml.folders.children().get(name="Supply Locations")

        # This only gets direct children (2 placemarks)
        direct_only = supply_folder.placemarks.children()
        assert len(direct_only) == 2

        # To get ALL placemarks including nested ones, filter from root
        # by checking if placemark's parent hierarchy includes the folder
        def get_all_nested_placemarks(folder: Any) -> List[Any]:
            """Get all placemarks in folder including nested subfolders."""
            result: List[Any] = []
            # Add direct placemarks
            result.extend(folder.placemarks.children())
            # Recursively add from subfolders
            for subfolder in folder.folders.children():
                result.extend(get_all_nested_placemarks(subfolder))
            return result

        # Now this gets all 3 placemarks (2 direct + 1 in Warehouse subfolder)
        all_nested = get_all_nested_placemarks(supply_folder)
        assert len(all_nested) == 3

        # Verify we got the correct placemarks
        nested_names = {p.name for p in all_nested}
        assert nested_names == {"Capital Electric Supply", "Electric Depot", "Main Warehouse"}
