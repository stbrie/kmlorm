Spatial Calculations
====================

.. module:: kmlorm.spatial

The spatial module provides comprehensive geospatial calculations for KML elements,
including distance calculations, bearing computations, and coordinate operations.

Overview
--------

The spatial module implements a Protocol-based design that allows any object with
coordinates to participate in spatial calculations. This provides clean separation
of concerns and extensibility.

Key Features
~~~~~~~~~~~~

* **Multiple distance calculation strategies** - Haversine (default), Vincenty (high precision), and Euclidean (fast approximation)
* **Support for multiple distance units** - Kilometers, meters, miles, nautical miles, feet, and yards
* **Protocol-based design** - Any object implementing ``HasCoordinates`` can use spatial operations
* **LRU caching** - Automatic caching of repeated calculations for performance
* **Bulk operations** - Efficient batch distance calculations

Quick Example
~~~~~~~~~~~~~

.. code-block:: python

    from kmlorm.models import Placemark
    from kmlorm.spatial import DistanceUnit

    # Create two placemarks
    nyc = Placemark(name="NYC", coordinates=(-74.006, 40.7128))
    london = Placemark(name="London", coordinates=(-0.1276, 51.5074))

    # Calculate distance (default: kilometers)
    distance_km = nyc.distance_to(london)
    print(f"Distance: {distance_km:.1f} km")  # Distance: 5570.2 km

    # Calculate in different units
    distance_miles = nyc.distance_to(london, unit=DistanceUnit.MILES)
    print(f"Distance: {distance_miles:.1f} miles")  # Distance: 3461.0 miles

    # Calculate bearing
    bearing = nyc.bearing_to(london)
    print(f"Bearing: {bearing:.1f}°")  # Bearing: 51.2°

    # Find midpoint
    midpoint = nyc.midpoint_to(london)
    print(f"Midpoint: ({midpoint.longitude:.2f}, {midpoint.latitude:.2f})")
    # Midpoint: (-41.29, 52.37)

Core Components
---------------

HasCoordinates Protocol
~~~~~~~~~~~~~~~~~~~~~~~

The ``HasCoordinates`` protocol defines the interface for objects that can provide coordinates:

.. code-block:: python

    from typing import Protocol, Optional
    from kmlorm.models.point import Coordinate

    class HasCoordinates(Protocol):
        """Protocol for objects that can provide coordinates."""

        def get_coordinates(self) -> Optional[Coordinate]:
            """Return the coordinate representation of this object."""
            ...

Any object implementing this protocol can participate in spatial calculations. The following
classes implement ``HasCoordinates``:

* :class:`~kmlorm.models.point.Coordinate`
* :class:`~kmlorm.models.point.Point`
* :class:`~kmlorm.models.placemark.Placemark`

Distance Units
~~~~~~~~~~~~~~

.. class:: DistanceUnit(Enum)

    Enumeration of available distance units with conversion factors from kilometers.

    .. attribute:: KILOMETERS

        Kilometers (base unit, factor = 1.0)

    .. attribute:: METERS

        Meters (factor = 1000.0)

    .. attribute:: MILES

        Statute miles (factor = 0.621371)

    .. attribute:: NAUTICAL_MILES

        Nautical miles (factor = 0.539957)

    .. attribute:: FEET

        Feet (factor = 3280.84)

    .. attribute:: YARDS

        Yards (factor = 1093.61)

    Example usage:

    .. code-block:: python

        from kmlorm.spatial import DistanceUnit

        # Calculate distance in different units
        distance_km = point1.distance_to(point2)
        distance_m = point1.distance_to(point2, unit=DistanceUnit.METERS)
        distance_mi = point1.distance_to(point2, unit=DistanceUnit.MILES)

Spatial Calculations
--------------------

