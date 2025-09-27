Models
======

KML ORM provides Django-style model classes for representing different types of KML elements.

Base Element
------------

.. automodule:: kmlorm.models.base
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Placemark
---------

Represents point locations with coordinates and metadata.

.. automodule:: kmlorm.models.placemark
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Folder
------

Container for organizing KML elements hierarchically.

.. automodule:: kmlorm.models.folder
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Path (LineString)
-----------------

Represents paths and routes as sequences of coordinates.

.. automodule:: kmlorm.models.path
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Polygon
-------

Represents polygon areas with outer and inner boundaries.

.. automodule:: kmlorm.models.polygon
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Point
-----

Represents standalone Point geometries.

.. automodule:: kmlorm.models.point
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

MultiGeometry
-------------

Container for multiple geometry types within a single element.

.. automodule:: kmlorm.models.multigeometry
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Distance and Bearing Methods
----------------------------

Placemark Distance Calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`~kmlorm.models.placemark.Placemark` class provides methods for calculating
distances and bearings between geographic points.

.. automethod:: kmlorm.models.placemark.Placemark.distance_to

.. automethod:: kmlorm.models.placemark.Placemark.bearing_to

**Distance Calculation Implementation:**

These methods use the same **Haversine formula** as the QuerySet :meth:`~kmlorm.core.querysets.KMLQuerySet.near` method.
See :doc:`querysets` for detailed information about accuracy, limitations, and appropriate use cases.

**Key Features:**

* **Consistent Results**: Same algorithm as QuerySet geospatial methods
* **Flexible Input**: Accept either Placemark objects or coordinate tuples
* **Reliable Accuracy**: Within 0.5% for distances up to hundreds of kilometers
* **Great Circle Distance**: True geodesic distance accounting for Earth's curvature

**Distance Calculation Example:**

.. code-block:: python

   from kmlorm import Placemark
   from kmlorm.models.point import Point

   # Create two placemarks
   baltimore = Placemark(
       name="Baltimore, MD",
       point=Point(coordinates=(-76.6, 39.3))
   )

   washington = Placemark(
       name="Washington, DC",
       point=Point(coordinates=(-77.0, 38.9))
   )

   # Calculate distance between cities
   distance = baltimore.distance_to(washington)
   print(f"Distance: {distance:.1f} km")  # ≈ 56.3 km

   # Calculate using coordinate tuple
   distance_to_tuple = baltimore.distance_to((-77.0, 38.9))
   print(f"Same distance: {distance_to_tuple:.1f} km")

   # Calculate bearing (direction)
   bearing = baltimore.bearing_to(washington)
   print(f"Bearing: {bearing:.1f}°")  # ≈ 225° (southwest)

**Return Value Handling:**

Both methods return ``None`` when coordinates are unavailable:

.. code-block:: python

   # Placemark without coordinates
   no_coords = Placemark(name="Unknown Location")

   result = baltimore.distance_to(no_coords)
   if result is None:
       print("Cannot calculate distance - missing coordinates")

For complete details about distance calculation accuracy and limitations,
see :doc:`querysets` under "Distance Calculation Details".

Example Usage
-------------

.. code-block:: python

   from kmlorm import Placemark, Folder, Point

   # Create a placemark with coordinates
   store = Placemark(
       name="Capital Electric",
       address="123 Main St, Baltimore, MD",
       coordinates=(-76.5, 39.3)
   )

   # Create a folder to organize placemarks
   stores_folder = Folder(name="Electric Stores")
   stores_folder.placemarks.add(store)

   # Access coordinates
   print(f"Store location: {store.longitude}, {store.latitude}")

   # Calculate distance to another location
   distance = store.distance_to((-76.6, 39.3))  # Distance to Baltimore center
   if distance:
       print(f"Distance to Baltimore: {distance:.2f} km")

   # Validate the placemark
   if store.validate():
       print("Placemark is valid!")