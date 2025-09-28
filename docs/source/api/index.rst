API Reference
=============

Complete reference documentation for KML ORM's classes, methods, and utilities.

Core Components
---------------

.. toctree::
   :maxdepth: 1

   kmlfile
   models
   querysets
   coordinates
   exceptions

Quick Navigation
----------------

**Data Loading & Management**
   :doc:`kmlfile` - Load and parse KML files from various sources

**Model Classes**
   :doc:`models` - Placemark, Folder, Path, Polygon, Point, and MultiGeometry classes

**Querying & Filtering**
   :doc:`querysets` - Django-style query methods and managers

**Coordinates & Geometry**
   :doc:`coordinates` - Coordinate validation and geometry handling

**Error Handling**
   :doc:`exceptions` - Exception classes and error handling patterns

Overview
--------

KML ORM provides a Django-style ORM for working with KML (Keyhole Markup Language) files.
The API is designed to be familiar to Django developers while providing specialized
functionality for geospatial data manipulation.

**Key Features:**

* **Familiar API**: Django-style ``.objects.all()``, ``.filter()``, ``.get()`` methods
* **Type Safety**: Full type annotation support throughout the API
* **Geospatial Queries**: Built-in spatial operations like ``.near()`` and ``.within_bounds()``
* **Flexible Loading**: Load KML from files, URLs, or strings
* **Robust Validation**: Automatic coordinate and data validation

Getting Started
---------------

For a quick introduction, see the :doc:`../quickstart` guide.
For comprehensive examples, explore the :doc:`../tutorial`.

Example Usage
-------------

.. code-block:: python

   from kmlorm import KMLFile

   # Load KML file
   kml = KMLFile.from_file('places.kml')

   # Query elements (include nested elements)
   all_places = kml.placemarks.all()
   nearby = kml.placemarks.all().near(-76.6, 39.3, radius_km=25)

   # Chain complex queries
   results = (kml.placemarks.all()
       .filter(name__icontains='store')
       .has_coordinates()
       .order_by('name')
   )