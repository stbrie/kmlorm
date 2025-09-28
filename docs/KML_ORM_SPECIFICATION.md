# KML ORM Specification

## Project Overview

A Django-style ORM for KML (Keyhole Markup Language) files that provides intuitive data access and filtering without requiring Django as a dependency.

**Primary Goal**: Extract data from KML files and make it accessible using Django idioms like `folder.placemarks.filter(id__ilike="1.")`.

**Focus**: Robust parsing and user-friendly data access. Geospatial calculations and manipulations are left to specialized libraries.

## Core Architecture

### Base Classes

```python
from kmlorm import KMLFile, Placemark, Folder, Path, Polygon

# File loading
kml = KMLFile.from_file('places.kml')
kml = KMLFile.from_string(kml_text)
kml = KMLFile.from_url('https://example.com/data.kml')
```

### Model-Style Classes

```python
class KMLElement:
    """Base class for all KML elements"""
    objects = KMLManager()

    # Common attributes
    id: str
    name: str
    description: str
    visibility: bool

class Placemark(KMLElement):
    """Point locations with coordinates"""
    coordinates: Coordinate  # Coordinate object with longitude, latitude, altitude
    address: str
    phone_number: str
    snippet: str
    style_url: str
    extended_data: dict

class Folder(KMLElement):
    """Container for organizing KML elements"""
    placemarks: RelatedManager
    folders: RelatedManager  # Nested folders
    paths: RelatedManager
    polygons: RelatedManager
    multigeometries: RelatedManager

class Point(KMLElement):
    """Geographic point with coordinates"""
    coordinates: Coordinate  # Coordinate object (longitude, latitude, altitude)
    extrude: bool
    altitude_mode: str

class Path(KMLElement):
    """LineString paths/routes"""
    coordinates: list  # [(lon, lat, alt), ...]
    tessellate: bool
    altitude_mode: str

class Polygon(KMLElement):
    """Polygon areas"""
    outer_boundary: list  # [(lon, lat, alt), ...]
    inner_boundaries: list  # [[(lon, lat, alt), ...], ...]
    extrude: bool
    altitude_mode: str

class MultiGeometry(KMLElement):
    """Collection of multiple geometry types"""
    points: list[Point]
    paths: list[Path]
    polygons: list[Polygon]
    # Supports mixed geometry collections

class Coordinate:
    """Individual coordinate with longitude, latitude, altitude"""
    longitude: float
    latitude: float
    altitude: float = 0.0

    @classmethod
    def from_string(cls, coord_str: str) -> 'Coordinate'
    @classmethod
    def from_any(cls, value: Any) -> 'Coordinate'
    def to_dict(self) -> dict

class KMLFile:
    """Main entry point for KML document parsing and access"""
    name: str
    description: str
    placemarks: KMLManager
    folders: KMLManager

    @classmethod
    def from_file(cls, path: str) -> 'KMLFile'
    @classmethod
    def from_string(cls, kml_data: str) -> 'KMLFile'
    @classmethod
    def from_url(cls, url: str) -> 'KMLFile'
```

## QuerySet Methods

### Django-Compatible Core Methods

```python
# Basic retrieval
.all()                              # Return all objects
.get(**kwargs)                      # Get single object, raise if not found
.filter(**kwargs)                   # Filter objects by criteria
.exclude(**kwargs)                  # Exclude objects by criteria
.first()                           # Get first object or None
.last()                            # Get last object or None
.count()                           # Count objects in queryset
.exists()                          # Check if any objects exist
.none()                            # Return empty queryset

# Ordering
.order_by(*fields)                 # Order by field(s)
.reverse()                         # Reverse current ordering

# Slicing and limiting
.distinct()                        # Remove duplicates
[:n]                               # Slice notation support

# Aggregation
.values(*fields)                   # Return dicts with specified fields
.values_list(*fields, flat=False)  # Return tuples
.only(*fields)                     # Defer loading of other fields
.defer(*fields)                    # Defer loading of specified fields
```

### Data Access Methods

```python
# Coordinate-based filtering
.has_coordinates()                                   # Non-null coordinates
.filter(coordinates__isnull=False)                  # Standard Django pattern

# Geospatial operations (built-in)
.near(longitude, latitude, radius_km=50)            # Within radius
.within_bounds(north, south, east, west)            # Within bounding box

# Note: Advanced geospatial operations (intersection, buffering, etc.)
# should be handled by dedicated libraries like Shapely, GeoPandas, or PostGIS
```

