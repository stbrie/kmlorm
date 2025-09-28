"""
Integration tests for KMLFile.from_url() with real HTTP server.

This module tests the URL loading functionality using an actual local HTTP server
serving real KML fixture files, proving that the functionality works end-to-end
without mocking.
"""

import http.server
import os
import socketserver
import threading
import time
from typing import Any

import pytest

from ..core.exceptions import KMLParseError
from ..parsers.kml_file import KMLFile


class TestKMLFileURLIntegration:
    """
    Integration tests for loading KML files from URLs using a local HTTP server.

    This test class sets up a temporary HTTP server to serve KML fixture files and verifies
    that the `KMLFile.from_url` method can correctly load and parse KML files over HTTP.
    It covers scenarios including:

    - Loading sample KML files and verifying their contents.
    - Handling of nested folders and placemarks.
    - Verifying placemark metadata such as name, address, and coordinates.
    - Error handling for 404 responses and invalid server URLs.
    - Loading comprehensive KML files with complex structures.
    - Ensuring the usage pattern shown in documentation works as expected.

    The HTTP server is started and stopped automatically for each test, serving files from
    the `fixtures` directory. Tests assert correct parsing, error handling, and query operations.
    """

    fixtures_dir: str
    port: int
    server_thread: threading.Thread
    httpd: socketserver.TCPServer
    base_url: str

    @pytest.fixture(autouse=True)
    def setup_http_server(self) -> Any:
        """
        Sets up a temporary HTTP server to serve files from the test fixtures
        directory for integration testing.

        This method:
        - Locates the 'fixtures' directory relative to the test file.
        - Finds an available port between 8765 and 8799.
        - Starts a SimpleHTTPRequestHandler-based HTTP server in a background thread, serving
            files from the fixtures directory.
        - Sets the `base_url` attribute for use in test requests.
        - Yields control to allow test execution.
        - Shuts down and cleans up the server after tests complete.

        Yields:
            None

        Attributes set:
            fixtures_dir (str): Path to the fixtures directory.
            port (int): Port number the server is running on.
            httpd (socketserver.TCPServer): The HTTP server instance.
            server_thread (threading.Thread): The thread running the server.
            base_url (str): Base URL for accessing the server.
        """

        # Get the fixtures directory
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")

        # Find an available port
        self.port = 8765
        for port in range(8765, 8800):
            try:
                # Test if port is available
                test_server = socketserver.TCPServer(
                    ("localhost", port), http.server.SimpleHTTPRequestHandler
                )
                test_server.server_close()
                self.port = port
                break
            except OSError:
                continue

        # Create HTTP server
        os.chdir(self.fixtures_dir)  # Serve from fixtures directory

        handler = http.server.SimpleHTTPRequestHandler
        self.httpd = socketserver.TCPServer(("localhost", self.port), handler)

        # Start server in background thread
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Give server time to start
        time.sleep(0.1)

        # Base URL for test requests
        self.base_url = f"http://localhost:{self.port}"

        yield

        # Cleanup
        self.httpd.shutdown()
        self.httpd.server_close()
        self.server_thread.join(timeout=1.0)

    def test_from_url_real_http_request_sample_kml(self) -> None:
        """Test loading sample.kml via real HTTP request to local server."""
        url = f"{self.base_url}/sample.kml"

        kml = KMLFile.from_url(url)

        # Verify we got a KMLFile instance
        assert isinstance(kml, KMLFile)

        # Verify document metadata from sample.kml
        assert kml.document_name == "Capital Electric Supply Locations"
        assert kml.document_description == "Sample KML file with store locations for testing"

        # Verify we have folders
        folders = kml.folders.children()  # Direct child folders
        assert len(folders) > 0
        maryland_folder = next((f for f in folders if f.name == "Maryland Stores"), None)
        assert maryland_folder is not None

        # Verify we have placemarks (use flatten=True to get from nested folders)
        placemarks = kml.placemarks.all(flatten=True)
        assert len(placemarks) > 0

        # Find the Rosedale store
        rosedale = next((p for p in placemarks if p.name and "Rosedale" in p.name), None)
        assert rosedale is not None
        assert rosedale.name == "Capital Electric Supply - Rosedale"
        assert rosedale.address == "1234 Baltimore Avenue, Rosedale, MD 21237"

        # Verify coordinates
        assert rosedale.coordinates is not None
        assert rosedale.longitude == -76.5105
        assert rosedale.latitude == 39.3220

    def test_from_url_real_http_request_tutorial_stores(self) -> None:
        """Test loading tutorial_stores.kml via real HTTP request."""
        url = f"{self.base_url}/tutorial_stores.kml"

        kml = KMLFile.from_url(url)

        # Verify we got a KMLFile instance
        assert isinstance(kml, KMLFile)

        # Verify we can access elements
        placemarks = kml.placemarks.children()  # Direct child placemarks
        assert len(placemarks) > 0

        # Verify at least one placemark has coordinates
        placemark_with_coords = next((p for p in placemarks if p.coordinates), None)
        assert placemark_with_coords is not None
        assert placemark_with_coords.longitude is not None
        assert placemark_with_coords.latitude is not None

    def test_from_url_404_error_handling(self) -> None:
        """Test error handling when URL returns 404."""
        url = f"{self.base_url}/nonexistent.kml"

        # Should raise KMLParseError for 404 responses
        with pytest.raises(KMLParseError):
            KMLFile.from_url(url)

    def test_from_url_invalid_server_url(self) -> None:
        """Test error handling for completely invalid server URL."""
        # Use a port that definitely won't have a server
        invalid_url = "http://localhost:9999/test.kml"

        with pytest.raises(KMLParseError):
            KMLFile.from_url(invalid_url)

    def test_from_url_comprehensive_kml(self) -> None:
        """Test loading comprehensive.kml with complex structure via HTTP."""
        url = f"{self.base_url}/comprehensive.kml"

        kml = KMLFile.from_url(url)

        # Verify we got a KMLFile instance
        assert isinstance(kml, KMLFile)

        # Verify we can get element counts
        counts = kml.element_counts()
        assert isinstance(counts, dict)
        assert "placemarks" in counts

        # Verify we have various element types
        all_elements = kml.all_elements()
        assert len(all_elements) > 0

    def test_quickstart_example_pattern(self) -> None:
        """Test the exact pattern shown in quickstart.rst documentation."""
        # This mimics: kml = KMLFile.from_url('https://example.com/data.kml')
        # but with our local server serving real data
        url = f"{self.base_url}/sample.kml"

        kml = KMLFile.from_url(url)

        # Verify the quickstart pattern works
        assert isinstance(kml, KMLFile)

        # Verify we can do the operations shown in quickstart
        placemarks = kml.placemarks.all(flatten=True)
        assert len(placemarks) > 0

        # Test basic query operations from quickstart
        stores_with_electric = kml.placemarks.all(flatten=True).filter(name__icontains="electric")
        assert len(stores_with_electric) > 0

        # Test coordinate access pattern from quickstart
        for placemark in placemarks:
            if placemark.coordinates:
                assert placemark.longitude is not None
                assert placemark.latitude is not None
                break
        else:
            pytest.fail("No placemarks with coordinates found")


if __name__ == "__main__":
    pytest.main([__file__])
