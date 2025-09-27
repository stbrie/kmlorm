Coordinates and Geometry
========================

KML ORM provides robust coordinate handling through the Coordinate class and related utilities.

Coordinate Class
----------------

.. note::
   Coordinate objects are automatically validated upon creation and will raise
   :class:`kmlorm.core.exceptions.KMLValidationError` if invalid values are provided.

.. autoclass:: kmlorm.models.point.Coordinate
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Creating Coordinates
--------------------

From Tuple
~~~~~~~~~~

.. automethod:: kmlorm.models.point.Coordinate.from_tuple

From String
~~~~~~~~~~~

.. automethod:: kmlorm.models.point.Coordinate.from_string

From Any Format
~~~~~~~~~~~~~~~

.. automethod:: kmlorm.models.point.Coordinate.from_any

Properties
----------

.. autoattribute:: kmlorm.models.point.Coordinate.longitude

.. autoattribute:: kmlorm.models.point.Coordinate.latitude

.. autoattribute:: kmlorm.models.point.Coordinate.altitude

Validation
----------

.. automethod:: kmlorm.models.point.Coordinate.validate

Data Export
-----------

.. automethod:: kmlorm.models.point.Coordinate.to_dict

Usage Examples
--------------

Creating Coordinates
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm.models.point import Coordinate

   # From tuple
   coord1 = Coordinate.from_tuple((-76.5, 39.3, 100))

   # From string
   coord2 = Coordinate.from_string("-76.5,39.3,100")

   # Direct creation (altitude defaults to 0 if not provided)
   coord3 = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)

   # From various formats
   coord4 = Coordinate.from_any((-76.5, 39.3))
   coord5 = Coordinate.from_any("-76.5,39.3")
   coord6 = Coordinate.from_any([-76.5, 39.3, 0])

Accessing Properties
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm.models.point import Coordinate

   coord = Coordinate(longitude=-76.5, latitude=39.3, altitude=100)

   print(f"Longitude: {coord.longitude}")
   print(f"Latitude: {coord.latitude}")
   print(f"Altitude: {coord.altitude}")

Validation
~~~~~~~~~~

.. code-block:: python

   from kmlorm.models.point import Coordinate
   from kmlorm.core.exceptions import KMLValidationError

   # Valid coordinate
   valid_coord = Coordinate(longitude=-76.5, latitude=39.3)
   if valid_coord.validate():
       print("Coordinate is valid")

   # Invalid coordinate (will raise exception automatically on creation)
   try:
       invalid_coord = Coordinate(longitude=200, latitude=100)  # Raises on __post_init__
   except KMLValidationError as e:
       print(f"Invalid coordinate: {e}")

Integration with Placemark
--------------------------

Coordinates are automatically handled when working with Placemarks:

.. code-block:: python

   from kmlorm import Placemark
   from kmlorm.models.point import Coordinate

   # Set coordinates during creation
   placemark = Placemark(
       name="Test Location",
       coordinates=(-76.5, 39.3, 100.0)  # Automatically converted to Coordinate
   )

   # Access coordinate properties
   print(f"Location: {placemark.longitude}, {placemark.latitude}")

   # Get the full coordinate object
   coord = placemark.coordinates
   if coord:
       print(f"Full coordinates: {coord.longitude}, {coord.latitude}, {coord.altitude}")

Exporting Coordinate Data
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm.models.point import Coordinate
   from kmlorm import Placemark

   # Create a coordinate
   coord = Coordinate(longitude=-76.5294, latitude=39.2904, altitude=100.5)

   # Export to dictionary format
   coord_dict = coord.to_dict()
   print(coord_dict)
   # Output: {'longitude': -76.5294, 'latitude': 39.2904, 'altitude': 100.5}

   # Access individual values from dictionary
   longitude = coord_dict["longitude"]
   latitude = coord_dict["latitude"]
   altitude = coord_dict["altitude"]

   # Use with placemarks for data transfer
   placemark = Placemark(name="Distribution Center", coordinates=(-76.5294, 39.2904, 100.5))

   # Export placemark coordinate data
   if placemark.coordinates:
       coord_data = placemark.coordinates.to_dict()
       print(f"Coordinate data: {coord_data}")

Coordinate Validation Rules
---------------------------

The Coordinate class enforces standard geographic coordinate ranges:

* **Longitude**: Must be between -180.0 and 180.0 degrees
* **Latitude**: Must be between -90.0 and 90.0 degrees
* **Altitude**: Must be a finite numeric value (if provided)

Invalid coordinates will raise a :class:`~kmlorm.core.exceptions.KMLValidationError`.