.. class:: SpatialCalculations

    Core class providing static methods for spatial calculations between geographic coordinates.
    All calculations use the WGS84 ellipsoid model and assume coordinates in decimal degrees.

    .. method:: distance_between(from_obj: HasCoordinates, to_obj: HasCoordinates, unit: DistanceUnit = DistanceUnit.KILOMETERS) -> Optional[float]
        :classmethod:

        Calculate the distance between two objects with coordinates.

        :param from_obj: Source object with coordinates
        :param to_obj: Destination object with coordinates
        :param unit: Unit for distance measurement (default: kilometers)
        :return: Distance in specified units, or None if coordinates unavailable

        Example:

        .. code-block:: python

            from kmlorm.spatial.calculations import SpatialCalculations
            from kmlorm.models.point import Coordinate

            coord1 = Coordinate(longitude=-74.006, latitude=40.7128)
            coord2 = Coordinate(longitude=-0.1276, latitude=51.5074)

            distance = SpatialCalculations.distance_between(coord1, coord2)
            print(f"Distance: {distance:.1f} km")

    .. method:: bearing_between(from_obj: HasCoordinates, to_obj: HasCoordinates) -> Optional[float]
        :classmethod:

        Calculate the initial bearing (azimuth) between two objects.

        :param from_obj: Source object with coordinates
        :param to_obj: Destination object with coordinates
        :return: Initial bearing in degrees (0-360), where 0° = North, 90° = East, etc.

        Example:

        .. code-block:: python

            bearing = SpatialCalculations.bearing_between(coord1, coord2)
            print(f"Bearing: {bearing:.1f}°")

    .. method:: midpoint(obj1: HasCoordinates, obj2: HasCoordinates) -> Optional[Coordinate]
        :classmethod:

        Find the geographic midpoint between two objects.

        :param obj1: First object with coordinates
        :param obj2: Second object with coordinates
        :return: Coordinate representing the midpoint, or None if calculation fails

    .. method:: distances_to_many(from_obj: HasCoordinates, to_objects: List[HasCoordinates], unit: DistanceUnit = DistanceUnit.KILOMETERS) -> List[Optional[float]]
        :classmethod:

        Calculate distances from one object to many others efficiently.

        :param from_obj: Source object with coordinates
        :param to_objects: List of destination objects
        :param unit: Unit for distance measurements
        :return: List of distances (None for objects without coordinates)

        Example:

        .. code-block:: python

            center = Coordinate(longitude=0, latitude=0)
            targets = [coord1, coord2, coord3, coord4]

            distances = SpatialCalculations.distances_to_many(center, targets)
            for i, dist in enumerate(distances):
                if dist is not None:
                    print(f"Distance to target {i}: {dist:.1f} km")

Distance Calculation Strategies
-------------------------------

The spatial module provides multiple strategies for distance calculation, each with
different trade-offs between accuracy and performance.

.. class:: HaversineStrategy

    Great circle distance using the Haversine formula. This is the default strategy,
    providing a good balance of speed and accuracy.

    * **Accuracy**: ±0.5% for most distances
    * **Performance**: Fast (O(1) with simple trigonometric operations)
    * **Best for**: General purpose distance calculations

.. class:: VincentyStrategy

    Vincenty's formulae for accurate distance on an oblate spheroid (WGS84 ellipsoid).
    More accurate than Haversine but significantly slower.

    * **Accuracy**: ±0.5mm for distances up to ~20,000 km
    * **Performance**: Slower (iterative algorithm)
    * **Best for**: High-precision applications requiring maximum accuracy

.. class:: EuclideanApproximation

    Fast Euclidean approximation using equirectangular projection. Very fast but
    only accurate for small distances.

    * **Accuracy**: Good for distances <100km, decreases with distance and latitude
    * **Performance**: Very fast (O(1) with minimal operations)
    * **Best for**: Quick approximations when speed is critical and distances are small

.. class:: AdaptiveStrategy

    Adaptive strategy that automatically selects the best algorithm based on distance
    and requirements. Uses Euclidean for very small distances (<50km), Haversine for
    medium distances, and optionally Vincenty for long distances when high accuracy
    is requested.

Usage Examples
--------------

Basic Distance Calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kmlorm.models import Placemark, Point
    from kmlorm.models.point import Coordinate

    # Distance between Coordinate objects
    coord1 = Coordinate(longitude=-74.006, latitude=40.7128)  # NYC
    coord2 = Coordinate(longitude=-0.1276, latitude=51.5074)   # London
    distance = coord1.distance_to(coord2)

    # Distance between Points
    point1 = Point(coordinates=(-74.006, 40.7128))
    point2 = Point(coordinates=(-0.1276, 51.5074))
    distance = point1.distance_to(point2)

    # Distance between Placemarks
    place1 = Placemark(name="NYC", coordinates=(-74.006, 40.7128))
    place2 = Placemark(name="London", coordinates=(-0.1276, 51.5074))
    distance = place1.distance_to(place2)

    # Mixed types - all work together
    distance = coord1.distance_to(place2)
    distance = point1.distance_to(coord2)

Working with Different Units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kmlorm.spatial import DistanceUnit

    # Default is kilometers
    km = place1.distance_to(place2)

    # Other units
    meters = place1.distance_to(place2, unit=DistanceUnit.METERS)
    miles = place1.distance_to(place2, unit=DistanceUnit.MILES)
    nautical = place1.distance_to(place2, unit=DistanceUnit.NAUTICAL_MILES)
    feet = place1.distance_to(place2, unit=DistanceUnit.FEET)
    yards = place1.distance_to(place2, unit=DistanceUnit.YARDS)

    print(f"Distance: {km:.1f} km = {miles:.1f} mi = {nautical:.1f} nm")

