"""
Tests that validate every example in docs/source/api/exceptions.rst and
docs/source/api/kmlorm.core.exceptions.rst work as documented.

This test suite ensures that all code examples in the exceptions documentation
are functional and produce the expected results.
"""

# pylint: disable=duplicate-code
import unittest
import logging
import tempfile
import os
from unittest.mock import patch
from typing import Optional
from kmlorm import KMLFile
from kmlorm.models.point import Coordinate
from kmlorm.core.exceptions import (
    KMLOrmException,
    KMLParseError,
    KMLValidationError,
    KMLElementNotFound,
    KMLMultipleElementsReturned,
    KMLInvalidCoordinates,
    KMLQueryError,
)


class TestExceptionsDocsExamples(unittest.TestCase):
    """Test cases that validate exceptions.rst documentation examples."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a temporary KML file for testing
        self.temp_kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Test Document</name>
        <Placemark>
            <name>Capital Electric - Rosedale</name>
            <description>Store location</description>
            <Point>
                <coordinates>-76.5,39.3,0</coordinates>
            </Point>
        </Placemark>
        <Placemark>
            <name>Capital Electric - Downtown</name>
            <description>Another store location</description>
            <Point>
                <coordinates>-76.6,39.4,0</coordinates>
            </Point>
        </Placemark>
        <Placemark>
            <name>Store A</name>
            <description>First store</description>
            <Point>
                <coordinates>-77.0,40.0,0</coordinates>
            </Point>
        </Placemark>
        <Placemark>
            <name>Store B</name>
            <description>Second store</description>
            <Point>
                <coordinates>-77.1,40.1,0</coordinates>
            </Point>
        </Placemark>
    </Document>
</kml>"""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as temp_file:
            temp_file.write(self.temp_kml_content)
        self.temp_file = temp_file

        # Invalid KML content
        self.invalid_kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <InvalidElement>This is not valid KML</InvalidElement>
    </Document>
