"""
Basic tests for KML ORM functionality.

This module contains fundamental tests to verify that the core
functionality works as expected.
"""

from typing import List
import pytest
from ..core.exceptions import KMLElementNotFound, KMLMultipleElementsReturned
from ..core.managers import KMLManager
from ..models.folder import Folder
from ..models.placemark import Placemark


class TestPlacemark:
    """Test basic Placemark functionality."""

    def test_placemark_creation(self) -> None:
        """Test creating a placemark with coordinates."""
        placemark = Placemark(
            name="Test Store",
            coordinates=(-76.5, 39.3, 0),
            address="123 Main St, Baltimore, MD",
        )

        assert placemark.name == "Test Store"
        assert placemark.longitude == -76.5
        assert placemark.latitude == 39.3
        assert placemark.altitude == 0
        assert placemark.has_coordinates

    def test_placemark_coordinates_from_string(self) -> None:
        """Test parsing coordinates from string format."""
        placemark = Placemark(name="String Coords", coordinates="-76.5,39.3,100")

        assert placemark.longitude == -76.5
        assert placemark.latitude == 39.3
        assert placemark.altitude == 100

    def test_placemark_distance_calculation(self) -> None:
        """Test distance calculation between placemarks."""
        placemark1 = Placemark(coordinates=(-76.5, 39.3))
        placemark2 = Placemark(coordinates=(-76.6, 39.4))

        distance = placemark1.distance_to(placemark2)
        assert distance is not None
        assert distance > 0
        assert distance < 50  # Should be less than 50km

    def test_placemark_bearing_calculation(self) -> None:
        """Test bearing calculation between placemarks."""
        placemark1 = Placemark(coordinates=(-76.5, 39.3))
        placemark2 = Placemark(coordinates=(-76.4, 39.4))  # Northeast

        bearing = placemark1.bearing_to(placemark2)
        assert bearing is not None
        assert bearing > 0
        assert bearing < 360

    def test_placemark_validation(self) -> None:
        """Test placemark validation."""
        # Valid placemark
        placemark = Placemark(coordinates=(-76.5, 39.3))
        assert placemark.validate()

        # Invalid longitude
        with pytest.raises(Exception):
            invalid_placemark = Placemark(coordinates=(200, 39.3))
            invalid_placemark.validate()

        # Invalid latitude
        with pytest.raises(Exception):
            invalid_placemark = Placemark(coordinates=(-76.5, 100))
            invalid_placemark.validate()


class TestFolder:
    """Test basic Folder functionality."""

    def test_folder_creation(self) -> None:
        """Test creating a folder."""
        folder = Folder(name="Test Folder", description="A test folder")

        assert folder.name == "Test Folder"
        assert folder.description == "A test folder"
        assert folder.total_element_count() == 0

    def test_folder_placemark_management(self) -> None:
        """Test adding placemarks to a folder."""
        folder = Folder(name="Store Folder")
        placemark = Placemark(name="Test Store", coordinates=(-76.5, 39.3))

        # Add placemark to folder
        folder.placemarks.add(placemark)

        assert folder.placemarks.count() == 1
        assert folder.total_element_count() == 1
        assert placemark.parent == folder

        # Remove placemark
        folder.placemarks.remove(placemark)
        assert folder.placemarks.count() == 0


class TestQuerySet:
    """Test QuerySet functionality."""

    placemarks: List[Placemark]
    manager: KMLManager

    @pytest.fixture(autouse=True)
    def setup_test_data(self, sample_placemarks: List[Placemark]) -> None:
        """Set up test data using fixture from conftest."""
        self.placemarks = sample_placemarks

        # Create a manager and add placemarks
        self.manager = KMLManager()
        for placemark in self.placemarks:
            self.manager.add(placemark)

    def test_filter_by_name(self) -> None:
        """Test filtering by name."""
        capital_stores = self.manager.filter(name__icontains="capital")
        assert capital_stores.count() == 2

        for store in capital_stores:
            assert store.name is not None  # Type assertion for mypy
            assert "Capital" in store.name

    def test_exclude_filter(self) -> None:
        """Test exclude filter."""
        non_capital = self.manager.exclude(name__icontains="capital")
        assert non_capital.count() == 1
        first_element = non_capital.first()
        assert first_element is not None  # Type assertion for mypy
        assert first_element.name == "Other Store"

    def test_get_single_element(self) -> None:
        """Test getting a single element."""
        store = self.manager.get(name="Other Store")
        assert store.name == "Other Store"

        # Test get with no results
        with pytest.raises(KMLElementNotFound):
            self.manager.get(name="Nonexistent Store")

        # Test get with multiple results
        with pytest.raises(KMLMultipleElementsReturned):
            self.manager.get(name__icontains="Capital")

    def test_order_by(self) -> None:
        """Test ordering elements."""
        ordered = self.manager.order_by("name")
        names = [p.name for p in ordered]

        assert names[0] == "Capital Electric - Rosedale"
        assert names[1] == "Capital Electric - Timonium"
        assert names[2] == "Other Store"

        # Test reverse order
        reverse_ordered = self.manager.order_by("-name")
        reverse_names = [p.name for p in reverse_ordered]
        assert reverse_names == list(reversed(names))

    def test_geospatial_queries(self) -> None:
        """Test geospatial query methods."""
        # Test near query
        near_baltimore = self.manager.near(-76.6, 39.3, radius_km=50)
        assert near_baltimore.count() == 3  # All should be within 50km

        # Test tight radius
        near_tight = self.manager.near(-76.5, 39.3, radius_km=5)
        assert near_tight.count() == 1  # Only Rosedale

        # Test within bounds
        bounded = self.manager.within_bounds(north=39.5, south=39.25, east=-76.4, west=-76.8)
        assert bounded.count() == 3  # All within bounds

    def test_chaining_queries(self) -> None:
        """Test chaining multiple query operations."""
        result = (
            self.manager.filter(name__icontains="capital")
            .near(-76.6, 39.3, radius_km=30)
            .order_by("name")
        )

        assert result.count() == 2
        names = [p.name for p in result]
        assert names[0] == "Capital Electric - Rosedale"
        assert names[1] == "Capital Electric - Timonium"


if __name__ == "__main__":
    pytest.main([__file__])