Bearing and Navigation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Calculate bearing (initial heading)
    bearing = place1.bearing_to(place2)
    print(f"Initial bearing from NYC to London: {bearing:.1f}°")

    # Bearing interpretation
    if bearing < 22.5 or bearing >= 337.5:
        direction = "North"
    elif bearing < 67.5:
        direction = "Northeast"
    elif bearing < 112.5:
        direction = "East"
    elif bearing < 157.5:
        direction = "Southeast"
    elif bearing < 202.5:
        direction = "South"
    elif bearing < 247.5:
        direction = "Southwest"
    elif bearing < 292.5:
        direction = "West"
    else:
        direction = "Northwest"

    print(f"Head {direction} ({bearing:.1f}°)")

Finding Midpoints
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Find geographic midpoint
    midpoint = place1.midpoint_to(place2)

    print(f"Midpoint between NYC and London:")
    print(f"  Longitude: {midpoint.longitude:.4f}")
    print(f"  Latitude: {midpoint.latitude:.4f}")

    # Create a new placemark at the midpoint
    midpoint_place = Placemark(
        name="Atlantic Midpoint",
        coordinates=(midpoint.longitude, midpoint.latitude)
    )

Bulk Distance Operations
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kmlorm.spatial.calculations import SpatialCalculations

    # Efficient bulk distance calculations
    center = Coordinate(longitude=0, latitude=0)

    # Many target locations
    targets = [
        Placemark(name="North", coordinates=(0, 10)),
        Placemark(name="South", coordinates=(0, -10)),
        Placemark(name="East", coordinates=(10, 0)),
        Placemark(name="West", coordinates=(-10, 0)),
        Placemark(name="Northeast", coordinates=(10, 10)),
    ]

    # Calculate all distances at once
    distances = SpatialCalculations.distances_to_many(center, targets)

    for target, distance in zip(targets, distances):
        if distance is not None:
            print(f"{target.name}: {distance:.1f} km")

Integration with QuerySets
~~~~~~~~~~~~~~~~~~~~~~~~~~

The QuerySet's ``near()`` method uses the spatial calculations internally:

.. code-block:: python

    from kmlorm.parsers import KMLFile

    # Load KML file
    kml = KMLFile.from_file("stores.kml")

    # Find all stores within 50km of a location
    center_lat, center_lon = 40.7128, -74.006  # NYC

    nearby_stores = kml.placemarks.near(
        longitude=center_lon,
        latitude=center_lat,
        radius_km=50
    )

    for store in nearby_stores:
        # Each store has distance methods available
        distance = store.distance_to((center_lon, center_lat))
        bearing = store.bearing_to((center_lon, center_lat))
        print(f"{store.name}: {distance:.1f} km at {bearing:.0f}°")

Edge Cases and Limitations
--------------------------

Date Line Crossing
~~~~~~~~~~~~~~~~~~

The Haversine and Vincenty strategies correctly handle date line crossing:

.. code-block:: python

    # Points on opposite sides of the International Date Line
    west_of_date_line = Coordinate(longitude=179.5, latitude=0)
    east_of_date_line = Coordinate(longitude=-179.5, latitude=0)

    # Correctly calculates ~111 km, not ~39,000 km
    distance = west_of_date_line.distance_to(east_of_date_line)

Polar Regions
~~~~~~~~~~~~~

All strategies handle polar calculations correctly:

.. code-block:: python

    north_pole = Coordinate(longitude=0, latitude=90)
    south_pole = Coordinate(longitude=0, latitude=-90)

    # Pole to pole distance
    distance = north_pole.distance_to(south_pole)  # ~20,004 km

Coordinate Validation
~~~~~~~~~~~~~~~~~~~~~

Invalid coordinates are handled gracefully:

.. code-block:: python

    from kmlorm.models import Placemark

    # Placemark without coordinates
    place_no_coords = Placemark(name="Unknown Location")

    # Returns None for objects without valid coordinates
    distance = place_no_coords.distance_to(north_pole)  # None

Performance Considerations
--------------------------

Caching
~~~~~~~

The spatial module uses LRU caching for repeated calculations:

.. code-block:: python

    # These repeated calculations are cached automatically
    for i in range(1000):
        distance = place1.distance_to(place2)  # Cached after first calculation

Strategy Selection
~~~~~~~~~~~~~~~~~~

Choose the appropriate strategy based on your needs:

.. code-block:: python

    from kmlorm.spatial.strategies import HaversineStrategy, VincentyStrategy

    # For general use (default)
    strategy = HaversineStrategy()

    # For high precision requirements
    strategy = VincentyStrategy()

    # Use with SpatialCalculations
    from kmlorm.spatial.calculations import SpatialCalculations

    # The strategy can be selected internally based on requirements

Typical Use Cases
~~~~~~~~~~~~~~~~~

For typical KML files with hundreds of placemarks, the default Haversine strategy
provides excellent performance and accuracy. The spatial calculations are optimized
for this common use case.

API Reference
-------------

.. automodule:: kmlorm.spatial
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. automodule:: kmlorm.spatial.calculations
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. automodule:: kmlorm.spatial.strategies
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: kmlorm.spatial.constants
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: kmlorm.spatial.exceptions
   :members:
   :undoc-members:
   :show-inheritance: