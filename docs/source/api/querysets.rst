QuerySets and Managers
======================

KML ORM provides Django-style QuerySets and Managers for filtering and querying KML elements. Managers serve as the interface between models and the database-like operations, providing access to QuerySets which handle the actual filtering, chaining, and data manipulation. When you call methods like ``.filter()`` or ``.all()`` on a manager, it returns a QuerySet that can be further refined with additional filters and operations. This two-tier system allows for intuitive, chainable queries while maintaining clean separation between data access (Managers) and data manipulation (QuerySets).

QuerySet
--------

A QuerySet represents a collection of KML elements that can be filtered, ordered, and manipulated through a fluent interface. The term "QuerySet" originates from Django's ORM, where it describes a lazy, chainable container for database queries that doesn't execute until the data is actually needed. In KML ORM, QuerySets work similarly but operate on in-memory KML data rather than database records.

QuerySets are lazy and chainable, meaning you can apply multiple filters, ordering operations, and transformations without immediately processing the data. The actual filtering and processing occurs when you iterate over the QuerySet, access specific elements, or call evaluation methods. This design allows for efficient composition of complex queries and provides an intuitive interface for data manipulation that feels natural to developers familiar with Django or similar ORMs.

The :class:`~kmlorm.core.querysets.KMLQuerySet` class provides chainable query methods.

.. automodule:: kmlorm.core.querysets
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Manager
-------

A Manager is the interface between KML models and QuerySets, serving as the primary access point for retrieving and manipulating collections of KML elements. The term "Manager" comes from Django's ORM, where it represents the layer responsible for managing database table operations and providing the entry point for queries. In Django, managers are accessed through the ``.objects`` attribute on models, establishing a clean separation between the model definition and query operations.

In KML ORM, managers work similarly but are tailored for KML data structures. Each KML element type has its own specialized manager that provides type-safe access to QuerySets. Managers handle the initial data access and creation of QuerySets, while also providing convenience methods for common operations. They act as the bridge between the high-level model interface and the low-level query operations, ensuring that all data access follows consistent patterns and maintains proper type safety throughout the query chain.

The :class:`~kmlorm.core.managers.KMLManager` class provides the interface for accessing QuerySets.

.. automodule:: kmlorm.core.managers
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Query Methods
------------------

Basic Retrieval
~~~~~~~~~~~~~~~

.. automethod:: kmlorm.core.querysets.KMLQuerySet.all

.. automethod:: kmlorm.core.querysets.KMLQuerySet.filter

.. automethod:: kmlorm.core.querysets.KMLQuerySet.exclude

.. automethod:: kmlorm.core.querysets.KMLQuerySet.get

.. automethod:: kmlorm.core.querysets.KMLQuerySet.first

.. automethod:: kmlorm.core.querysets.KMLQuerySet.last

.. automethod:: kmlorm.core.querysets.KMLQuerySet.count

.. automethod:: kmlorm.core.querysets.KMLQuerySet.exists

Ordering and Slicing
~~~~~~~~~~~~~~~~~~~~

.. automethod:: kmlorm.core.querysets.KMLQuerySet.order_by

.. automethod:: kmlorm.core.querysets.KMLQuerySet.reverse

.. automethod:: kmlorm.core.querysets.KMLQuerySet.distinct

Geospatial Methods
------------------

Distance-Based Queries
~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: kmlorm.core.querysets.KMLQuerySet.near

Bounding Box Queries
~~~~~~~~~~~~~~~~~~~~

.. automethod:: kmlorm.core.querysets.KMLQuerySet.within_bounds

Coordinate Filtering
~~~~~~~~~~~~~~~~~~~~

.. automethod:: kmlorm.core.querysets.KMLQuerySet.has_coordinates

Distance Calculation Details
----------------------------

Understanding Geospatial Accuracy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

KML ORM uses the **Haversine formula** to calculate great circle distances on Earth's surface.
This provides reliable distance calculations for most geospatial applications.

**Technical Implementation:**

* **Formula**: Standard Haversine formula for great circle distances
* **Earth Radius**: 6371 km (mean radius of Earth)
* **Coordinate System**: WGS84 longitude/latitude in decimal degrees
* **Accuracy**: Within 0.5% for distances up to hundreds of kilometers

**Accuracy Characteristics:**

.. code-block:: python

   # Example: 1 degree of latitude ≈ 111.32 km anywhere on Earth
   # 1 degree of longitude ≈ 111.32 km * cos(latitude)

   from kmlorm import KMLFile

   kml = KMLFile.from_file('places.kml')

   # Distance queries are accurate for typical use cases:
   nearby_stores = kml.placemarks.near(-76.6, 39.3, radius_km=25)  # ±125m accuracy
   regional_search = kml.placemarks.near(-76.6, 39.3, radius_km=100)  # ±500m accuracy

**Limitations and Considerations:**

* **Spherical Earth Assumption**: Uses mean Earth radius rather than accounting for ellipsoidal shape
* **2D Calculations**: Altitude/elevation is not considered in distance calculations
* **Great Circle Distance**: Calculates "as the crow flies" distance, not driving/walking routes
* **Coordinate Precision**: Limited by the precision of coordinates in your KML data

**Recommended Use Cases:**

* **Excellent for**: Regional searches, proximity analysis, geographic clustering
* **Good for**: City-scale analysis, finding nearby points of interest
* **Consider alternatives for**: Sub-meter precision requirements, elevation-dependent calculations

**Performance Notes:**

Distance calculations are performed in-memory after loading the KML data. For large datasets
with frequent geospatial queries, consider pre-filtering with bounding boxes before applying
distance-based filters.

Query Examples
--------------

Basic Filtering
~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm import KMLFile

   kml = KMLFile.from_file('places.kml')

   # Get all placemarks
   all_places = kml.placemarks.all()

   # Filter by name
   capital_stores = kml.placemarks.filter(name__icontains='capital')

   # Exclude certain items
   not_capital = kml.placemarks.exclude(name__icontains='capital')

   # Get single item
   rosedale_store = kml.placemarks.get(name__contains='Rosedale')

Geospatial Queries
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Find placemarks near Baltimore
   nearby = kml.placemarks.near(-76.6, 39.3, radius_km=25)

   # Find placemarks within bounding box
   in_area = kml.placemarks.within_bounds(
       north=39.5, south=39.0,
       east=-76.0, west=-77.0
   )

   # Only placemarks with coordinates
   with_location = kml.placemarks.has_coordinates()

Chaining Queries
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Complex query chain
   result = (kml.placemarks
       .filter(name__icontains='electric')
       .near(-76.6, 39.3, radius_km=50)
       .has_coordinates()
       .order_by('name')
   )

Field Lookups
-------------

KML ORM supports Django-style field lookups:

* ``exact`` - Exact match (default)
* ``icontains`` - Case-insensitive contains
* ``contains`` - Case-sensitive contains
* ``startswith`` - Starts with
* ``endswith`` - Ends with
* ``in`` - Value in list
* ``isnull`` - Is null/None
* ``regex`` - Regular expression match

.. code-block:: python

   # Various lookup examples
   kml.placemarks.filter(name='Capital Electric')  # exact
   kml.placemarks.filter(name__icontains='capital')  # case-insensitive
   kml.placemarks.filter(name__startswith='Capital')  # starts with
   kml.placemarks.filter(coordinates__isnull=False)  # has coordinates