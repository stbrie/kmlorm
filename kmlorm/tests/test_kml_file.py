"""
Tests for KMLFile loading and parsing functionality.

This module tests the KMLFile class and its ability to load
KML data from various sources.
"""

# pylint: disable=duplicate-code
from typing import Any
from unittest.mock import mock_open, patch

import pytest

from ..core.exceptions import KMLParseError
from ..parsers.kml_file import KMLFile


class TestKMLFile:
    """Test KMLFile loading and parsing."""

    test_kml: str

    @pytest.fixture(autouse=True)
    def setup_kml_data(self, simple_kml_content: str) -> None:
        """Set up test data using fixture from conftest."""
        self.test_kml = simple_kml_content

    def test_from_string_basic(self) -> None:
        """Test loading KML from string."""
        # This test checks the string parsing setup.
        kml_file = KMLFile.from_string(self.test_kml)
        assert isinstance(kml_file, KMLFile)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_from_file_mock(self, mock_exists: Any, mock_file: Any) -> None:
        """Test loading KML from file using mocks."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.test_kml

        kml_file = KMLFile.from_file("test.kml")
        assert isinstance(kml_file, KMLFile)

    def test_from_file_not_found(self) -> None:
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            KMLFile.from_file("nonexistent.kml")

    @patch("kmlorm.parsers.xml_parser.urlopen")
    def test_from_url_mock(self, mock_urlopen: Any) -> None:
        """Test loading KML from URL using mocks."""
        # Mock the URL response
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = self.test_kml.encode("utf-8")

        kml_file = KMLFile.from_url("http://example.com/test.kml")
        assert isinstance(kml_file, KMLFile)

    def test_from_url_invalid_url(self) -> None:
        """Test loading from invalid URL."""
        with pytest.raises(KMLParseError):
            KMLFile.from_url("not-a-url")

    def test_element_counts_empty(self) -> None:
        """Test element counts on empty KML file."""
        kml_file = KMLFile()
        counts = kml_file.element_counts()

        expected = {
            "placemarks": 0,
            "folders": 0,
            "paths": 0,
            "polygons": 0,
            "points": 0,
            "multigeometries": 0,
        }
        assert counts == expected

    def test_all_elements_empty(self) -> None:
        """Test getting all elements from empty KML file."""
        kml_file = KMLFile()
        elements = kml_file.all_elements()
        assert len(elements) == 0

    def test_managers_setup(self) -> None:
        """Test that managers are properly set up."""
        kml_file = KMLFile()

        # Check that managers exist
        assert hasattr(kml_file, "placemarks")
        assert hasattr(kml_file, "folders")
        assert hasattr(kml_file, "paths")
        assert hasattr(kml_file, "polygons")

        # Check that they have the expected interface
        assert hasattr(kml_file.placemarks, "all")
        assert hasattr(kml_file.placemarks, "filter")
        assert hasattr(kml_file.placemarks, "count")

    def test_kmz_detection(self) -> None:
        """Test KMZ content detection."""
        # ZIP file signature
        zip_content = b"PK\x03\x04"
        assert KMLFile._is_zip_content(zip_content)  # pylint: disable=protected-access

        # Non-ZIP content
        kml_content = b'<?xml version="1.0"'
        assert not KMLFile._is_zip_content(kml_content)  # pylint: disable=protected-access


if __name__ == "__main__":
    pytest.main([__file__])
