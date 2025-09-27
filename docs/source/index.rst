KML ORM Documentation
=====================

A Django-style ORM for KML (Keyhole Markup Language) files that provides intuitive,
chainable query interfaces for geospatial data without requiring Django as a dependency.

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   quickstart
   tutorial
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
* **No Django dependency**: Use Django patterns without the framework
* **Geospatial operations**: Built-in spatial queries like ``.near()``, ``.within_bounds()``
* **Multiple export formats**: Export to GeoJSON, PostGIS, pandas, and more

Quick Example
-------------

.. code-block:: python

   from kmlorm import KMLFile

   # Load KML file
   kml = KMLFile.from_file('places.kml')

   # Query placemarks (use flatten=True to include those in folders)
   all_places = kml.placemarks.all(flatten=True)
   capital_stores = kml.placemarks.all(flatten=True).filter(name__icontains='capital')
   nearby = kml.placemarks.all(flatten=True).near(-76.6, 39.3, radius_km=25)

   # Chain queries
   nearby_open = (kml.placemarks.all(flatten=True)
       .filter(name__icontains='electric')
       .near(-76.6, 39.3, radius_km=50)
       .filter(visibility=True)
   )

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

