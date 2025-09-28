Tutorial
========

This tutorial covers advanced features and patterns for working with KML ORM.

Advanced Querying
-----------------

.. note:: **Folder Hierarchy Behavior**

   KML ORM provides two methods for accessing elements:

   * Direct children only: ``kml.placemarks.children()``
   * All elements (including nested): ``kml.placemarks.all()``

Field Lookups
~~~~~~~~~~~~~

KML ORM supports various Django-style field lookups:

.. code-block:: python

   from kmlorm import KMLFile

   kml = KMLFile.from_file('stores.kml')

   # Exact match (default) - includes all elements including nested
   exact = kml.placemarks.all().filter(name='Capital Electric Supply')

   # Case-insensitive contains
   contains = kml.placemarks.all().filter(name__icontains='electric')

   # Starts with / ends with
   starts = kml.placemarks.all().filter(name__startswith='Capital')
   ends = kml.placemarks.all().filter(name__endswith='Store')

   # In a list of values
   multiple = kml.placemarks.all().filter(name__in=['Hardware Store', 'Electric Depot'])

   # Null checks
   with_description = kml.placemarks.all().filter(description__isnull=False)
   without_description = kml.placemarks.all().filter(description__isnull=True)

   # Regular expressions
   regex_match = kml.placemarks.all().filter(name__regex=r'^Capital.*Electric.*$')

Complex Queries
~~~~~~~~~~~~~~~

Combine multiple filters and use Q objects for complex logic:

.. code-block:: python

   # Multiple filters (AND logic)
   result = (kml.placemarks
       .filter(name__icontains='electric')
       .filter(visibility=True)
       .exclude(description__isnull=True)
   )

   # Geospatial + attribute filtering
   baltimore_electric_stores = (kml.placemarks
       .filter(name__icontains='electric')
       .near(-76.6, 39.3, radius_km=25)
       .has_coordinates()
   )

Working with Hierarchies
------------------------

Folder Navigation
~~~~~~~~~~~~~~~~~

Navigate folder hierarchies and access nested elements:

.. code-block:: python

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

Cross-Folder Queries
~~~~~~~~~~~~~~~~~~~~

Query across all folders simultaneously:

.. code-block:: python

   # All placemarks regardless of folder (includes nested)
   all_stores = kml.placemarks.all().filter(name__icontains='store')

   # Get placemarks from specific folder (direct children only)
   supply_folder = kml.folders.children().get(name='Supply Locations')
   supply_stores = supply_folder.placemarks.children()

**Important**: ``kml.placemarks.all()`` includes all placemarks including
those in nested folders. Use ``kml.placemarks.children()`` for direct
children only.

Coordinate Operations
---------------------

Distance Calculations
~~~~~~~~~~~~~~~~~~~~~

.. note:: **About Distance Calculations**

   KML ORM calculates **straight-line distances** (great circle distances) between geographic points,
   not travel distances by vehicle or foot. These are "as the crow flies" distances that account
   for Earth's curvature but ignore terrain, roads, and other travel constraints.

   * **Accuracy**: Within 0.5% for distances up to hundreds of kilometers
   * **Method**: Haversine formula using Earth's mean radius (6371 km)
   * **Limitations**: 2D calculations only (altitude ignored), spherical Earth assumption

   For detailed technical information, see :doc:`api/querysets` under "Distance Calculation Details".

Calculate distances between placemarks:

.. code-block:: python

   # Get two placemarks (includes nested)
   store1 = kml.placemarks.all().get(name__contains='Rosedale')
   store2 = kml.placemarks.all().get(name__contains='Timonium')

   # Calculate distance
   if store1.coordinates and store2.coordinates:
       distance = store1.distance_to(store2)
       print(f"Distance: {distance:.2f} km")

Bearing Calculations
~~~~~~~~~~~~~~~~~~~~

Calculate bearing between points:

.. code-block:: python

   if store1.coordinates and store2.coordinates:
       bearing = store1.bearing_to(store2)
       print(f"Bearing: {bearing:.1f}°")

Working with Different Geometry Types
-------------------------------------

Paths (LineStrings)
~~~~~~~~~~~~~~~~~~~

Work with path/route data:

.. code-block:: python

   # Get all paths (direct children only)
   paths = kml.paths.children()

   for path in paths:
       print(f"Path: {path.name}")
       if path.coordinates:
           print(f"  Points: {len(path.coordinates)}")
           print(f"  Length: {path.calculate_length():.2f} km")

Polygons
~~~~~~~~

Work with polygon areas:

.. code-block:: python

   # Get all polygons (direct children only)
   polygons = kml.polygons.children()

   for polygon in polygons:
       print(f"Polygon: {polygon.name}")
       if polygon.outer_boundary:
           print(f"  Boundary points: {len(polygon.outer_boundary)}")
           print(f"  Has holes: {len(polygon.inner_boundaries) > 0}")

Data Validation
---------------

Validate Elements
~~~~~~~~~~~~~~~~~

Ensure data integrity with validation:

.. code-block:: python

   from kmlorm.core.exceptions import KMLValidationError

   for placemark in kml.placemarks.all():
       try:
           if placemark.validate():
               print(f"✓ {placemark.name} is valid")
       except KMLValidationError as e:
           print(f"✗ {placemark.name} validation failed: {e}")

