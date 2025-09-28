Quick Start Guide
=================

This guide will get you up and running with KML ORM in just a few minutes.

Installation
------------

Install KML ORM using pip:

.. code-block:: bash

   pip install kmlorm

Requirements
~~~~~~~~~~~~

* Python 3.11+
* lxml

.. note:: **Working with Folders**

   KML files often organize placemarks inside folders. By default,
   ``kml.placemarks.all()`` returns all the placemarks in a document
   even though they may be nested below the top level document.  Think of ``kml.placemarks.all()``
   as roughly equivalent to Django's ``Placemark.objects.all()`` queryset.  In Django, the 
   database is implied.  To make a true parallel, the Django statement would be written, 
   ``database.Placemark.objects.all()``. (Don't.  That won't work in Django. We are just drawing
   comparisons for understanding.)

   To retrieve placemarks only at the "root" level, use ``kml.placemarks.children()``.

   This changed in version 1.0.0.  Prior to this version, to get the placemarks at the "root" level, the statement was ``kml.placemarks.all()``, and to get all the placemarks in a file, the statement was ``kml.placemarks.all(flatten=True)``.

   * Document-level only: ``kml.placemarks.children()``
   * All placemarks (including those in folders): ``kml.placemarks.all()``

Basic Usage
-----------

Loading KML Data
~~~~~~~~~~~~~~~~

KML ORM can load KML data from files, strings, or URLs:

