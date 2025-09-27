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
* lxml (recommended, automatically detected)

.. note:: **Working with Folders**

   KML files often organize placemarks inside folders. By default,
   ``kml.placemarks.all()`` only returns placemarks at the document level.
   To include placemarks from all folders, use ``kml.placemarks.all(flatten=True)``.

   * Document-level only: ``kml.placemarks.all()``
   * All placemarks (including those in folders): ``kml.placemarks.all(flatten=True)``

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
   root_placemarks = kml.placemarks.all()
   print(f"Found {len(root_placemarks)} root-level placemarks")

   # Get ALL placemarks including those nested in folders
   all_placemarks = kml.placemarks.all(flatten=True)
   print(f"Found {len(all_placemarks)} total placemarks")

   # Access different element types
   folders = kml.folders.all()
   paths = kml.paths.all()
   polygons = kml.polygons.all()
   points = kml.points.all()
   multigeometries = kml.multigeometries.all()

   # Or get ALL elements of each type using flatten=True
   all_folders = kml.folders.all(flatten=True)
   all_paths = kml.paths.all(flatten=True)
   all_polygons = kml.polygons.all(flatten=True)
   all_points = kml.points.all(flatten=True)
   all_multigeometries = kml.multigeometries.all(flatten=True)

**Understanding flatten=True:**

- ``all()`` returns only elements that are **direct children of the Document**
- ``all(flatten=True)`` returns all elements including those nested inside Folders
- This applies to **all element types**: placemarks, folders, paths, polygons, points, and multigeometries
- Most real-world KML files organize elements in nested folders, so ``flatten=True`` is often needed

**KML Structure Example:**

.. code-block:: xml

   <kml>
     <Document>
       <Folder>
         <Folder>...</Folder>           <!-- Nested folder: requires flatten=True -->
         <Placemark>...</Placemark>     <!-- Nested placemark: requires flatten=True -->
         <Path>...</Path>               <!-- Nested path: requires flatten=True -->
         <MultiGeometry>...</MultiGeometry> <!-- Nested multigeometry: requires flatten=True -->
       </Folder>
       <Folder>...</Folder>             <!-- Direct child folder: found by all() -->
       <Placemark>...</Placemark>       <!-- Direct child placemark: found by all() -->
       <Path>...</Path>                 <!-- Direct child path: found by all() -->
       <MultiGeometry>...</MultiGeometry> <!-- Direct child multigeometry: found by all() -->
     </Document>
   </kml>

Basic Queries
~~~~~~~~~~~~~

Filter elements using Django-style query methods:

.. code-block:: python

   # Filter by name (root-level placemarks only)
   capital_stores = kml.placemarks.filter(name__icontains='capital')

   # Filter ALL placemarks including those in folders
   all_capital_stores = kml.placemarks.all(flatten=True).filter(name__icontains='capital')

   # Exclude items (root-level only)
   not_capital = kml.placemarks.exclude(name__icontains='capital')

   # Exclude ALL placemarks including those in folders
   all_not_capital = kml.placemarks.all(flatten=True).exclude(name__icontains='capital')

   # Get a single item (searches root-level only)
   store = kml.placemarks.get(name='Capital Electric - Rosedale')

   # Get from ALL placemarks including folders
   store = kml.placemarks.all(flatten=True).get(name='Capital Electric - Rosedale')

   # Check if items exist (root-level only)
   has_stores = kml.placemarks.filter(name__icontains='store').exists()

   # Check ALL placemarks including folders
   has_any_stores = kml.placemarks.all(flatten=True).filter(name__icontains='store').exists()

.. note:: **Important: Searching All vs. Root-Level Elements**

   The query methods like ``filter()``, ``exclude()``, ``get()``, and ``exists()`` operate on the manager's current elements:

   * ``kml.placemarks.filter()`` - Searches only root-level placemarks
   * ``kml.placemarks.all(flatten=True).filter()`` - Searches ALL placemarks including nested ones

   Since most real-world KML files organize elements in folders, you'll typically want to use ``all(flatten=True)`` before applying filters to search the entire document.

Working with Coordinates
~~~~~~~~~~~~~~~~~~~~~~~~

Access coordinate data from placemarks:

.. code-block:: python

   for placemark in kml.placemarks.all():
       if placemark.coordinates:
           print(f"{placemark.name}: {placemark.longitude}, {placemark.latitude}")

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
       # Simple distance calculation (you might use a proper geospatial library)
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