## Query Examples

### Basic Filtering

```python
# Load KML file
kml = KMLFile.from_file('capital_electric.kml')

# Get all placemarks
all_places = kml.placemarks.all()

# Filter by name
capital_stores = kml.placemarks.filter(name__icontains='capital')

# Get specific placemark
rosedale = kml.placemarks.get(address__contains='Rosedale')

# Filter by multiple criteria
md_stores = kml.placemarks.filter(
    name__icontains='capital',
    address__contains='MD'
)

# Exclude certain items
non_capital = kml.placemarks.exclude(name__icontains='capital')

# Chain filters
nearby_open = (kml.placemarks
    .filter(name__icontains='electric')
    .near(-76.6, 39.3, radius_km=50)
    .filter(visibility=True)
)
```

### Coordinate-Based Filtering

```python
# Basic coordinate checks
has_coords = kml.placemarks.has_coordinates()

# Filter by coordinate existence
with_location = kml.placemarks.filter(coordinates__isnull=False)

# Raw coordinate access (for use with external geospatial libraries)
for placemark in kml.placemarks.all():
    if placemark.coordinates:
        coord = placemark.coordinates  # Coordinate object
        lon, lat = coord.longitude, coord.latitude
        # Or direct access: placemark.longitude, placemark.latitude
        # Use with Shapely, GeoPandas, etc. for calculations

# Complex geospatial operations should use dedicated libraries:
# - Shapely for geometric operations
# - GeoPandas for spatial analysis
# - PostGIS for database spatial queries
```

### Aggregation and Counting

```python
# Count placemarks
total_places = kml.placemarks.count()
capital_count = kml.placemarks.filter(name__icontains='capital').count()

# Check existence
has_capital = kml.placemarks.filter(name__icontains='capital').exists()

# Get coordinate bounds
bounds = kml.placemarks.aggregate(
    min_lat=Min('coordinates__1'),
    max_lat=Max('coordinates__1'),
    min_lon=Min('coordinates__0'),
    max_lon=Max('coordinates__0')
)
```

### Folder Relationships

```python
# Navigate folder hierarchy
supply_folder = kml.folders.get(name='capital electric supply')
folder_places = supply_folder.placemarks.all()

# Nested folder access
all_subfolders = supply_folder.folders.all()

# Cross-folder queries
all_capital_places = kml.placemarks.filter(name__icontains='capital')
```

## Field Lookups

### String Lookups

```python
.filter(name='Capital Electric')                    # Exact match
.filter(name__icontains='capital')                  # Case-insensitive contains
.filter(name__contains='Electric')                  # Case-sensitive contains
.filter(name__startswith='Capital')                 # Starts with
.filter(name__endswith='Electric')                  # Ends with
.filter(name__regex=r'^Capital.*Electric$')         # Regex match
.filter(address__in=['Rosedale, MD', 'Timonium, MD']) # In list
```

### Coordinate Lookups

```python
.filter(coordinates__longitude__gte=-77.0)          # Longitude >= -77.0
.filter(coordinates__latitude__range=(39.0, 40.0))  # Latitude between 39-40
.filter(coordinates__altitude__isnull=True)         # No altitude data
.filter(coordinates__distance_lt=('POINT(-76.6 39.3)', 1000)) # Within 1km
```

### Extended Data Lookups

```python
.filter(extended_data__has_key='placepageUri')      # Has extended data key
.filter(extended_data__phone__icontains='410')      # Extended data field
.filter(phone_number__startswith='(410)')           # Direct phone field
```

## Relationships and Related Managers

```python
class RelatedManager:
    """Manager for related objects (e.g., folder.placemarks)"""

    def add(self, *objects):                        # Add objects to relationship
    def remove(self, *objects):                     # Remove from relationship
    def clear():                                    # Remove all related objects
    def create(**kwargs):                           # Create and add new object
    def get_or_create(**kwargs):                    # Get existing or create new

    # All QuerySet methods available
    def all(self): ...
    def filter(self, **kwargs): ...
    def count(self): ...
```

### Usage Examples

```python
# Folder relationships
folder = kml.folders.get(name='stores')
folder.placemarks.count()                           # Count placemarks in folder
folder.placemarks.filter(name__contains='Electric') # Filter within folder
folder.placemarks.create(name='New Store', coordinates=(-76.0, 39.0))

# Reverse relationships
placemark = kml.placemarks.first()
placemark.folder                                    # Parent folder (if any)
```

