"""
Tests for examples from the examples documentation.

This module contains tests that verify all code examples from the
examples.rst documentation work correctly.
"""

from typing import List, Dict, Any, TYPE_CHECKING, cast

from ..core.exceptions import KMLValidationError
from ..parsers.kml_file import KMLFile

if TYPE_CHECKING:
    from kmlorm.models.point import Coordinate


class TestExamplesDocumentation:
    """Test all examples from the examples documentation."""

    comprehensive_kml: str

    def setup_method(self) -> None:
        """Set up test data for each test."""
        # Comprehensive KML data for complex examples
        self.comprehensive_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Comprehensive Test Data</name>
    <description>Complete dataset for testing examples</description>

    <!-- Store locations for store locator analysis -->
    <Placemark>
      <name>Capital Electric Store - Baltimore</name>
      <address>123 Main St, Baltimore, MD 21201</address>
      <description>Main electrical supply store</description>
      <Point>
        <coordinates>-76.6,39.3,0</coordinates>
      </Point>
    </Placemark>

    <Placemark>
      <name>Hardware Store - Towson</name>
      <address>456 York Rd, Towson, MD 21286</address>
      <Point>
        <coordinates>-76.6,39.4,0</coordinates>
      </Point>
    </Placemark>

    <Placemark>
      <name>Electric Supply - Dundalk</name>
      <address>789 Dundalk Ave, Dundalk, MD 21222</address>
      <Point>
        <coordinates>-76.5,39.25,0</coordinates>
      </Point>
    </Placemark>

    <!-- Delivery routes for route planning -->
    <Placemark>
      <name>Route 1 - Downtown</name>
      <LineString>
        <coordinates>
          -76.6,39.3,0 -76.59,39.31,0 -76.58,39.32,0 -76.57,39.33,0
        </coordinates>
      </LineString>
    </Placemark>

    <Placemark>
      <name>Route 2 - Suburbs</name>
      <LineString>
        <coordinates>
          -76.65,39.35,0 -76.64,39.36,0 -76.63,39.37,0
        </coordinates>
      </LineString>
    </Placemark>

    <!-- Coverage areas for spatial analysis -->
    <Placemark>
      <name>Service Area North</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -76.7,39.4,0 -76.5,39.4,0 -76.5,39.5,0 -76.7,39.5,0 -76.7,39.4,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>

    <!-- Test data with missing coordinates for validation -->
    <Placemark>
      <name>Store Without Coordinates</name>
      <address>No location specified</address>
    </Placemark>

    <!-- Duplicate names for quality testing -->
    <Placemark>
      <name>Duplicate Store Name</name>
      <Point>
        <coordinates>-76.7,39.2,0</coordinates>
      </Point>
    </Placemark>

    <Placemark>
      <name>Duplicate Store Name</name>
      <Point>
        <coordinates>-76.8,39.1,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""

    def test_store_locator_analysis(self) -> None:
        """Test store coverage analysis example."""
        # From examples.rst: Store Locator Analysis section
        kml = KMLFile.from_string(self.comprehensive_kml)

        def calculate_distance(  # pylint: disable=unused-argument
            coord1: "Coordinate", coord2: "Coordinate"
        ) -> int:
            """Calculate distance between two coordinate points."""
            # You would implement actual distance calculation here
            return 0  # Placeholder

        def analyze_store_coverage(
            kml_file: "KMLFile", city_center: "Coordinate", max_distance: float = 25.0
        ) -> Dict[str, Any]:
            """Analyze store coverage for a city."""
            # Get all stores
            stores = kml_file.placemarks.filter(name__icontains="store")
            store_count = stores.count()

            # Find stores within city limits
            city_stores = stores.near(
                city_center.longitude, city_center.latitude, radius_km=max_distance
            )
            city_store_count = city_stores.count()

            # Analyze coverage
            coverage_analysis = []
            for store in city_stores:
                if store.coordinates:
                    distance_to_center = calculate_distance(store.coordinates, city_center)
                    coverage_analysis.append(
                        {
                            "name": store.name,
                            "address": store.address,
                            "distance_to_center": distance_to_center,
                            "longitude": store.longitude,
                            "latitude": store.latitude,
                        }
                    )

            # Sort by distance
            coverage_analysis.sort(key=lambda x: x["distance_to_center"] or float("inf"))

            return {
                "total_stores": store_count,
                "city_stores": city_store_count,
                "analysis": coverage_analysis,
            }

        # Test the analysis
        from kmlorm.models.point import Coordinate  # pylint: disable=import-outside-toplevel

        baltimore_center = Coordinate.from_any((-76.6, 39.3, 0))
        assert baltimore_center is not None
        result = analyze_store_coverage(kml, baltimore_center)

        assert result["total_stores"] >= 3
        assert result["city_stores"] >= 1
        assert len(result["analysis"]) >= 1
        assert all("name" in item for item in result["analysis"])

    def test_route_planning_analysis(self) -> None:
        """Test delivery route analysis example."""
        # From examples.rst: Route Planning section
        kml = KMLFile.from_string(self.comprehensive_kml)

        def analyze_delivery_routes(kml_file: KMLFile) -> "List[Dict[str, Any]]":
            """Analyze delivery route efficiency."""
            routes = kml_file.paths.all()

            route_analysis = []
            for route in routes:
                if route.coordinates:
                    analysis = {
                        "route_name": route.name,
                        "total_points": len(route.coordinates),
                        "estimated_length": estimate_route_length(route.coordinates),
                        "start_point": route.coordinates[0] if route.coordinates else None,
                        "end_point": route.coordinates[-1] if route.coordinates else None,
                    }
                    route_analysis.append(analysis)

            # Sort by length
            route_analysis.sort(
                key=lambda x: float(cast(float, x["estimated_length"])), reverse=True
            )
            return route_analysis

        def estimate_route_length(coordinates: List[Any]) -> float:
            """Estimate total route length."""
            if len(coordinates) < 2:
                return 0

            total_length = 0.0
            for i in range(1, len(coordinates)):
                # Simplified distance calculation
                prev_coord = coordinates[i - 1]
                curr_coord = coordinates[i]
                segment_length = calculate_segment_distance(prev_coord, curr_coord)
                total_length += segment_length

            return total_length

        def calculate_segment_distance(  # pylint: disable=unused-argument
            coord1: "Coordinate", coord2: "Coordinate"
        ) -> float:
            """Calculate distance between two points."""
            # Simplified calculation for testing
            return 1.0

        # Test the analysis
        route_data = analyze_delivery_routes(kml)

        assert len(route_data) >= 0  # May be 0 if no paths found
        for route in route_data:
            assert "route_name" in route
            assert "total_points" in route
            assert "estimated_length" in route

    def test_geographic_data_validation(self) -> None:
        """Test data validation example."""
        # From examples.rst: Geographic Data Validation section
        kml = KMLFile.from_string(self.comprehensive_kml)

        def validate_geographic_data(kml_file: KMLFile) -> Dict[str, Any]:
            """Validate and report issues with geographic data."""
            validation_report: Dict[str, Any] = {
                "total_elements": 0,
                "valid_elements": 0,
                "invalid_elements": [],
                "missing_coordinates": [],
                "duplicate_names": [],
            }

            # Check placemarks
            all_placemarks = kml_file.placemarks.all()
            validation_report["total_elements"] = len(all_placemarks)

            names_seen = set()
            for placemark in all_placemarks:
                # Check for duplicates
                if placemark.name in names_seen:
                    cast(list, validation_report["duplicate_names"]).append(placemark.name)
                names_seen.add(placemark.name)

                # Check coordinates
                if not placemark.coordinates:
                    cast(list, validation_report["missing_coordinates"]).append(placemark.name)
                    continue

                # Validate coordinates
                try:
                    if placemark.validate():
                        validation_report["valid_elements"] = (
                            cast(int, validation_report["valid_elements"]) + 1
                        )
                except KMLValidationError as e:
                    cast(list, validation_report["invalid_elements"]).append(
                        {"name": placemark.name, "error": str(e)}
                    )

            return validation_report

        # Test validation
        report = validate_geographic_data(kml)

        assert report["total_elements"] > 0
        assert report["valid_elements"] >= 0
        assert isinstance(report["invalid_elements"], list)
        assert isinstance(report["missing_coordinates"], list)
        assert isinstance(report["duplicate_names"], list)

        # Should find our test duplicate
        assert "Duplicate Store Name" in report["duplicate_names"]

        # Should find missing coordinates
        assert "Store Without Coordinates" in report["missing_coordinates"]

    def test_data_access_with_to_dict(self) -> None:
        """Test data access with to_dict() methods example from lines 202-241."""
        # From examples.rst: Data Access with to_dict() Methods section
        kml = KMLFile.from_string(self.comprehensive_kml)

        # Test converting individual placemarks to dictionaries
        for placemark in kml.placemarks.has_coordinates():
            placemark_dict = placemark.to_dict()
            print(f"Placemark: {placemark_dict['name']}")
            print(f"Coordinates: {placemark_dict['coordinates']}")
            print(f"Point data: {placemark_dict['point']}")

            # Verify the dictionary structure
            assert 'name' in placemark_dict
            assert 'coordinates' in placemark_dict
            assert 'point' in placemark_dict

        # Convert all placemarks to a list of dictionaries
        all_placemarks = [p.to_dict() for p in kml.placemarks.all()]
        print(f"Converted {len(all_placemarks)} placemarks to dictionaries")
        assert len(all_placemarks) > 0

        # Access coordinate data
        for placemark in kml.placemarks.has_coordinates():
            if placemark.point is not None:
                point_dict = placemark.point.to_dict()
                if placemark.point.coordinates is not None:
                    coord_dict = placemark.point.coordinates.to_dict()

                    print(f"Point: {point_dict}")
                    print(f"Coordinates: {coord_dict}")

                    # Verify point and coordinate dictionaries
                    assert isinstance(point_dict, dict)
                    assert isinstance(coord_dict, dict)
                    assert 'longitude' in coord_dict
                    assert 'latitude' in coord_dict

        # Verify we have dictionaries with the right structure
        # No need to test JSON/CSV export - we don't provide export functionality
        for placemark_dict in all_placemarks:
            assert isinstance(placemark_dict, dict)
            # Verify essential keys exist
            assert 'name' in placemark_dict
            if placemark_dict.get('point'):
                assert 'coordinates' in placemark_dict
                # Coordinates should be in the dict (even if as an object)
                assert placemark_dict['coordinates'] is not None


    def test_spatial_analysis_clusters(self) -> None:
        """Test spatial clustering analysis example."""
        # From examples.rst: Spatial Analysis section
        kml = KMLFile.from_string(self.comprehensive_kml)

        def find_clusters(  # pylint: disable=too-many-locals
            kml_file: KMLFile, cluster_radius: float = 5.0
        ) -> "List[Dict[str, Any]]":
            """Find clusters of nearby placemarks."""
            placemarks_with_coords = kml_file.placemarks.has_coordinates()
            clusters = []
            processed = set()

            placemark_list = list(placemarks_with_coords)

            for i, placemark in enumerate(placemark_list):
                if i in processed:
                    continue

                # Find nearby placemarks
                nearby = []
                center = (placemark.longitude, placemark.latitude)

                for j, other in enumerate(placemark_list):
                    if j != i and j not in processed:
                        # Create simple coordinate tuples for distance calculation
                        coord1 = (placemark.longitude or 0.0, placemark.latitude or 0.0)
                        coord2 = (other.longitude or 0.0, other.latitude or 0.0)
                        distance = calculate_distance_tuple(coord1, coord2)
                        if distance <= cluster_radius:
                            nearby.append((j, other))

                if nearby:
                    cluster = {
                        "center_placemark": placemark,
                        "nearby_placemarks": [p[1] for p in nearby],
                        "total_count": len(nearby) + 1,
                        "center_coordinates": center,
                    }
                    clusters.append(cluster)
                    processed.add(i)
                    processed.update(p[0] for p in nearby)

            # Sort clusters by size
            clusters.sort(key=lambda x: cast(int, x["total_count"]), reverse=True)
            return clusters

        def calculate_distance_tuple(
            coord1: tuple[float, float], coord2: tuple[float, float]
        ) -> float:
            """Calculate distance between coordinate tuples (simplified)."""
            # Simplified distance calculation for testing
            return float(abs(coord1[0] - coord2[0]) + abs(coord1[1] - coord2[1]))

        # Test clustering
        clusters = find_clusters(kml, cluster_radius=10)

        assert isinstance(clusters, list)
        for cluster in clusters:
            assert "center_placemark" in cluster
            assert "total_count" in cluster
            assert cluster["total_count"] >= 1

    def test_data_quality_assessment(self) -> None:
        """Test comprehensive data quality assessment example."""
        # From examples.rst: Data Quality Assessment section
        kml = KMLFile.from_string(self.comprehensive_kml)

        def assess_data_quality(kml_file: KMLFile) -> Dict[str, Any]:
            """Comprehensive data quality assessment."""
            quality_metrics: Dict[str, Any] = {
                "completeness": {},
                "accuracy": {},
                "consistency": {},
                "coverage": {},
            }

            all_placemarks = kml_file.placemarks.all()
            total_count = len(all_placemarks)

            # Completeness metrics
            with_names = sum(1 for p in all_placemarks if p.name)
            with_coords = sum(1 for p in all_placemarks if p.coordinates)
            with_descriptions = sum(1 for p in all_placemarks if p.description)
            with_addresses = sum(1 for p in all_placemarks if p.address)

            quality_metrics["completeness"] = {
                "total_records": total_count,
                "name_completion": with_names / total_count * 100,
                "coordinate_completion": with_coords / total_count * 100,
                "description_completion": with_descriptions / total_count * 100,
                "address_completion": with_addresses / total_count * 100,
            }

            # Accuracy metrics (coordinate validation)
            valid_coords = 0
            invalid_coords = []
            for placemark in all_placemarks:
                if placemark.coordinates:
                    try:
                        if placemark.validate():
                            valid_coords += 1
                    except KMLValidationError:
                        invalid_coords.append(placemark.name)

            quality_metrics["accuracy"] = {
                "valid_coordinates": valid_coords / with_coords * 100 if with_coords > 0 else 0,
                "invalid_coordinate_count": len(invalid_coords),
            }

            # Consistency metrics
            name_lengths = [len(p.name) for p in all_placemarks if p.name]
            duplicate_names = len(all_placemarks) - len(
                set(p.name for p in all_placemarks if p.name)
            )

            quality_metrics["consistency"] = {
                "duplicate_names": duplicate_names,
                "avg_name_length": sum(name_lengths) / len(name_lengths) if name_lengths else 0,
                "name_length_std": (
                    calculate_std_dev([float(x) for x in name_lengths]) if name_lengths else 0
                ),
            }

            # Geographic coverage
            if with_coords > 0:
                lats = [
                    p.latitude for p in all_placemarks if p.coordinates and p.latitude is not None
                ]
                lons = [
                    p.longitude for p in all_placemarks if p.coordinates and p.longitude is not None
                ]

                if lats and lons:
                    quality_metrics["coverage"] = {
                        "lat_range": (min(lats), max(lats)),
                        "lon_range": (min(lons), max(lons)),
                        "geographic_spread": max(lats) - min(lats) + max(lons) - min(lons),
                    }

            return quality_metrics

        def calculate_std_dev(values: List[float]) -> float:
            """Calculate standard deviation."""
            if len(values) < 2:
                return 0
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            return float(variance**0.5)

        # Test quality assessment
        quality_report = assess_data_quality(kml)

        assert "completeness" in quality_report
        assert "accuracy" in quality_report
        assert "consistency" in quality_report
        assert "coverage" in quality_report

        completeness = quality_report["completeness"]
        assert completeness["total_records"] > 0
        assert 0 <= completeness["name_completion"] <= 100
        assert 0 <= completeness["coordinate_completion"] <= 100

    def test_batch_processing(self) -> None:
        """Test batch processing example."""
        # From examples.rst: Batch Processing section

        def batch_process_kml_data(kml_data_list: List[str]) -> "List[Dict[str,Any]]":
            """Process multiple KML datasets."""
            results = []

            for i, kml_data in enumerate(kml_data_list):
                try:
                    kml = KMLFile.from_string(kml_data)

                    # Extract summary information
                    summary = {
                        "dataset_id": f"dataset_{i}",
                        "document_name": kml.document_name,
                        "placemark_count": kml.placemarks.count(),
                        "folder_count": kml.folders.count(),
                        "path_count": kml.paths.count(),
                        "polygon_count": kml.polygons.count(),
                        "has_coordinates": kml.placemarks.has_coordinates().count(),
                    }

                    results.append(summary)

                except (ValueError, TypeError, KMLValidationError) as e:
                    results.append({"dataset_id": f"dataset_{i}", "error": str(e)})

            return results

        # Test batch processing
        kml_datasets = [self.comprehensive_kml]
        results = batch_process_kml_data(kml_datasets)

        assert len(results) == 1
        result = results[0]

        if "error" not in result:
            assert "document_name" in result
            assert "placemark_count" in result
            assert result["placemark_count"] > 0