Coordinate Validation
~~~~~~~~~~~~~~~~~~~~~

Validate coordinate ranges:

.. code-block:: python

   from kmlorm.models.point import Coordinate

   try:
       # Valid coordinate
       coord = Coordinate(longitude=-76.5, latitude=39.3)
       coord.validate()

       # Invalid coordinate (will raise exception)
       invalid = Coordinate(longitude=200, latitude=100)
       invalid.validate()
   except KMLValidationError as e:
       print(f"Invalid coordinate: {e}")

Performance Optimization
------------------------

Efficient Querying
~~~~~~~~~~~~~~~~~~

Use efficient query patterns for better performance:

.. code-block:: python

   # Good: Use specific filters early
   nearby_electric = (kml.placemarks
       .filter(name__icontains='electric')  # Filter first
       .near(-76.6, 39.3, radius_km=10)     # Then apply geospatial
   )

   # Less efficient: Geospatial first on large dataset
   all_nearby = kml.placemarks.near(-76.6, 39.3, radius_km=50)
   electric_nearby = all_nearby.filter(name__icontains='electric')

Batch Operations
~~~~~~~~~~~~~~~~

Process large datasets efficiently:

.. code-block:: python

   # Process in batches
   all_placemarks = kml.placemarks.all()
   batch_size = 100

   for i in range(0, len(all_placemarks), batch_size):
       batch = all_placemarks[i:i + batch_size]
       process_batch(batch)

   def process_batch(placemarks):
       for placemark in placemarks:
           # Process individual placemark
           if placemark.coordinates:
               validate_location(placemark)

Error Handling Patterns
-----------------------

Graceful Error Handling
~~~~~~~~~~~~~~~~~~~~~~~

Handle errors gracefully in production code:

.. code-block:: python

   import logging
   from kmlorm.core.exceptions import (
       KMLParseError,
       KMLElementNotFound,
       KMLValidationError
   )

   logger = logging.getLogger(__name__)

   def safe_kml_processing(file_path):
       try:
           kml = KMLFile.from_file(file_path)

           # Process with error handling
           for placemark in kml.placemarks.all():
               try:
                   if placemark.validate():
                       process_placemark(placemark)
               except KMLValidationError as e:
                   logger.warning(f"Skipping invalid placemark {placemark.name}: {e}")
                   continue

       except KMLParseError as e:
           logger.error(f"Failed to parse KML file {file_path}: {e}")
           return None
       except Exception as e:
           logger.error(f"Unexpected error processing {file_path}: {e}")
           raise

   def process_placemark(placemark):
       # Your processing logic here
       pass

Integration Patterns
--------------------

With Pandas
~~~~~~~~~~~

Convert KML data to pandas DataFrames:

.. code-block:: python

   import pandas as pd

   def kml_to_dataframe(kml_file):
       data = []
       for placemark in kml_file.placemarks.all():
           row = {
               'name': placemark.name,
               'description': placemark.description,
               'longitude': placemark.longitude,
               'latitude': placemark.latitude,
               'altitude': placemark.altitude,
               'address': placemark.address,
               'phone': placemark.phone_number,
           }
           data.append(row)

       return pd.DataFrame(data)

   # Usage
   kml = KMLFile.from_file('stores.kml')
   df = kml_to_dataframe(kml)
   print(df.head())

With GeoPandas
~~~~~~~~~~~~~~

Convert to GeoPandas for advanced geospatial analysis:

.. code-block:: python

   import geopandas as gpd
   from shapely.geometry import Point

   def kml_to_geodataframe(kml_file):
       data = []
       geometries = []

       for placemark in kml_file.placemarks.all():
           if placemark.coordinates:
               # Create Shapely Point
               point = Point(placemark.longitude, placemark.latitude)
               geometries.append(point)

               # Create data row
               data.append({
                   'name': placemark.name,
                   'description': placemark.description,
                   'address': placemark.address,
               })

       # Create GeoDataFrame
       gdf = gpd.GeoDataFrame(data, geometry=geometries, crs='EPSG:4326')
       return gdf

   # Usage
   kml = KMLFile.from_file('stores.kml')
   gdf = kml_to_geodataframe(kml)

   # Now you can use GeoPandas operations
   # Buffer points by 1km
   buffered = gdf.buffer(0.01)  # roughly 1km at this latitude

Custom Extensions
-----------------

Extending Models
~~~~~~~~~~~~~~~~

Create custom model extensions:

.. code-block:: python

   from kmlorm import Placemark

   class Store(Placemark):
       @property
       def is_open(self):
           # Custom business logic
           return getattr(self, 'hours', None) is not None

       def distance_to_customer(self, customer_location):
           if self.coordinates and customer_location:
               return self.distance_to(customer_location)
           return float('inf')

   # Usage
   store = Store(name="My Store", coordinates=(-76.5, 39.3))
   distance = store.distance_to_customer((-76.6, 39.4))

Next Steps
----------

* Explore the complete :doc:`api/index` documentation
* Check out real-world :doc:`examples`
* Learn about :doc:`contributing` to the project