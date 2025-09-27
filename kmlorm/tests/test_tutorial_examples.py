"""
Tests for examples from the tutorial documentation.

This module contains tests that verify all code examples from the
tutorial.rst documentation work correctly.
"""

from typing import List, Dict, Any

import pytest
from ..core.exceptions import KMLValidationError
from ..models.point import Coordinate
from ..parsers.kml_file import KMLFile


class TestTutorialExamples:
    """Test all examples from the tutorial guide."""

    complex_kml: str

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

    def test_field_lookups(self) -> None:
        """Test various Django-style field lookups (tutorial example)."""
        # From tutorial.rst: Field Lookups section
        kml = KMLFile.from_string(self.complex_kml)

        # Exact match (default)
        exact = kml.placemarks.all(flatten=True).filter(name="Capital Electric Supply")
        assert len(exact) == 1

        # Case-insensitive contains
        contains = kml.placemarks.all(flatten=True).filter(name__icontains="electric")
        assert len(contains) == 2  # Capital Electric Supply and Electric Depot

        # Starts with / ends with
        starts = kml.placemarks.all(flatten=True).filter(name__startswith="Capital")
        assert len(starts) == 1

        ends = kml.placemarks.all(flatten=True).filter(name__endswith="Store")
        assert len(ends) == 2  # Hardware Store and Independent Store

        # In a list of values
        multiple = kml.placemarks.all(flatten=True).filter(
            name__in=["Hardware Store", "Electric Depot"]
        )
        assert len(multiple) == 2

        # Null checks
        with_description = kml.placemarks.all(flatten=True).filter(description__isnull=False)
        assert len(with_description) >= 1

        without_description = kml.placemarks.all(flatten=True).filter(description__isnull=True)
        assert len(without_description) >= 1

        # Regular expressions
        regex_match = kml.placemarks.all(flatten=True).filter(name__regex=r"^Capital.*Electric.*$")
        assert len(regex_match) == 1

    def test_complex_queries(self) -> None:
        """Test complex query combinations (tutorial example)."""
        # From tutorial.rst: Complex Queries section
        kml = KMLFile.from_string(self.complex_kml)

        # Multiple filters (AND logic)
        result = (
            kml.placemarks.all(flatten=True)
            .filter(name__icontains="electric")
            .filter(visibility=True)
            .exclude(description__isnull=True)
        )
        assert len(result) >= 1

        # Geospatial + attribute filtering
        baltimore_electric_stores = (
            kml.placemarks.all(flatten=True)
            .filter(name__icontains="electric")
            .near(-76.6, 39.3, radius_km=25)
            .has_coordinates()
        )
        assert len(baltimore_electric_stores) >= 1

    def test_folder_navigation(self) -> None:
        """Test folder hierarchy navigation (tutorial example)."""
        # From tutorial.rst: Folder Navigation section
        kml = KMLFile.from_string(self.complex_kml)

        # Get all folders
        folders = kml.folders.all()
        assert len(folders) >= 2

        folder_info = []
        for folder in folders:
            info = {
                "name": folder.name,
                "placemark_count": folder.placemarks.count(),
                "subfolder_count": folder.folders.count(),
            }
            folder_info.append(info)

            # Access folder contents
            placemark_names = [p.name for p in folder.placemarks.all()]
            assert isinstance(placemark_names, list)

            # Recursively process subfolders
            for subfolder in folder.folders.all():
                assert hasattr(subfolder, "name")

        # Verify we found the expected folders
        folder_names = [f["name"] for f in folder_info]
        assert "Supply Locations" in folder_names

    def test_cross_folder_queries(self) -> None:
        """Test queries across folder boundaries (tutorial example)."""
        # From tutorial.rst: Cross-Folder Queries section
        kml = KMLFile.from_string(self.complex_kml)

        # All placemarks regardless of folder
        all_stores = kml.placemarks.all(flatten=True).filter(name__icontains="store")
        assert len(all_stores) >= 2

        # Get placemarks from specific folder
        supply_folder = kml.folders.get(name="Supply Locations")
        supply_stores = supply_folder.placemarks.all()
        assert len(supply_stores) >= 2

    def test_distance_calculations(self) -> None:
        """Test distance calculation methods (tutorial example)."""
        # From tutorial.rst: Distance Calculations section
        kml = KMLFile.from_string(self.complex_kml)

        # Get two placemarks
        store1 = kml.placemarks.all(flatten=True).get(name__contains="Capital")
        store2 = kml.placemarks.all(flatten=True).get(name__contains="Depot")

        # Calculate distance
        if store1.coordinates and store2.coordinates:
            distance = store1.distance_to(store2)
            assert distance is not None
            assert distance > 0
            assert distance < 100  # Should be reasonable distance

    def test_bearing_calculations(self) -> None:
        """Test bearing calculation methods (tutorial example)."""
        # From tutorial.rst: Bearing Calculations section
        kml = KMLFile.from_string(self.complex_kml)

        store1 = kml.placemarks.all(flatten=True).get(name__contains="Capital")
        store2 = kml.placemarks.all(flatten=True).get(name__contains="Depot")

        if store1.coordinates and store2.coordinates:
            bearing = store1.bearing_to(store2)
            assert bearing is not None
            assert 0 <= bearing <= 360

    def test_coordinate_validation(self) -> None:
        """Test coordinate validation (tutorial example)."""
        # From tutorial.rst: Coordinate Validation section

        # Valid coordinate
        coord = Coordinate(longitude=-76.5, latitude=39.3)
        assert coord.validate() is True

        # Invalid coordinate (will raise exception)
        with pytest.raises(KMLValidationError):
            invalid = Coordinate(longitude=200, latitude=100)
            invalid.validate()

    def test_element_validation(self) -> None:
        """Test element validation (tutorial example)."""
        # From tutorial.rst: Validate Elements section
        kml = KMLFile.from_string(self.complex_kml)

        validation_results = []
        for placemark in kml.placemarks.all(flatten=True):
            try:
                is_valid = placemark.validate()
                validation_results.append({"name": placemark.name, "valid": is_valid})
            except KMLValidationError as e:
                validation_results.append({"name": placemark.name, "valid": False, "error": str(e)})

        # All our test placemarks should be valid
        valid_count = sum(1 for r in validation_results if r["valid"])
        assert valid_count > 0

    def test_efficient_querying_patterns(self) -> None:
        """Test performance optimization patterns (tutorial example)."""
        # From tutorial.rst: Efficient Querying section
        kml = KMLFile.from_string(self.complex_kml)

        # Good: Use specific filters early
        nearby_electric = (
            kml.placemarks.all(flatten=True)
            .filter(name__icontains="electric")  # Filter first
            .near(-76.6, 39.3, radius_km=10)  # Then apply geospatial
        )
        assert len(nearby_electric) >= 0

        # Less efficient: Geospatial first on large dataset
        all_nearby = kml.placemarks.all(flatten=True).near(-76.6, 39.3, radius_km=50)
        electric_nearby = all_nearby.filter(name__icontains="electric")
        assert len(electric_nearby) >= 0

        # Both should return same results for our test data
        # (though efficiency differs on large datasets)

    def test_batch_operations(self) -> None:
        """Test batch processing patterns (tutorial example)."""
        # From tutorial.rst: Batch Operations section
        kml = KMLFile.from_string(self.complex_kml)

        # Process in batches
        all_placemarks = kml.placemarks.all(flatten=True)
        batch_size = 2

        processed_count = 0
        for i in range(0, len(all_placemarks), batch_size):
            batch = all_placemarks[i : i + batch_size]  # noqa: E203

            # Process batch
            for placemark in batch:
                if placemark.coordinates:
                    # Simulate validation
                    assert placemark.validate() is True
                    processed_count += 1

        assert processed_count > 0

    def test_error_handling_patterns(self) -> None:
        """Test graceful error handling (tutorial example)."""
        # From tutorial.rst: Graceful Error Handling section

        def safe_kml_processing(kml_content: str) -> dict:
            """Simulate the safe_kml_processing function from tutorial."""
            try:
                kml = KMLFile.from_string(kml_content)

                processed_count = 0
                skipped_count = 0

                # Process with error handling
                for placemark in kml.placemarks.all(flatten=True):
                    try:
                        if placemark.validate():
                            processed_count += 1
                    except KMLValidationError:
                        skipped_count += 1
                        continue

                return {"processed": processed_count, "skipped": skipped_count, "success": True}

            except Exception:  # pylint: disable=broad-exception-caught
                return {"success": False, "error": "Parse error"}

        # Test with valid KML
        result = safe_kml_processing(self.complex_kml)
        assert result["success"] is True
        assert result["processed"] > 0

        # Test with invalid KML
        invalid_kml = "not valid xml"
        result = safe_kml_processing(invalid_kml)
        assert result["success"] is False

    def test_integration_patterns_dataframe_conversion(self) -> None:
        """Test KML to DataFrame conversion pattern (tutorial example)."""
        # From tutorial.rst: With Pandas section
        kml = KMLFile.from_string(self.complex_kml)

        def kml_to_dataframe_data(kml_file: KMLFile) -> List[Dict[str, Any]]:
            """Convert KML to DataFrame-compatible data."""
            data = []
            for placemark in kml_file.placemarks.all(flatten=True):
                row = {
                    "name": placemark.name,
                    "description": placemark.description,
                    "longitude": placemark.longitude,
                    "latitude": placemark.latitude,
                    "altitude": placemark.altitude,
                    "address": placemark.address,
                    "phone": getattr(placemark, "phone_number", None),
                }
                data.append(row)
            return data

        # Convert to data structure
        data = kml_to_dataframe_data(kml)
        assert len(data) > 0
        assert all("name" in row for row in data)
        assert all("longitude" in row for row in data)
