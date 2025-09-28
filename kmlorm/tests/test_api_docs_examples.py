"""
Tests for examples from the API documentation.

This module contains tests that verify all code examples from the
API reference documentation work correctly.
"""

# pylint: disable=duplicate-code
from typing import Any
from unittest.mock import mock_open, patch

import pytest
from ..core.exceptions import (
    KMLParseError,
    KMLValidationError,
    KMLElementNotFound,
)
from ..models.point import Coordinate
from ..models.placemark import Placemark
from ..parsers.kml_file import KMLFile


class TestAPIExamples:
    """Test all examples from the API documentation."""

    api_test_kml: str

    @pytest.fixture(autouse=True)
    def setup_kml_data(self) -> None:
        """Set up test data using fixture from conftest."""
        # Use a custom KML for API tests that matches documentation examples
        self.api_test_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>API Test Document</name>
    <description>Test data for API examples</description>
    <Placemark>
      <name>Test Store A</name>
      <address>123 Main St, City, State</address>
      <description>First test store</description>
      <Point>
        <coordinates>-76.5,39.3,100</coordinates>
      </Point>
    </Placemark>
    <Placemark>
      <name>Test Store B</name>
      <address>456 Oak Ave, Town, State</address>
      <Point>
        <coordinates>-76.6,39.4,50</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""

    def test_coordinate_creation_examples(self) -> None:
        """Test coordinate creation examples from coordinates.rst."""
        # From api/coordinates.rst: Creating Coordinates section

        # From tuple
        coord1 = Coordinate.from_tuple((-76.5, 39.3, 100))
        assert coord1.longitude == -76.5
        assert coord1.latitude == 39.3
        assert coord1.altitude == 100

        # From string
        coord2 = Coordinate.from_string("-76.5,39.3,100")
        assert coord2.longitude == -76.5
        assert coord2.latitude == 39.3
        assert coord2.altitude == 100

        # Direct creation
        coord3 = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)
        assert coord3.longitude == -76.5
        assert coord3.latitude == 39.3
        assert coord3.altitude == 100

        # From various formats
        coord4 = Coordinate.from_any((-76.5, 39.3))
        assert coord4.longitude == -76.5
        assert coord4.latitude == 39.3
        assert coord4.altitude == 0  # Default

        coord5 = Coordinate.from_any("-76.5,39.3")
        assert coord5.longitude == -76.5
        assert coord5.latitude == 39.3

        coord6 = Coordinate.from_any([-76.5, 39.3, 0])
        assert coord6.longitude == -76.5
        assert coord6.latitude == 39.3
        assert coord6.altitude == 0

    def test_coordinate_properties_examples(self) -> None:
        """Test coordinate property access examples from coordinates.rst."""
        # From api/coordinates.rst: Accessing Properties section

        coord = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)

        # Test property access
        assert coord.longitude == -76.5
        assert coord.latitude == 39.3
        assert coord.altitude == 100

        # Test string representation
        coord_str = str(coord)
        assert "-76.5" in coord_str
        assert "39.3" in coord_str

    def test_coordinate_validation_examples(self) -> None:
        """Test coordinate validation examples from coordinates.rst."""
        # From api/coordinates.rst: Validation section

        # Valid coordinate
        valid_coord = Coordinate(longitude=-76.5, latitude=39.3)
        assert valid_coord.validate() is True

        # Invalid coordinate (will raise exception)
        with pytest.raises(KMLValidationError):
            invalid_coord = Coordinate(longitude=200, latitude=100)
            invalid_coord.validate()

    def test_coordinate_integration_examples(self) -> None:
        """Test coordinate integration examples from coordinates.rst."""
        # From api/coordinates.rst: Integration with KML Elements section
        kml = KMLFile.from_string(self.api_test_kml)

        for placemark in kml.placemarks.all():
            # Access coordinates directly
            if placemark.longitude and placemark.latitude:
                assert isinstance(placemark.longitude, float)
                assert isinstance(placemark.latitude, float)

            # Get the full coordinate object
            coord = placemark.coordinates
            if coord:
                assert hasattr(coord, "longitude")
                assert hasattr(coord, "latitude")
                assert hasattr(coord, "altitude")

    def test_exception_handling_parse_errors(self) -> None:
        """Test parse error handling examples from exceptions.rst."""
        # From api/exceptions.rst: Handling Parse Errors section

        invalid_kml = "not valid xml content"

        with pytest.raises(KMLParseError):
            KMLFile.from_string(invalid_kml)

    def test_exception_handling_query_errors(self) -> None:
        """Test query error handling examples from exceptions.rst."""
        # From api/exceptions.rst: Handling Query Errors section

        kml = KMLFile.from_string(self.api_test_kml)

        # Test KMLElementNotFound
        with pytest.raises(KMLElementNotFound):
            kml.placemarks.get(name="Nonexistent Store")

        # Test successful get
        store = kml.placemarks.get(name="Test Store A")
        assert store.name == "Test Store A"

        # Test multiple elements (would raise KMLMultipleElementsReturned in real scenario)
        # For our test data, this should work since we have unique names

    def test_exception_handling_validation_errors(self) -> None:
        """Test validation error handling examples from exceptions.rst."""
        # From api/exceptions.rst: Handling Validation Errors section

        with pytest.raises(KMLValidationError):
            # Invalid coordinates
            placemark = Placemark(coordinates=(200, 100))  # Out of valid range
            placemark.validate()

    def test_exception_best_practices(self) -> None:
        """Test exception handling best practices from exceptions.rst."""
        # From api/exceptions.rst: Best Practices section

        def load_kml_safely(kml_content: str) -> KMLFile:
            """Test the safe loading pattern."""
            try:
                return KMLFile.from_string(kml_content)
            except KMLParseError as e:
                # Log error in real code
                raise ValueError(f"Invalid KML content: {e}") from e
            except Exception as e:
                # Log error in real code
                raise RuntimeError(f"Failed to load KML: {e}") from e

        # Test with valid KML
        try:
            kml = load_kml_safely(self.api_test_kml)
            assert isinstance(kml, KMLFile)
        except ValueError:
            pass

        # Test with invalid KML
        with pytest.raises(ValueError):
            load_kml_safely("invalid xml")

    def test_kmlfile_loading_examples(self) -> None:
        """Test KMLFile loading examples from kmlfile.rst."""
        # From api/kmlfile.rst: Usage Examples section

        # Test from_string
        kml = KMLFile.from_string(self.api_test_kml)
        assert isinstance(kml, KMLFile)
        assert kml.document_name == "API Test Document"

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_kmlfile_from_file_example(self, mock_exists: Any, mock_file: Any) -> None:
        """Test KMLFile.from_file example from kmlfile.rst."""
        # From api/kmlfile.rst: Loading from File section
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.api_test_kml

        kml = KMLFile.from_file("test.kml")
        assert isinstance(kml, KMLFile)

    def test_kmlfile_properties_examples(self) -> None:
        """Test KMLFile property access examples from kmlfile.rst."""
        # From api/kmlfile.rst: Properties section
        kml = KMLFile.from_string(self.api_test_kml)

        # Document properties
        assert kml.document_name == "API Test Document"
        assert kml.document_description == "Test data for API examples"

        # Element counts
        counts = kml.element_counts()
        assert isinstance(counts, dict)
        assert "placemarks" in counts
        assert counts["placemarks"] == 2

        # All elements
        all_elements = kml.all_elements()
        assert len(all_elements) >= 2

    def test_models_basic_usage_examples(self) -> None:
        """Test basic model usage examples from models.rst."""
        # From api/models.rst: Basic Usage section
        kml = KMLFile.from_string(self.api_test_kml)

        # Access placemarks
        placemarks = kml.placemarks.all()
        assert len(placemarks) == 2

        # Test placemark properties
        for placemark in placemarks:
            assert hasattr(placemark, "name")
            assert hasattr(placemark, "coordinates")
            assert hasattr(placemark, "address")

            # Test coordinate access
            if placemark.coordinates:
                assert hasattr(placemark, "longitude")
                assert hasattr(placemark, "latitude")
                assert hasattr(placemark, "altitude")

    def test_querysets_basic_filtering_examples(self) -> None:
        """Test basic filtering examples from querysets.rst."""
        # From api/querysets.rst: Basic Filtering section

        kml = KMLFile.from_string(self.api_test_kml)

        # Filter by name
        store_a = kml.placemarks.filter(name="Test Store A")
        assert len(store_a) == 1
        assert store_a[0].name == "Test Store A"

        # Filter with contains
        stores = kml.placemarks.filter(name__icontains="store")
        assert len(stores) == 2

        # Filter with startswith
        test_stores = kml.placemarks.filter(name__startswith="Test")
        assert len(test_stores) == 2

    def test_querysets_geospatial_examples(self) -> None:
        """Test geospatial query examples from querysets.rst."""
        # From api/querysets.rst: Geospatial Queries section

        kml = KMLFile.from_string(self.api_test_kml)

        # Near query
        nearby = kml.placemarks.near(-76.5, 39.3, radius_km=50)
        assert len(nearby) >= 1

        # Within bounds
        in_area = kml.placemarks.within_bounds(north=40.0, south=39.0, east=-76.0, west=-77.0)
        assert len(in_area) >= 1

        # Has coordinates
        with_coords = kml.placemarks.has_coordinates()
        assert len(with_coords) == 2

    def test_querysets_chaining_examples(self) -> None:
        """Test query chaining examples from querysets.rst."""
        # From api/querysets.rst: Query Chaining section
        kml = KMLFile.from_string(self.api_test_kml)

        # Complex chained query
        result = (
            kml.placemarks.filter(name__icontains="test")
            .has_coordinates()
            .near(-76.5, 39.3, radius_km=100)
            .order_by("name")
        )

        assert len(result) >= 1

        # Verify ordering
        if len(result) > 1:
            names = [p.name or "" for p in result]
            assert names == sorted(names)

    def test_querysets_aggregation_examples(self) -> None:
        """Test aggregation examples from querysets.rst."""
        # From api/querysets.rst: Aggregation section
        kml = KMLFile.from_string(self.api_test_kml)

        # Count
        count = kml.placemarks.count()
        assert count == 2

        # Exists
        exists = kml.placemarks.filter(name__icontains="test").exists()
        assert exists is True

        # First and last
        first = kml.placemarks.first()
        last = kml.placemarks.last()
        assert first is not None
        assert last is not None