.. code-block:: python

   from kmlorm import KMLFile

   # From file
   kml = KMLFile.from_file('places.kml')

   # From string
   kml_string = """<?xml version="1.0" encoding="UTF-8"?>
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
   kml = KMLFile.from_string(kml_string)

   # From URL (example with localhost server)
   kml = KMLFile.from_url('http://localhost:8000/data.kml')

Accessing Elements
~~~~~~~~~~~~~~~~~~

Once loaded, use Django-style managers to access different element types:

.. code-block:: python

   # Get placemarks at document root level only
   root_placemarks = kml.placemarks.children()
   print(f"Found {len(root_placemarks)} root-level placemarks")

   # Get ALL placemarks including those nested in folders
   all_placemarks = kml.placemarks.all()
   print(f"Found {len(all_placemarks)} total placemarks")

   # Access different element types at the "root" level
   folders = kml.folders.children()
   paths = kml.paths.children()
   polygons = kml.polygons.children()
   points = kml.points.children()
   multigeometries = kml.multigeometries.children()

   # Or get ALL elements of each type using all()
   all_folders = kml.folders.all()
   all_paths = kml.paths.all()
   all_polygons = kml.polygons.all()
   all_points = kml.points.all()
   all_multigeometries = kml.multigeometries.all()

**KML Structure Example:**

.. code-block:: xml

   <kml>
     <Document>
       <Folder>
         <Folder>...</Folder>           <!-- Nested folder: found by all() -->
         <Placemark>...</Placemark>     <!-- Nested placemark: found by all() -->
         <Path>...</Path>               <!-- Nested path: found by all() -->
         <MultiGeometry>...</MultiGeometry> <!-- Nested multigeometry: found by all() -->
       </Folder>
       <Folder>...</Folder>             <!-- Direct child folder: found by children() -->
       <Placemark>...</Placemark>       <!-- Direct child placemark: found by children() -->
       <Path>...</Path>                 <!-- Direct child path: found by children() -->
       <MultiGeometry>...</MultiGeometry> <!-- Direct child multigeometry: found by children() -->
     </Document>
   </kml>

Basic Queries
~~~~~~~~~~~~~

Filter elements using Django-style query methods:

.. code-block:: python

   # Filter by name (root-level placemarks only)
   capital_stores = kml.placemarks.filter(name__icontains='capital')

   # Filter ALL placemarks including those in folders
   all_capital_stores = kml.placemarks.all().filter(name__icontains='capital')

   # Exclude items (root-level only)
   not_capital = kml.placemarks.exclude(name__icontains='capital')

   # Exclude ALL placemarks including those in folders
   all_not_capital = kml.placemarks.all().exclude(name__icontains='capital')

   # Get a single item (searches root-level only)
   store = kml.placemarks.get(name='Capital Electric - Rosedale')

   # Get from ALL placemarks including folders
   store = kml.placemarks.all().get(name='Capital Electric - Rosedale')

   # Check if items exist (root-level only)
   has_stores = kml.placemarks.filter(name__icontains='store').exists()

   # Check ALL placemarks including folders
   has_any_stores = kml.placemarks.all().filter(name__icontains='store').exists()

.. note:: **Important: Searching All vs. Root-Level Elements**

   The query methods like ``filter()``, ``exclude()``, ``get()``, and ``exists()`` operate on the manager's current elements:

   * ``kml.placemarks.children().filter()`` - Searches only root-level placemarks
   * ``kml.placemarks.all().filter()`` - Searches ALL placemarks including nested ones

   Since most real-world KML files organize elements in folders, you'll typically want to use ``all()`` before applying filters to search the entire document.

Working with Coordinates
~~~~~~~~~~~~~~~~~~~~~~~~

Access coordinate data from placemarks:

.. code-block:: python

   for placemark in kml.placemarks.all():
       if placemark.coordinates:
           print(f"{placemark.name}: {placemark.longitude}, {placemark.latitude}")

Spatial Calculations
~~~~~~~~~~~~~~~~~~~~

Calculate distances, bearings, and midpoints between geographic locations:

.. code-block:: python

   from kmlorm.spatial import DistanceUnit

   # Get two placemarks
   store1 = kml.placemarks.get(name='Store A')
   store2 = kml.placemarks.get(name='Store B')

   # Calculate distance (default: kilometers)
   distance_km = store1.distance_to(store2)
   print(f"Distance: {distance_km:.1f} km")

   # Calculate in different units
   distance_miles = store1.distance_to(store2, unit=DistanceUnit.MILES)
   print(f"Distance: {distance_miles:.1f} miles")

   # Calculate bearing (compass direction)
   bearing = store1.bearing_to(store2)
   print(f"Direction: {bearing:.1f}°")

   # Find midpoint between locations
   midpoint = store1.midpoint_to(store2)
   print(f"Midpoint: {midpoint.longitude:.4f}, {midpoint.latitude:.4f}")

   # Distance to specific coordinates (tuple or list)
   baltimore = (-76.6, 39.3)
   distance = store1.distance_to(baltimore)
   print(f"Distance to Baltimore: {distance:.1f} km")

Geospatial Queries
~~~~~~~~~~~~~~~~~~

Find elements based on location:

.. code-block:: python

   # Find placemarks near Baltimore (within 25 km)
   nearby = kml.placemarks.near(-76.6, 39.3, radius_km=25)

   # Find placemarks within a bounding box
   in_area = kml.placemarks.within_bounds(
       north=39.5, south=39.0,
       east=-76.0, west=-77.0
   )

   # Only placemarks with coordinates
   with_location = kml.placemarks.has_coordinates()

Chaining Queries
~~~~~~~~~~~~~~~~

Combine multiple query methods for complex filtering:

.. code-block:: python

   # Complex query
   result = (kml.placemarks
       .filter(name__icontains='electric')
       .near(-76.6, 39.3, radius_km=50)
       .has_coordinates()
       .order_by('name')
   )

   for placemark in result:
       print(f"- {placemark.name}")

Complete Example
----------------

Here's a complete example that demonstrates common usage patterns:

.. code-block:: python

   from kmlorm import KMLFile
   from kmlorm.core.exceptions import KMLParseError, KMLElementNotFound

   def analyze_kml_file(file_path):
       try:
           # Load the KML file
           kml = KMLFile.from_file(file_path)

           print(f"Document: {kml.document_name}")
           print(f"Description: {kml.document_description}")
           print()

           # Show element counts
           counts = kml.element_counts()
           for element_type, count in counts.items():
               print(f"{element_type.title()}: {count}")
           print()

           # Find stores near Baltimore
           nearby_stores = (kml.placemarks
               .filter(name__icontains='store')
               .near(-76.6, 39.3, radius_km=30)
               .order_by('name')
           )

           print(f"Stores near Baltimore ({nearby_stores.count()}):")
           for store in nearby_stores:
               distance = calculate_distance_to_baltimore(store)
               print(f"- {store.name} ({distance:.1f} km away)")

           # Get a specific store
           try:
               rosedale_store = kml.placemarks.get(name__contains='Rosedale')
               print(f"\nRosedale store: {rosedale_store.address}")
           except KMLElementNotFound:
               print("\nNo Rosedale store found")

       except KMLParseError as e:
           print(f"Error parsing KML file: {e}")
       except Exception as e:
           print(f"Unexpected error: {e}")

   def calculate_distance_to_baltimore(placemark):
       # Using built-in spatial calculations
       if placemark.coordinates:
           # Baltimore coordinates: -76.6, 39.3
           baltimore_coord = (-76.6, 39.3)
           return placemark.distance_to(baltimore_coord)
       return 0

   # Run the analysis
   if __name__ == "__main__":
       analyze_kml_file('example.kml')

Error Handling
--------------

Always handle potential errors when working with KML data:

.. code-block:: python

   from kmlorm.core.exceptions import (
       KMLParseError,
       KMLElementNotFound,
       KMLMultipleElementsReturned
   )

   try:
       kml = KMLFile.from_file('data.kml')
       store = kml.placemarks.get(name='My Store')
   except KMLParseError:
       print("Invalid KML file")
   except KMLElementNotFound:
       print("Store not found")
   except KMLMultipleElementsReturned:
       print("Multiple stores found, be more specific")

Next Steps
----------

* Read the :doc:`tutorial` for more detailed examples
* Explore the :doc:`api/index` for complete API documentation
* Check out :doc:`examples` for real-world use cases