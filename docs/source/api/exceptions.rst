Exceptions
==========

KML ORM defines custom exceptions for handling various error conditions during KML parsing and querying operations.

.. automodule:: kmlorm.core.exceptions
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Exception Hierarchy
-------------------

All KML ORM exceptions inherit from :class:`~kmlorm.core.exceptions.KMLOrmException`.

.. code-block:: text

   KMLOrmException
   ├── KMLParseError
   ├── KMLValidationError
   ├── KMLElementNotFound
   ├── KMLMultipleElementsReturned
   ├── KMLInvalidCoordinates
   └── KMLQueryError

Base Exception
--------------

.. autoexception:: kmlorm.core.exceptions.KMLOrmException
    :no-index:
    :members:
    :undoc-members:

Parsing Exceptions
------------------

.. autoexception:: kmlorm.core.exceptions.KMLParseError

Validation Exceptions
---------------------

.. autoexception:: kmlorm.core.exceptions.KMLValidationError

.. autoexception:: kmlorm.core.exceptions.KMLInvalidCoordinates

Query Exceptions
----------------

.. autoexception:: kmlorm.core.exceptions.KMLElementNotFound

.. autoexception:: kmlorm.core.exceptions.KMLMultipleElementsReturned

.. autoexception:: kmlorm.core.exceptions.KMLQueryError

Usage Examples
--------------

Handling Parse Errors
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm import KMLFile
   from kmlorm.core.exceptions import KMLParseError

   try:
       kml = KMLFile.from_file('invalid.kml')
   except KMLParseError as e:
       print(f"Failed to parse KML: {e}")

Handling Query Errors
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm import KMLFile
   from kmlorm.core.exceptions import KMLElementNotFound, KMLMultipleElementsReturned

   kml = KMLFile.from_file('stores.kml')

   try:
       # This will raise KMLElementNotFound if no match
       store = kml.placemarks.get(name='Nonexistent Store')
   except KMLElementNotFound:
       print("Store not found")

   try:
       # This will raise KMLMultipleElementsReturned if multiple matches
       store = kml.placemarks.get(name__icontains='Capital')
   except KMLMultipleElementsReturned:
       print("Multiple stores found, be more specific")

Handling Validation Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from kmlorm.models.point import Coordinate
   from kmlorm.core.exceptions import KMLValidationError

   try:
       # Invalid coordinates (validation happens automatically on creation)
       coord = Coordinate(longitude=200, latitude=100)  # Out of valid range
   except KMLValidationError as e:
       print(f"Validation failed: {e}")
       print(f"Field: {e.field}")
       print(f"Value: {e.value}")

Best Practices
--------------

1. **Catch Specific Exceptions**: Always catch the most specific exception type first.

2. **Provide User-Friendly Messages**: Convert technical exceptions into user-friendly error messages.

3. **Log Errors**: Log exceptions for debugging while showing clean messages to users.

.. code-block:: python

   import logging
   from kmlorm import KMLFile
   from kmlorm.core.exceptions import KMLParseError, KMLOrmException

   logger = logging.getLogger(__name__)

   def load_kml_safely(file_path):
       try:
           return KMLFile.from_file(file_path)
       except KMLParseError as e:
           logger.error(f"Failed to parse KML file {file_path}: {e}")
           if hasattr(e, 'source') and e.source:
               logger.error(f"Error source: {e.source}")
           raise ValueError(f"Invalid KML file: {file_path}")
       except KMLOrmException as e:
           logger.error(f"KML ORM error with {file_path}: {e}")
           raise
       except Exception as e:
           logger.error(f"Unexpected error loading {file_path}: {e}")
           raise RuntimeError(f"Failed to load KML file: {file_path}")

Error Codes and Context
-----------------------

Many exceptions include additional context about the error:

* **Field name**: Which field caused the validation error
* **Value**: The invalid value that caused the error
* **Element context**: Information about which KML element failed

.. code-block:: python

   from kmlorm.models.point import Coordinate
   from kmlorm.core.exceptions import KMLValidationError

   try:
       # Example that shows error context
       coord = Coordinate(longitude=200, latitude=100)
   except KMLValidationError as e:
       print(f"Field: {e.field if hasattr(e, 'field') else 'N/A'}")
       print(f"Value: {e.value if hasattr(e, 'value') else 'N/A'}")
       print(f"Message: {str(e)}")

   # Exception attributes available for KMLElementNotFound:
   try:
       kml.placemarks.get(name='Missing')
   except KMLElementNotFound as e:
       print(f"Element type: {e.element_type}")
       print(f"Query: {e.query_kwargs}")

   # Exception attributes available for KMLMultipleElementsReturned:
   try:
       kml.placemarks.get(name__icontains='Store')
   except KMLMultipleElementsReturned as e:
       print(f"Element type: {e.element_type}")
       print(f"Count found: {e.count}")
       print(f"Query: {e.query_kwargs}")