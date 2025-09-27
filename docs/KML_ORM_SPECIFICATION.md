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
# - Use PostGIS connectors for database export
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

    # Export
    DEFAULT_SRID = 4326
    GEOJSON_PRECISION = 6
```

## Package Structure

```
kmlorm/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── managers.py          # KMLManager, RelatedManager
│   ├── querysets.py         # KMLQuerySet with all methods
│   ├── fields.py            # CoordinateField, etc.
│   └── exceptions.py        # All exception classes
├── models/
│   ├── __init__.py
│   ├── base.py             # KMLElement base class
│   ├── placemark.py        # Placemark model
│   ├── folder.py           # Folder model
│   ├── path.py             # Path/LineString model
│   └── polygon.py          # Polygon model
├── parsers/
│   ├── __init__.py
│   ├── xml_parser.py       # Built-in XML parser (lxml/stdlib)
│   └── validation.py       # KML validation
├── spatial/
│   ├── __init__.py
│   ├── index.py            # Spatial indexing (R-tree, etc.)
│   ├── operations.py       # Spatial operations
│   └── utils.py            # Coordinate utilities
├── exports/
│   ├── __init__.py
│   ├── django_export.py    # Django model export
│   ├── postgis_export.py   # PostGIS export
│   ├── geojson_export.py   # GeoJSON export
│   └── pandas_export.py    # DataFrame export
├── utils/
│   ├── __init__.py
│   ├── caching.py          # QuerySet caching
│   └── helpers.py          # Utility functions
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_querysets.py
    ├── test_spatial.py
    ├── test_exports.py
    └── fixtures/
        ├── sample.kml
        ├── complex.kml
        └── invalid.kml
```

## Dependencies

### Required
- `lxml` - XML parsing (with stdlib fallback)
- `typing-extensions` - Type hints for older Python

### Optional
- `django` - For Django model export
- `sqlalchemy` - For database export
- `psycopg2` or `psycopg3` - For PostGIS export
- `pandas` - For DataFrame export
- `geopandas` - For GeoDataFrame export
- `shapely` - For advanced spatial operations
- `rtree` - For spatial indexing performance

## Compatibility

- **Python**: 3.8+
- **KML**: Google Earth KML/KMZ, OGC KML 2.2
- **Coordinate Systems**: WGS84 (EPSG:4326) primary, others via transformation
- **File Formats**: .kml, .kmz (zipped KML)

## Future Enhancements

1. **Async Support**: Async querysets for large files
2. **Streaming**: Process large KML files without loading entirely into memory
3. **Schema Evolution**: Handle KML schema changes gracefully
4. **Plugin System**: Custom parsers and exporters
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

This specification provides a comprehensive Django-style ORM interface for KML data, filling a significant gap in the Python geospatial ecosystem while remaining framework-agnostic and highly reusable.