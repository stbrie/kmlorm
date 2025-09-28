"""
Shared pytest fixtures for KML ORM tests.

This module provides common test fixtures that can be used across
multiple test files to reduce duplication and ensure consistency.
"""

# pylint: disable=redefined-outer-name, duplicate-code
# This is intentional - pytest fixtures use parameter names to specify dependencies

import tempfile
from pathlib import Path
from typing import Generator, Any, Tuple, cast, List
import pytest


from kmlorm import KMLFile
from kmlorm.models import Placemark


@pytest.fixture
def sample_kml_content() -> str:
    """Provide comprehensive sample KML content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Test Document</name>
        <description>A comprehensive test document for KML ORM</description>

        <Folder>
            <name>Store Locations</name>
            <description>All store locations</description>
            <visibility>1</visibility>

            <Placemark>
                <name>Capital Electric - Rosedale</name>
                <description>Main store location</description>
                <address>123 Main St, Rosedale, MD</address>
                <Point>
                    <coordinates>-76.5,39.3,0</coordinates>
                </Point>
            </Placemark>

            <Placemark>
                <name>Capital Electric - Downtown</name>
                <description>Downtown branch</description>
                <address>456 Oak Ave, Baltimore, MD</address>
                <Point>
                    <coordinates>-76.6,39.4,0</coordinates>
                </Point>
            </Placemark>

            <Folder>
                <name>Nested Folder</name>
                <description>Nested store locations</description>
                <visibility>1</visibility>

                <Placemark>
                    <name>Capital Electric - Nested</name>
                    <description>Nested store</description>
                    <Point>
                        <coordinates>-76.4,39.2,0</coordinates>
                    </Point>
                </Placemark>
            </Folder>
        </Folder>

        <Placemark>
            <name>Capital Electric - Root Level</name>
            <description>Root level store</description>
            <address>789 Pine St, Baltimore, MD</address>
            <Point>
                <coordinates>-76.7,39.1,0</coordinates>
            </Point>
        </Placemark>
    </Document>
</kml>"""


@pytest.fixture
def simple_kml_content() -> str:
    """Provide simple KML content for basic testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <Placemark>
            <name>Test Store</name>
            <Point>
                <coordinates>-76.5,39.3,0</coordinates>
            </Point>
        </Placemark>
    </Document>
</kml>"""


@pytest.fixture
def kml_with_coordinates() -> str:
    """Provide KML content with known coordinates for spatial testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <Placemark>
            <name>Store A</name>
            <Point>
                <coordinates>-74.006,40.7128,0</coordinates>
            </Point>
        </Placemark>
        <Placemark>
            <name>Store B</name>
            <Point>
                <coordinates>-0.1276,51.5074,0</coordinates>
            </Point>
        </Placemark>
    </Document>
</kml>"""


@pytest.fixture
def sample_kml_file(sample_kml_content: str) -> KMLFile:
    """Create KMLFile instance from sample content."""
    return KMLFile.from_string(sample_kml_content)


@pytest.fixture
def simple_kml_file(simple_kml_content: str) -> KMLFile:
    """Create KMLFile instance from simple content."""
    return KMLFile.from_string(simple_kml_content)


@pytest.fixture
def kml_file_with_coordinates(kml_with_coordinates: str) -> KMLFile:
    """Create KMLFile instance with known coordinates for spatial testing."""
    return KMLFile.from_string(kml_with_coordinates)


@pytest.fixture
def temp_kml_file(sample_kml_content: str) -> Generator[Path, None, None]:
    """Create temporary KML file that is automatically cleaned up."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False, encoding="utf-8") as f:
        f.write(sample_kml_content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create temporary directory that is automatically cleaned up."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def baltimore_coordinates() -> tuple:
    """Standard Baltimore coordinates for testing."""
    return (-76.6, 39.3)


@pytest.fixture
def nyc_coordinates() -> tuple:
    """Standard NYC coordinates for testing."""
    return (-74.006, 40.7128)


@pytest.fixture
def london_coordinates() -> tuple:
    """Standard London coordinates for testing."""
    return (-0.1276, 51.5074)


# Coordinate test data for parametrized tests
KNOWN_DISTANCES = [
    # (coord1, coord2, expected_km, tolerance_km)
    ((-74.006, 40.7128), (-0.1276, 51.5074), 5567, 10),  # NYC to London
    ((139.6917, 35.6895), (-122.4194, 37.7749), 8280, 10),  # Tokyo to San Francisco
    ((0, 0), (0, 0), 0, 0),  # Same point
    ((0, 0), (1, 0), 111.32, 1),  # 1 degree longitude at equator
    ((0, 0), (0, 1), 111.32, 1),  # 1 degree latitude
]


@pytest.fixture(params=KNOWN_DISTANCES)
def known_distance_data(
    request: Any,
) -> Tuple[Tuple[float, float], Tuple[float, float], float, float]:
    """Parametrized fixture for known distance test data."""
    return cast(Tuple[Tuple[float, float], Tuple[float, float], float, float], request.param)


# ===== Commonly Used Test Data Fixtures =====


@pytest.fixture
def nested_kml_content() -> str:
    """KML content with deeply nested folder structure for testing hierarchy."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Test Document</name>
        <Placemark>
            <name>Root Placemark 1</name>
            <Point>
                <coordinates>-122.0856545755255,37.42243077405461,0</coordinates>
            </Point>
        </Placemark>
        <Placemark>
            <name>Root Placemark 2</name>
            <Point>
                <coordinates>-122.084075,37.4220033612141,0</coordinates>
            </Point>
        </Placemark>
        <Folder>
            <name>Level 1 Folder</name>
            <Placemark>
                <name>Nested Placemark 1</name>
                <Point>
                    <coordinates>-122.085075,37.4230033612141,0</coordinates>
                </Point>
            </Placemark>
            <Folder>
                <name>Level 2 Folder</name>
                <Placemark>
                    <name>Deep Nested Placemark</name>
                    <Point>
                        <coordinates>-122.086075,37.4240033612141,0</coordinates>
                    </Point>
                </Placemark>
            </Folder>
        </Folder>
        <Folder>
            <name>Another Root Folder</name>
            <Placemark>
                <name>Another Nested Placemark</name>
                <Point>
                    <coordinates>-122.087075,37.4250033612141,0</coordinates>
                </Point>
            </Placemark>
        </Folder>
    </Document>
</kml>"""


@pytest.fixture
def sample_placemarks() -> List[Placemark]:
    """List of sample Placemark objects for testing."""
    return [
        Placemark(name="Capital Electric - Rosedale", coordinates=(-76.5, 39.3)),
        Placemark(name="Capital Electric - Timonium", coordinates=(-76.6, 39.4)),
        Placemark(name="Other Store", coordinates=(-76.7, 39.5)),
    ]


@pytest.fixture
def stores_kml_content() -> str:
    """KML content with store locations for business logic testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Store Locations</name>
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
    </Document>
</kml>"""


@pytest.fixture
def empty_kml_content() -> str:
    """Empty but valid KML document for edge case testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Empty Document</name>
    </Document>
</kml>"""


@pytest.fixture
def invalid_kml_content() -> str:
    """Invalid KML content for error testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <Placemark>
            <name>Invalid Placemark</name>
            <!-- Missing closing tags -->
</kml>"""