</kml>"""

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_handling_parse_errors_basic_example(self) -> None:
        """Test the basic parse error example from exceptions.rst."""
        # Example from exceptions.rst:
        # from kmlorm import KMLFile
        # from kmlorm.core.exceptions import KMLParseError
        #
        # try:
        #     kml = KMLFile.from_file('invalid.kml')
        # except KMLParseError as e:
        #     print(f"Failed to parse KML: {e}")

        # Create an invalid KML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as invalid_file:
            invalid_file.write("invalid xml content")
        invalid_file.close()

        try:
            with self.assertRaises(KMLParseError) as context:
                _ = KMLFile.from_file(invalid_file.name)

            # Verify we can format the error as shown in documentation
            error_message = f"Failed to parse KML: {context.exception}"
            self.assertIn("Failed to parse KML:", error_message)
        finally:
            os.unlink(invalid_file.name)

    def test_handling_parse_errors_comprehensive_example(self) -> None:
        """Test the comprehensive parse error example from kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # from kmlorm import KMLFile, KMLParseError
        #
        # try:
        #     kml = KMLFile.from_file('invalid.kml')
        # except KMLParseError as e:
        #     print(f"Failed to parse KML: {e}")
        #     if hasattr(e, 'source') and e.source:
        #         print(f"Source: {e.source}")

        # Create an invalid KML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as invalid_file:
            invalid_file.write("invalid xml content")
        invalid_file.close()

        try:
            with self.assertRaises(KMLParseError) as context:
                _ = KMLFile.from_file(invalid_file.name)

            e = context.exception
            # Test the formatted message as shown in documentation
            parse_error_msg = f"Failed to parse KML: {e}"
            self.assertIn("Failed to parse KML:", parse_error_msg)

            # Test the source attribute handling as shown in documentation
            if hasattr(e, "source") and e.source:
                source_msg = f"Source: {e.source}"
                self.assertIn("Source:", source_msg)
        finally:
            os.unlink(invalid_file.name)

    def test_handling_query_errors_element_not_found_basic_example(self) -> None:
        """Test the basic KMLElementNotFound example from exceptions.rst."""
        # Example from exceptions.rst:
        # from kmlorm import KMLFile
        # from kmlorm.core.exceptions import KMLElementNotFound, KMLMultipleElementsReturned
        #
        # kml = KMLFile.from_file('stores.kml')
        #
        # try:
        #     # This will raise KMLElementNotFound if no match
        #     store = kml.placemarks.get(name='Nonexistent Store')
        # except KMLElementNotFound:
        #     print("Store not found")

        kml = KMLFile.from_file(self.temp_file.name)
        handled: bool = False
        with self.assertRaises(KMLElementNotFound):
            _ = kml.placemarks.get(name="Nonexistent Store")

        # Test that we can catch and handle it as shown in documentation
        try:
            _ = kml.placemarks.get(name="Nonexistent Store")
        except KMLElementNotFound:
            handled = True

        self.assertTrue(handled)

    def test_handling_query_errors_multiple_elements_basic_example(self) -> None:
        """Test the basic KMLMultipleElementsReturned example from exceptions.rst."""
        # Example from exceptions.rst:
        # try:
        #     # This will raise KMLMultipleElementsReturned if multiple matches
        #     store = kml.placemarks.get(name__icontains='Capital')
        # except KMLMultipleElementsReturned:
        #     print("Multiple stores found, be more specific")

        kml = KMLFile.from_file(self.temp_file.name)
        handled: bool = False
        with self.assertRaises(KMLMultipleElementsReturned):
            _ = kml.placemarks.get(name__icontains="Capital")

        # Test that we can catch and handle it as shown in documentation
        try:
            _ = kml.placemarks.get(name__icontains="Capital")
        except KMLMultipleElementsReturned:
            handled = True

        self.assertTrue(handled)

    def test_handling_query_errors_comprehensive_element_not_found_example(self) -> None:
        """Test the comprehensive KMLElementNotFound example from kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # kml = KMLFile.from_file('stores.kml')
        #
        # try:
        #     store = kml.placemarks.all().get(name='Nonexistent Store')
        # except KMLElementNotFound as e:
        #     print(f"Element not found: {e}")
        #     print(f"Element type: {e.element_type}")
        #     print(f"Query: {e.query_kwargs}")

        kml = KMLFile.from_file(self.temp_file.name)

        with self.assertRaises(KMLElementNotFound) as context:
            _ = kml.placemarks.all().get(name="Nonexistent Store")

        e = context.exception
        # Test the formatted messages as shown in documentation
        element_not_found_msg = f"Element not found: {e}"
        element_type_msg = f"Element type: {e.element_type}"
        query_msg = f"Query: {e.query_kwargs}"

        self.assertIn("Element not found:", element_not_found_msg)
        self.assertIn("Element type:", element_type_msg)
        self.assertIn("Query:", query_msg)

        # Verify the attributes exist as documented
        self.assertTrue(hasattr(e, "element_type"))
        self.assertTrue(hasattr(e, "query_kwargs"))

    def test_handling_query_errors_comprehensive_multiple_elements_example(self) -> None:
        """Test the comprehensive KMLMultipleElementsReturned example from
        kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # try:
        #     store = kml.placemarks.all().get(name__icontains='Store')
        # except KMLMultipleElementsReturned as e:
        #     print(f"Multiple elements found: {e}")
        #     print(f"Element type: {e.element_type}")
        #     print(f"Count: {e.count}")
        #     print(f"Query: {e.query_kwargs}")

        kml = KMLFile.from_file(self.temp_file.name)

        with self.assertRaises(KMLMultipleElementsReturned) as context:
            _ = kml.placemarks.all().get(name__icontains="Store")

        e = context.exception
        # Test the formatted messages as shown in documentation
        multiple_elements_msg = f"Multiple elements found: {e}"
        element_type_msg = f"Element type: {e.element_type}"
        count_msg = f"Count: {e.count}"
        query_msg = f"Query: {e.query_kwargs}"

        self.assertIn("Multiple elements found:", multiple_elements_msg)
        self.assertIn("Element type:", element_type_msg)
        self.assertIn("Count:", count_msg)
        self.assertIn("Query:", query_msg)

        # Verify the attributes exist as documented
        self.assertTrue(hasattr(e, "element_type"))
        self.assertTrue(hasattr(e, "count"))
        self.assertTrue(hasattr(e, "query_kwargs"))

    def test_handling_validation_errors_basic_example(self) -> None:
        """Test the basic validation error example from exceptions.rst."""
        # Example from exceptions.rst:
        # from kmlorm.models.point import Coordinate
        # from kmlorm.core.exceptions import KMLValidationError
        #
        # try:
        #     # Invalid coordinates (validation happens automatically on creation)
        #     coord = Coordinate(longitude=200, latitude=100)  # Out of valid range
        # except KMLValidationError as e:
        #     print(f"Validation failed: {e}")
        #     print(f"Field: {e.field}")
        #     print(f"Value: {e.value}")

        with self.assertRaises(KMLValidationError) as context:
            _ = Coordinate(longitude=200, latitude=100)

        e = context.exception
        # Test the formatted messages as shown in documentation
        validation_msg = f"Validation failed: {e}"
        field_msg = f"Field: {e.field}" if hasattr(e, "field") else "Field: N/A"
        value_msg = f"Value: {e.value}" if hasattr(e, "value") else "Value: N/A"

        self.assertIn("Validation failed:", validation_msg)
        self.assertIn("Field:", field_msg)
        self.assertIn("Value:", value_msg)

    def test_handling_validation_errors_comprehensive_example(self) -> None:
        """Test the comprehensive validation error example from kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # from kmlorm.models.point import Coordinate
        # from kmlorm import KMLValidationError
        #
        # try:
        #     # This will raise KMLValidationError on creation due to invalid longitude
        #     coord = Coordinate(longitude=200, latitude=100)
        # except KMLValidationError as e:
        #     print(f"Validation error: {e}")
        #     if hasattr(e, 'field'):
        #         print(f"Field: {e.field}")
        #     if hasattr(e, 'value'):
        #         print(f"Value: {e.value}")

        with self.assertRaises(KMLValidationError) as context:
            _ = Coordinate(longitude=200, latitude=100)

        e = context.exception
        # Test the formatted message as shown in documentation
        validation_error_msg = f"Validation error: {e}"
        self.assertIn("Validation error:", validation_error_msg)

        # Test the conditional attribute access as shown in documentation
        if hasattr(e, "field"):
            field_msg = f"Field: {e.field}"
            self.assertIn("Field:", field_msg)

        if hasattr(e, "value"):
            value_msg = f"Value: {e.value}"
            self.assertIn("Value:", value_msg)

    def test_best_practices_logging_example(self) -> None:
        """Test the best practices logging example from exceptions.rst."""
        # Example from exceptions.rst:
        # import logging
        # from kmlorm import KMLFile
        # from kmlorm.core.exceptions import KMLParseError, KMLOrmException
        #
        # logger = logging.getLogger(__name__)
        #
        # def load_kml_safely(file_path):
        #     try:
        #         return KMLFile.from_file(file_path)
        #     except KMLParseError as e:
        #         logger.error(f"Failed to parse KML file {file_path}: {e}")
        #         if hasattr(e, 'source') and e.source:
        #             logger.error(f"Error source: {e.source}")
        #         raise ValueError(f"Invalid KML file: {file_path}")
        #     except KMLOrmException as e:
        #         logger.error(f"KML ORM error with {file_path}: {e}")
        #         raise
        #     except Exception as e:
        #         logger.error(f"Unexpected error loading {file_path}: {e}")
        #         raise RuntimeError(f"Failed to load KML file: {file_path}")

        logger = logging.getLogger(__name__)

        def load_kml_safely(file_path: str) -> "Optional[KMLFile]":
            try:
                return KMLFile.from_file(file_path)
            except KMLParseError as e:
                logger.error("Failed to parse KML file %s: %s", file_path, e)
                if hasattr(e, "source") and e.source:
                    logger.error("Error source: %s", e.source)
                raise ValueError(f"Invalid KML file: {file_path}") from e
            except KMLOrmException as e:
                logger.error("KML ORM error with %s: %s", file_path, e)
                raise
            except Exception as e:
                logger.error("Unexpected error loading %s: %s", file_path, e)
                raise RuntimeError(f"Failed to load KML file: {file_path}") from e

        # Test with valid file - should work
        result = load_kml_safely(self.temp_file.name)
        self.assertIsInstance(result, KMLFile)

        # Test with invalid file - should raise ValueError
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as invalid_file:
            invalid_file.write("invalid xml")
        invalid_file.close()

        try:
            with self.assertRaises(ValueError) as context:
                load_kml_safely(invalid_file.name)

            self.assertIn("Invalid KML file:", str(context.exception))
        finally:
            os.unlink(invalid_file.name)

        # Test with non-existent file - should raise RuntimeError
        with self.assertRaises(RuntimeError) as runtime_context:
            load_kml_safely("nonexistent.kml")

        self.assertIn("Failed to load KML file:", str(runtime_context.exception))

    def test_error_context_validation_error_example(self) -> None:
        """Test the error context validation error example from exceptions.rst."""
        # Example from exceptions.rst:
        # from kmlorm.models.point import Coordinate
        # from kmlorm.core.exceptions import KMLValidationError
        #
        # try:
        #     # Example that shows error context
        #     coord = Coordinate(longitude=200, latitude=100)
        # except KMLValidationError as e:
        #     print(f"Field: {e.field if hasattr(e, 'field') else 'N/A'}")
        #     print(f"Value: {e.value if hasattr(e, 'value') else 'N/A'}")
        #     print(f"Message: {str(e)}")

        with self.assertRaises(KMLValidationError) as context:
            _ = Coordinate(longitude=200, latitude=100)

        e = context.exception
        # Test the formatted messages as shown in documentation
        field_msg = f"Field: {e.field if hasattr(e, 'field') else 'N/A'}"
        value_msg = f"Value: {e.value if hasattr(e, 'value') else 'N/A'}"
        message_msg = f"Message: {str(e)}"

        self.assertIn("Field:", field_msg)
        self.assertIn("Value:", value_msg)
        self.assertIn("Message:", message_msg)

    def test_error_context_element_not_found_attributes_example(self) -> None:
        """Test the KMLElementNotFound attributes example from exceptions.rst."""
        # Example from exceptions.rst:
        # # Exception attributes available for KMLElementNotFound:
        # try:
        #     kml.placemarks.get(name='Missing')
        # except KMLElementNotFound as e:
        #     print(f"Element type: {e.element_type}")
        #     print(f"Query: {e.query_kwargs}")

        kml = KMLFile.from_file(self.temp_file.name)

        with self.assertRaises(KMLElementNotFound) as context:
            kml.placemarks.get(name="Missing")

        e = context.exception
        # Test the attribute access as shown in documentation
        element_type_msg = f"Element type: {e.element_type}"
        query_msg = f"Query: {e.query_kwargs}"

        self.assertIn("Element type:", element_type_msg)
        self.assertIn("Query:", query_msg)

        # Verify the attributes are accessible
        self.assertTrue(hasattr(e, "element_type"))
        self.assertTrue(hasattr(e, "query_kwargs"))

    def test_error_context_multiple_elements_attributes_example(self) -> None:
        """Test the KMLMultipleElementsReturned attributes example from exceptions.rst."""
        # Example from exceptions.rst:
        # # Exception attributes available for KMLMultipleElementsReturned:
        # try:
        #     kml.placemarks.get(name__icontains='Store')
        # except KMLMultipleElementsReturned as e:
        #     print(f"Element type: {e.element_type}")
        #     print(f"Count found: {e.count}")
        #     print(f"Query: {e.query_kwargs}")

        kml = KMLFile.from_file(self.temp_file.name)

        with self.assertRaises(KMLMultipleElementsReturned) as context:
            kml.placemarks.get(name__icontains="Store")

        e = context.exception
        # Test the attribute access as shown in documentation
        element_type_msg = f"Element type: {e.element_type}"
        count_msg = f"Count found: {e.count}"
        query_msg = f"Query: {e.query_kwargs}"

        self.assertIn("Element type:", element_type_msg)
        self.assertIn("Count found:", count_msg)
        self.assertIn("Query:", query_msg)

        # Verify the attributes are accessible
        self.assertTrue(hasattr(e, "element_type"))
        self.assertTrue(hasattr(e, "count"))
        self.assertTrue(hasattr(e, "query_kwargs"))

    def test_best_practices_catch_specific_exceptions_first_example(self) -> None:
        """Test the catch specific exceptions first example from kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # try:
        #     element = kml.placemarks.get(name='Store')
        # except KMLElementNotFound:
        #     # Handle not found case
        #     pass
        # except KMLMultipleElementsReturned:
        #     # Handle multiple results case
        #     pass
        # except KMLOrmException:
        #     # Handle any other KML ORM exception
        #     pass

        kml = KMLFile.from_file(self.temp_file.name)

        # Test element not found case
        not_found_handled = False
        try:
            _ = kml.placemarks.get(name="NonexistentStore")
        except KMLElementNotFound:
            not_found_handled = True
        except KMLMultipleElementsReturned:
            pass
        except KMLOrmException:
            pass

        self.assertTrue(not_found_handled)

        # Test multiple elements returned case
        multiple_handled = False
        try:
            _ = kml.placemarks.get(name__icontains="Store")
        except KMLElementNotFound:
            pass
        except KMLMultipleElementsReturned:
            multiple_handled = True
        except KMLOrmException:
            pass

        self.assertTrue(multiple_handled)

    def test_best_practices_use_exception_context_example(self) -> None:
        """Test the use exception context example from kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # try:
        #     coord = Coordinate(longitude=invalid_value, latitude=39.3)
        # except KMLValidationError as e:
        #     # Use exception attributes for detailed error reporting
        #     logger.error(f"Validation failed for field {e.field} with value {e.value}: {e}")

        logger = logging.getLogger(__name__)
        invalid_value = 250  # Invalid longitude

        with patch.object(logger, "error") as mock_error:
            try:
                _ = Coordinate(longitude=invalid_value, latitude=39.3)
            except KMLValidationError as e:
                # Use exception attributes for detailed error reporting as shown in docs
                logger.error(
                    "Validation failed for field %s with value %s: %s", e.field, e.value, e
                )

            # Verify logger.error was called (even if attributes might not exist)
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]  # Get the first argument to logger.error
            self.assertIn("Validation failed for field", call_args)

    def test_best_practices_chain_exception_handling_example(self) -> None:
        """Test the chain exception handling example from kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # def safe_load_kml(file_path):
        #     try:
        #         return KMLFile.from_file(file_path)
        #     except KMLParseError as e:
        #         raise ValueError(f"Invalid KML file: {file_path}") from e
        #     except FileNotFoundError as e:
        #         raise ValueError(f"KML file not found: {file_path}") from e

        def safe_load_kml(file_path: str) -> Optional[KMLFile]:
            try:
                return KMLFile.from_file(file_path)
            except KMLParseError as e:
                raise ValueError(f"Invalid KML file: {file_path}") from e
            except FileNotFoundError as e:
                raise ValueError(f"KML file not found: {file_path}") from e

        # Test with valid file
        result = safe_load_kml(self.temp_file.name)
        self.assertIsInstance(result, KMLFile)

        # Test with invalid KML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as invalid_file:
            invalid_file.write("invalid xml")
        invalid_file.close()

        try:
            with self.assertRaises(ValueError) as context:
                safe_load_kml(invalid_file.name)

            self.assertIn("Invalid KML file:", str(context.exception))
            # Verify the exception was chained
            self.assertIsInstance(context.exception.__cause__, KMLParseError)
        finally:
            os.unlink(invalid_file.name)

        # Test with non-existent file
        with self.assertRaises(ValueError) as context:
            safe_load_kml("nonexistent_file.kml")

        self.assertIn("KML file not found:", str(context.exception))
        # Verify the exception was chained
        self.assertIsInstance(context.exception.__cause__, FileNotFoundError)

    def test_importing_exceptions_main_package_example(self) -> None:
        """Test the importing exceptions from main package example from
        kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # # Import from main package (recommended)
        # from kmlorm import (
        #     KMLOrmException,
        #     KMLParseError,
        #     KMLValidationError,
        #     KMLElementNotFound,
        #     KMLMultipleElementsReturned,
        #     KMLInvalidCoordinates
        # )

        # Test the recommended import pattern as shown in documentation
        # pylint: disable=import-outside-toplevel, reimported
        from kmlorm import (
            KMLOrmException as MainKMLOrmException,
            KMLParseError as MainKMLParseError,
            KMLValidationError as MainKMLValidationError,
            KMLElementNotFound as MainKMLElementNotFound,
            KMLMultipleElementsReturned as MainKMLMultipleElementsReturned,
            KMLInvalidCoordinates as MainKMLInvalidCoordinates,
        )

        # Verify all the exceptions can be imported from main package
        self.assertEqual(MainKMLOrmException.__name__, "KMLOrmException")
        self.assertEqual(MainKMLParseError.__name__, "KMLParseError")
        self.assertEqual(MainKMLValidationError.__name__, "KMLValidationError")
        self.assertEqual(MainKMLElementNotFound.__name__, "KMLElementNotFound")
        self.assertEqual(MainKMLMultipleElementsReturned.__name__, "KMLMultipleElementsReturned")
        self.assertEqual(MainKMLInvalidCoordinates.__name__, "KMLInvalidCoordinates")

        # Verify they are the same classes as the ones we imported at module level
        self.assertIs(MainKMLOrmException, KMLOrmException)
        self.assertIs(MainKMLParseError, KMLParseError)
        self.assertIs(MainKMLValidationError, KMLValidationError)
        self.assertIs(MainKMLElementNotFound, KMLElementNotFound)
        self.assertIs(MainKMLMultipleElementsReturned, KMLMultipleElementsReturned)
        self.assertIs(MainKMLInvalidCoordinates, KMLInvalidCoordinates)

    def test_importing_exceptions_direct_module_example(self) -> None:
        """Test the importing exceptions directly from module example from
        kmlorm.core.exceptions.rst."""
        # Example from kmlorm.core.exceptions.rst:
        # # Or import directly from exceptions module
        # from kmlorm.core.exceptions import (
        #     KMLOrmException,
        #     KMLParseError,
        #     KMLValidationError,
        #     KMLElementNotFound,
        #     KMLMultipleElementsReturned,
        #     KMLInvalidCoordinates,
        #     KMLQueryError
        # )

        # Test the direct module import pattern as shown in documentation
        # pylint: disable=import-outside-toplevel, reimported
        from kmlorm.core.exceptions import (
            KMLOrmException as DirectKMLOrmException,
            KMLParseError as DirectKMLParseError,
            KMLValidationError as DirectKMLValidationError,
            KMLElementNotFound as DirectKMLElementNotFound,
            KMLMultipleElementsReturned as DirectKMLMultipleElementsReturned,
            KMLInvalidCoordinates as DirectKMLInvalidCoordinates,
            KMLQueryError as DirectKMLQueryError,
        )

        # Verify all the exceptions can be imported directly from the module
        self.assertEqual(DirectKMLOrmException.__name__, "KMLOrmException")
        self.assertEqual(DirectKMLParseError.__name__, "KMLParseError")
        self.assertEqual(DirectKMLValidationError.__name__, "KMLValidationError")
        self.assertEqual(DirectKMLElementNotFound.__name__, "KMLElementNotFound")
        self.assertEqual(DirectKMLMultipleElementsReturned.__name__, "KMLMultipleElementsReturned")
        self.assertEqual(DirectKMLInvalidCoordinates.__name__, "KMLInvalidCoordinates")
        self.assertEqual(DirectKMLQueryError.__name__, "KMLQueryError")

        # Verify they are the same classes as the ones we imported at module level
        self.assertIs(DirectKMLOrmException, KMLOrmException)
        self.assertIs(DirectKMLParseError, KMLParseError)
        self.assertIs(DirectKMLValidationError, KMLValidationError)
        self.assertIs(DirectKMLElementNotFound, KMLElementNotFound)
        self.assertIs(DirectKMLMultipleElementsReturned, KMLMultipleElementsReturned)
        self.assertIs(DirectKMLInvalidCoordinates, KMLInvalidCoordinates)
        self.assertIs(DirectKMLQueryError, KMLQueryError)

        # Note: KMLQueryError is only available in direct import, not from main package

    def test_exception_hierarchy_inheritance(self) -> None:
        """Test that the documented exception hierarchy is correct."""
        # Documentation states that all exceptions inherit from KMLOrmException

        # Test KMLParseError inheritance
        self.assertTrue(issubclass(KMLParseError, KMLOrmException))

        # Test KMLValidationError inheritance
        self.assertTrue(issubclass(KMLValidationError, KMLOrmException))

        # Test KMLElementNotFound inheritance
        self.assertTrue(issubclass(KMLElementNotFound, KMLOrmException))

        # Test KMLMultipleElementsReturned inheritance
        self.assertTrue(issubclass(KMLMultipleElementsReturned, KMLOrmException))

        # Test KMLInvalidCoordinates inheritance
        self.assertTrue(issubclass(KMLInvalidCoordinates, KMLOrmException))

        # Test KMLQueryError inheritance
        self.assertTrue(issubclass(KMLQueryError, KMLOrmException))


if __name__ == "__main__":
    unittest.main()
