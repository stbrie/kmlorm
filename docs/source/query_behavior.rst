Query Method Behavior Reference
================================

Summary
-------

.. warning::

   All query methods (``filter()``, ``exclude()``, ``get()``, ``exists()``, etc.) operate on
   **direct children only** by default, equivalent to calling ``.children()`` first.
   To search nested elements, you must explicitly call ``.all()`` before the query method.

Core Principle
--------------

.. code-block:: python

   # These are equivalent:
   kml.placemarks.filter(name="Example")           # Searches direct children only
   kml.placemarks.children().filter(name="Example") # Explicitly searches direct children only

   # To search ALL elements including nested:
   kml.placemarks.all().filter(name="Example")     # Searches ALL placemarks including nested

Truth Table for Query Methods
------------------------------

.. list-table:: Query Method Behavior
   :header-rows: 1
   :widths: 20 15 15 25 25

   * - Manager Type
     - Query Method
     - Default Scope
     - Equivalent To
     - To Search All Nested
   * - ``kml.placemarks``
     - ``.filter()``
     - Direct children only
     - ``.children().filter()``
     - ``.all().filter()``
   * - ``kml.placemarks``
     - ``.exclude()``
     - Direct children only
     - ``.children().exclude()``
     - ``.all().exclude()``
   * - ``kml.placemarks``
     - ``.get()``
     - Direct children only
     - ``.children().get()``
     - ``.all().get()``
   * - ``kml.placemarks``
     - ``.exists()``
     - Direct children only
     - ``.children().exists()``
     - ``.all().exists()``
   * - ``kml.placemarks``
     - ``.count()``
     - Direct children only
     - ``len(children())``
     - ``.all().count()``
   * - ``kml.placemarks``
     - ``.first()``
     - Direct children only
     - ``.children().first()``
     - ``.all().first()``
   * - ``kml.placemarks``
     - ``.last()``
     - Direct children only
     - ``.children().last()``
     - ``.all().last()``

Behavior by Element Type
-------------------------

KMLFile Root Managers
~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Root Manager Query Behavior
   :header-rows: 1
   :widths: 30 40 30

   * - Manager
     - Default Query Scope
     - Notes
   * - ``kml.placemarks.filter()``
     - Root-level placemarks only
     - Does NOT search placemarks inside folders
   * - ``kml.folders.filter()``
     - Root-level folders only
     - Does NOT search nested subfolders
   * - ``kml.points.filter()``
     - Root-level standalone Points only
     - Does NOT include Points from Placemarks or nested folders
   * - ``kml.paths.filter()``
     - Root-level standalone Paths only
     - Does NOT include Paths from Placemarks or nested folders
   * - ``kml.polygons.filter()``
     - Root-level standalone Polygons only
     - Does NOT include Polygons from Placemarks or nested folders

Folder Managers
~~~~~~~~~~~~~~~

.. list-table:: Folder Manager Query Behavior
   :header-rows: 1
   :widths: 30 40 30

   * - Manager
     - Default Query Scope
     - Notes
   * - ``folder.placemarks.filter()``
     - Direct child placemarks only
     - Does NOT search placemarks in subfolders
   * - ``folder.folders.filter()``
     - Direct subfolders only
     - Does NOT search deeper nested folders
   * - ``folder.points.filter()``
     - Direct child standalone Points only
     - Does NOT include Points from child Placemarks or subfolders
   * - ``folder.paths.filter()``
     - Direct child standalone Paths only
     - Does NOT include Paths from child Placemarks or subfolders
   * - ``folder.polygons.filter()``
     - Direct child standalone Polygons only
     - Does NOT include Polygons from child Placemarks or subfolders

Special Cases
~~~~~~~~~~~~~

.. list-table:: Special Case Behavior
   :header-rows: 1
   :widths: 40 60

   * - Context
     - Behavior
   * - ``multigeometry.points.filter()``
     - Filters Points within this MultiGeometry only
   * - ``multigeometry.paths.filter()``
     - Filters Paths within this MultiGeometry only
   * - ``multigeometry.polygons.filter()``
     - Filters Polygons within this MultiGeometry only

Real-World Examples
-------------------

Example 1: Finding a Placemark by Name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # WRONG - Only searches root level:
   placemark = kml.placemarks.get(name="Store #42")
   # Raises KMLElementNotFound if Store #42 is in a folder

   # CORRECT - Searches all placemarks:
   placemark = kml.placemarks.all().get(name="Store #42")
   # Finds Store #42 wherever it is

Example 2: Counting Elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Count only root-level placemarks:
   root_count = kml.placemarks.count()  # e.g., returns 5

   # Count ALL placemarks including nested:
   total_count = kml.placemarks.all().count()  # e.g., returns 150

Example 3: Filtering Visible Placemarks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Only root-level visible placemarks:
   visible_root = kml.placemarks.filter(visibility=True)

   # ALL visible placemarks including nested:
   all_visible = kml.placemarks.all().filter(visibility=True)

Example 4: Geometry Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get only standalone Points at root level:
   root_points = kml.points.filter(altitude__gt=100)

   # Get ALL Points including those from Placemarks and nested folders:
   all_high_points = kml.points.all().filter(altitude__gt=100)

Implementation Details
----------------------

The reason for this behavior is in the manager implementation:

.. code-block:: python

   def filter(self, **kwargs):
       return self.get_queryset().filter(**kwargs)
       # get_queryset() returns direct children only

   def get_queryset(self):
       return KMLQuerySet(self.elements)
       # self.elements contains direct children only

The ``.all()`` method explicitly collects nested elements:

.. code-block:: python

   def all(self):
       all_elements = list(self.elements)  # Start with direct children
       all_elements.extend(self._collect_nested_elements())  # Add nested
       return KMLQuerySet(all_elements)

Best Practices
--------------

1. **Always use** ``.all()`` **when searching entire KML documents**:

   .. code-block:: python

      # Searching for any placemark named "Target"
      results = kml.placemarks.all().filter(name__icontains="Target")

2. **Use direct query methods only when you specifically want root/direct children**:

   .. code-block:: python

      # When you explicitly want only root-level folders
      root_folders = kml.folders.filter(visibility=True)

3. **Be explicit about scope for clarity**:

   .. code-block:: python

      # Clear intent - searching only direct children
      direct_children = folder.placemarks.children().filter(visibility=True)

      # Clear intent - searching all nested elements
      all_nested = folder.placemarks.all().filter(visibility=True)

4. **Remember geometry managers have special behavior**:

   - ``kml.points.all()`` collects from standalone Points AND Points within Placemarks
   - ``kml.points.filter()`` only filters standalone Points at root level
   - Same applies for ``paths`` and ``polygons``

Common Pitfalls
---------------

1. **Assuming** ``filter()`` **searches nested elements** - It doesn't!
2. **Using** ``get()`` **without** ``.all()`` **for nested elements** - Will raise ``KMLElementNotFound``
3. **Counting with** ``.count()`` **instead of** ``.all().count()`` - Undercounts nested elements
4. **Forgetting that geometry managers need** ``.all()`` **to include Placemark geometries**

Summary Recommendation
----------------------

.. important::

   **When in doubt, use** ``.all()`` **before query methods.** Most real-world KML files
   organize elements in folders, so you'll almost always want:

   .. code-block:: python

      kml.placemarks.all().filter(...)  # Not just kml.placemarks.filter(...)
      folder.points.all().filter(...)   # Not just folder.points.filter(...)

   This ensures you're searching the entire element tree, not just the immediate children.