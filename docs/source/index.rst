KML ORM Documentation
=====================

A Django-style ORM for KML (Keyhole Markup Language) files that provides intuitive,
chainable query interfaces for geospatial data without requiring Django as a dependency.

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   quickstart
   tutorial
   query_behavior
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/index
   api/kmlfile
   api/models
   api/querysets
   api/coordinates
   api/exceptions

.. toctree::
   :maxdepth: 1
   :caption: Development:

   contributing

Features
--------

* **Django-style API**: Familiar ``.objects.all()``, ``.filter()``, ``.get()`` methods
* **Chainable queries**: Build complex geospatial queries step by step
* **Type hints**: Full type annotation support for modern Python development
* **Django knowledge transfers**: Use the Django patterns that you know and love to parse and examine KML (now with less Django!)
* **Geospatial operations**: Built-in spatial queries like ``.near()``, ``.within_bounds()``
* **Python data structures**: Access KML data as native Python objects

Quick Example
-------------

.. code-block:: python

   from kmlorm import KMLFile

   # Load KML file
   kml = KMLFile.from_file('places.kml')

   # Query placemarks (includes those in nested folders)
   all_places = kml.placemarks.all()
   capital_stores = kml.placemarks.all().filter(name__icontains='capital')
   nearby = kml.placemarks.all().near(-76.6, 39.3, radius_km=25)

   # Chain queries
   nearby_open = (kml.placemarks.all()
       .filter(name__icontains='electric')
       .near(-76.6, 39.3, radius_km=50)
       .filter(visibility=True)
   )

Hierarchical Querying
----------------------

Work with nested folder structures using intuitive methods:

.. code-block:: python

   # Get only direct children (root-level placemarks)
   root_placemarks = kml.placemarks.children()

   # Get ALL placemarks including nested ones
   all_placemarks = kml.placemarks.all()

   # Same pattern works for folders
   root_folders = kml.folders.children()
   all_folders = kml.folders.all()

Installation
------------

.. code-block:: bash

   pip install kmlorm

Requirements
------------

* Python 3.11+
* lxml

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

