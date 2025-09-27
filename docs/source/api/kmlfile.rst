KMLFile
=======

The :class:`~kmlorm.parsers.kml_file.KMLFile` class is the main entry point for loading and working with KML data.

It can be imported directly from the main package:

.. code-block:: python

   from kmlorm import KMLFile

.. note::
   **Understanding flatten Parameter**

   By default, manager methods like ``kml.placemarks.all()`` only return elements at the document root level.
   To include elements from nested folders, use ``flatten=True``:

   * ``kml.placemarks.all()`` - Root-level placemarks only
   * ``kml.placemarks.all(flatten=True)`` - All placemarks including nested ones

   This applies to all element types: placemarks, folders, paths, polygons, points, and multigeometries.

.. automodule:: kmlorm.parsers.kml_file
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Loading KML Data
----------------

The KMLFile class provides several class methods for loading KML data from different sources:

.. automethod:: kmlorm.parsers.kml_file.KMLFile.from_file

.. automethod:: kmlorm.parsers.kml_file.KMLFile.from_string

.. automethod:: kmlorm.parsers.kml_file.KMLFile.from_url

Working with Managers
---------------------

Once loaded, KMLFile provides Django-style managers for accessing different types of KML elements. Each manager provides the full QuerySet API for filtering, querying, and manipulating elements.

**Available Managers:**

* :attr:`~kmlorm.parsers.kml_file.KMLFile.folders` - :class:`~kmlorm.core.managers.FolderManager` for accessing folders
* :attr:`~kmlorm.parsers.kml_file.KMLFile.placemarks` - :class:`~kmlorm.core.managers.PlacemarkManager` for accessing placemarks
* :attr:`~kmlorm.parsers.kml_file.KMLFile.paths` - :class:`~kmlorm.core.managers.PathManager` for accessing paths (LineStrings)
* :attr:`~kmlorm.parsers.kml_file.KMLFile.polygons` - :class:`~kmlorm.core.managers.PolygonManager` for accessing polygons
* :attr:`~kmlorm.parsers.kml_file.KMLFile.points` - :class:`~kmlorm.core.managers.PointManager` for accessing points
* :attr:`~kmlorm.parsers.kml_file.KMLFile.multigeometries` - :class:`~kmlorm.core.managers.MultiGeometryManager` for accessing multi-geometries

Each manager supports the full range of Django-style query methods including ``.filter()``, ``.get()``, ``.near()``, ``.within_bounds()``, and more. See :doc:`querysets` for complete documentation of available query methods.

.. code-block:: python

   from kmlorm import KMLFile

   kml = KMLFile.from_file('example.kml')

   # Access different element types (root-level only)
   root_placemarks = kml.placemarks.all()
   root_folders = kml.folders.all()
   root_paths = kml.paths.all()
   root_polygons = kml.polygons.all()
   root_points = kml.points.all()
   root_multigeometries = kml.multigeometries.all()

   # Access ALL elements including those nested in folders
   all_placemarks = kml.placemarks.all(flatten=True)
   all_folders = kml.folders.all(flatten=True)
   all_paths = kml.paths.all(flatten=True)
   all_polygons = kml.polygons.all(flatten=True)
   all_points = kml.points.all(flatten=True)
   all_multigeometries = kml.multigeometries.all(flatten=True)

Document Properties
-------------------

.. autoattribute:: kmlorm.parsers.kml_file.KMLFile.document_name

.. autoattribute:: kmlorm.parsers.kml_file.KMLFile.document_description

Utility Methods
---------------

.. automethod:: kmlorm.parsers.kml_file.KMLFile.element_counts

.. automethod:: kmlorm.parsers.kml_file.KMLFile.all_elements

Complete Usage Examples
-----------------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from kmlorm import KMLFile

   # Load from various sources
   kml_from_file = KMLFile.from_file('data.kml')
   kml_from_url = KMLFile.from_url('https://example.com/data.kml')
   kml_from_string = KMLFile.from_string(kml_content)

   # Access document metadata
   print(f"Document: {kml_from_file.document_name}")
   print(f"Description: {kml_from_file.document_description}")

   # Get element counts
   counts = kml_from_file.element_counts()
   print(f"Total placemarks: {counts['placemarks']}")
   print(f"Total folders: {counts['folders']}")

Querying Elements
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm import KMLFile

   kml = KMLFile.from_file('stores.kml')

   # Basic queries (root-level elements only)
   capital_stores = kml.placemarks.filter(name__icontains='capital')
   visible_folders = kml.folders.filter(visibility=True)

   # Comprehensive queries (including nested elements)
   all_capital_stores = kml.placemarks.all(flatten=True).filter(name__icontains='capital')
   all_visible_folders = kml.folders.all(flatten=True).filter(visibility=True)

   # Geospatial queries
   nearby_stores = kml.placemarks.all(flatten=True).near(-76.6, 39.3, radius_km=25)
   bounded_elements = kml.placemarks.all(flatten=True).within_bounds(
       north=39.5, south=39.0, east=-76.0, west=-77.0
   )

   # Get specific elements
   try:
       specific_store = kml.placemarks.all(flatten=True).get(name='Capital Electric - Rosedale')
       print(f"Found: {specific_store.name} at {specific_store.address}")
   except KMLElementNotFound:
       print("Store not found")

Working with All Elements
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm import KMLFile

   kml = KMLFile.from_file('comprehensive.kml')

   # Get all elements as a single list
   all_elements = kml.all_elements()
   print(f"Total elements in KML: {len(all_elements)}")

   # Process different element types
   for element in all_elements:
       if hasattr(element, 'coordinates') and element.coordinates:
           print(f"{element.__class__.__name__}: {element.name} at {element.coordinates}")
       else:
           print(f"{element.__class__.__name__}: {element.name}")