## Data Integration

### Raw Data Access

```python
# Access raw coordinate data for use with external libraries
for placemark in kml.placemarks.all():
    data = {
        'name': placemark.name,
        'coordinates': placemark.coordinates,  # Raw tuple (lon, lat, alt)
        'extended_data': placemark.extended_data,  # Raw dict
    }

# Convert to standard Python data structures
placemarks_data = kml.placemarks.values(
    'name', 'coordinates', 'address', 'extended_data'
)

# Integration with external libraries is user's responsibility:
# - Use pandas for DataFrame conversion
# - Use Shapely for geometry operations
# - Use GeoPandas for spatial analysis
# - Use PostGIS connectors for spatial database operations
```

## Advanced Features

### Caching and Performance

```python
# QuerySet caching
kml.placemarks.cache()                              # Cache queryset results
kml.placemarks.prefetch_related('folder')           # Eager load relationships

# Spatial indexing
kml.build_spatial_index()                           # Build spatial index for performance
kml.placemarks.using_spatial_index()                # Use spatial index for queries
```

### Custom Field Types

```python
class CoordinateField:
    """Custom field type for coordinates with spatial methods"""
    def distance_to(self, other_coords): ...
    def bearing_to(self, other_coords): ...
    def midpoint_to(self, other_coords): ...

class BoundingBoxField:
    """Field type for bounding boxes"""
    def contains(self, coordinates): ...
    def intersects(self, other_bbox): ...
    def union(self, other_bbox): ...
```

### Validation and Constraints

```python
# Built-in validation
.validate_coordinates()                             # Check coordinate validity
.validate_geometry()                               # Check geometry validity
.validate_kml_structure()                          # Check KML compliance

# Custom validators
def custom_validator(kml_element):
    """Custom validation function"""
    pass

kml.add_validator(custom_validator)
```

## Error Handling

```python
class KMLOrmException(Exception):
    """Base exception for KML ORM operations"""

class KMLParseError(KMLOrmException):
    """Raised when KML cannot be parsed"""

class KMLElementNotFound(KMLOrmException):
    """Raised when get() finds no matching elements"""

class KMLMultipleElementsReturned(KMLOrmException):
    """Raised when get() finds multiple elements"""

class KMLInvalidCoordinates(KMLOrmException):
    """Raised when coordinates are invalid"""
```

## Configuration and Settings

```python
class KMLOrmSettings:
    """Global settings for KML ORM behavior"""

    # Coordinate validation
    STRICT_COORDINATE_VALIDATION = True
    COORDINATE_PRECISION = 6                        # Decimal places

    # Performance
    DEFAULT_SPATIAL_INDEX = True
    CACHE_QUERYSETS = True
    MAX_CACHE_SIZE = 1000

    # Parsing
    IGNORE_INVALID_ELEMENTS = False
    DEFAULT_ENCODING = 'utf-8'
    NAMESPACE_HANDLING = 'strict'  # 'strict', 'lenient', 'ignore'

    # Spatial/Coordinate system
    DEFAULT_SRID = 4326
```

## Package Structure

```
kmlorm/
├── __init__.py              # Main package exports
├── _version.py              # Version management (auto-generated)
├── core/
│   ├── __init__.py
│   ├── managers.py          # KMLManager, RelatedManager implementations
│   ├── querysets.py         # KMLQuerySet with filtering and geospatial methods
│   └── exceptions.py        # All custom exception classes
├── models/
│   ├── __init__.py
│   ├── base.py              # KMLElement base class
│   ├── placemark.py         # Placemark model with coordinates
│   ├── folder.py            # Folder model for hierarchical organization
│   ├── path.py              # Path/LineString geometry model
│   ├── polygon.py           # Polygon geometry model
│   ├── point.py             # Point model and Coordinate class
│   └── multigeometry.py     # MultiGeometry collection model
├── parsers/
│   ├── __init__.py
│   ├── xml_parser.py        # XML/KML parsing with lxml
│   └── kml_file.py          # KMLFile main entry point
├── spatial/
│   └── __init__.py          # Reserved for spatial operations
├── exports/
│   └── __init__.py          # Reserved for future functionality
├── utils/
│   └── __init__.py          # Reserved for utility functions
└── tests/
    ├── __init__.py
    ├── test_basic.py         # Core model functionality tests
    ├── test_placemark.py     # Placemark-specific tests
    ├── test_folder.py        # Folder model tests
    ├── test_multigeometry.py # MultiGeometry tests
    ├── test_path.py          # Path model tests
    ├── test_polygon.py       # Polygon model tests
    ├── test_point_extra.py   # Point and Coordinate tests
    ├── test_base.py          # Base model tests
    ├── test_kml_file.py      # KMLFile parser tests
    ├── test_xml_parser.py    # XML parser tests
    ├── test_queryset.py      # QuerySet functionality tests
    ├── test_querysets_extra.py # Advanced QuerySet tests
    ├── test_managers_extra.py  # Manager functionality tests
    ├── test_url_integration.py # HTTP/URL loading tests
    ├── test_*_docs.py        # Documentation example tests
    ├── test_*_examples.py    # Usage pattern tests
    └── fixtures/
        ├── sample.kml        # Basic test KML
        ├── comprehensive.kml # Full-featured test KML
        ├── tutorial_stores.kml # Tutorial examples
        ├── multigeometry_test.kml # MultiGeometry samples
        └── google_earth_kml.kml # Real-world KML samples
```

## Dependencies

### Required
- `lxml` - XML parsing and KML document processing

### Optional
- None currently (reserved for future features that may require optional dependencies)
- Note: Users can integrate with `pandas`, `shapely`, `geopandas`, etc. using the `to_dict()` methods

## Compatibility

- **Python**: 3.11+ (as specified in pyproject.toml)
- **KML**: Google Earth KML, OGC KML 2.2 standard
- **Coordinate Systems**: WGS84 (EPSG:4326) - longitude, latitude, altitude order
- **File Formats**: .kml files and HTTP/HTTPS URLs

## Future Enhancements

1. **Async Support**: Async querysets for large files
2. **Streaming**: Process large KML files without loading entirely into memory
3. **Schema Evolution**: Handle KML schema changes gracefully
4. **Plugin System**: Custom parsers and data processors
5. **CLI Tools**: Command-line utilities for KML processing
6. **REST API**: Optional web API for KML data
7. **Visualization**: Integration with mapping libraries (Folium, Plotly, etc.)

## Use Cases

### Research and Academia
- Process scientific GPS tracking data
- Analyze geospatial survey results
- Convert field data for analysis

### Business Applications
- Import store/facility locations from Google Earth
- Process customer location data
- Analyze delivery routes and territories

### Government and GIS
- Process public facility data
- Analyze transportation networks
- Convert legacy KML datasets

### Personal Projects
- Process travel routes and waypoints
- Organize personal location collections
- Convert between geospatial formats

## Current Implementation Status

This specification reflects the current state of the kmlorm library as implemented. The following features are **fully implemented and tested**:

### ✅ Implemented Features
- **Core Models**: All KML element types (Placemark, Folder, Point, Path, Polygon, MultiGeometry)
- **Django-style API**: QuerySet methods (`.all()`, `.filter()`, `.get()`, etc.)
- **Geospatial Queries**: `.has_coordinates()`, `.valid_coordinates()`, `.near()`, `.within_bounds()`
- **Field Lookups**: `name__icontains`, `address__contains`, etc.
- **KML Parsing**: Full lxml-based XML/KML parsing with namespace support
- **URL Integration**: Load KML from HTTP/HTTPS URLs
- **Data Access**: `to_dict()` methods for all models for external library integration
- **Hierarchical Structure**: Nested folders with `.all()` (includes nested) and `.children()` (direct children) methods
- **Type Safety**: Full type annotations throughout
- **Comprehensive Testing**: 22 test files with documentation validation

### 🚧 Reserved for Future
- **spatial/**: Directory exists but no spatial indexing implemented
- **utils/**: Directory exists but no utility functions implemented
- **exports/**: Directory exists but no built-in export formats

### 📋 Testing Strategy
- **Documentation Tests**: All examples in docs are automatically tested
- **Integration Tests**: Real-world KML files and URL loading
- **Coverage**: Extensive test coverage across all implemented functionality
- **Type Checking**: Full mypy validation

This specification provides a comprehensive Django-style ORM interface for KML data, filling a significant gap in the Python geospatial ecosystem while remaining framework-agnostic and highly reusable.