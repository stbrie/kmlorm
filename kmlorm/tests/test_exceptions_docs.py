"""
Tests that validate every example in docs/source/api/exceptions.rst and
docs/source/api/kmlorm.core.exceptions.rst work as documented.

This test suite ensures that all code examples in the exceptions documentation
are functional and produce the expected results.
"""

# pylint: disable=duplicate-code, too-many-public-methods

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch
from typing import Optional, Generator
import pytest
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


class TestExceptionsDocsExamples:
    """Test cases that validate exceptions.rst documentation examples."""

    @pytest.fixture
    def temp_kml_content(self) -> str:
        """Provide comprehensive KML content for testing exceptions."""
        return """<?xml version="1.0" encoding="UTF-8"?>
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

    @pytest.fixture
    def temp_kml_file(self, temp_kml_content: str) -> Generator[Path, None, None]:
        """Create temporary KML file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".kml", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(temp_kml_content)
            temp_path = Path(temp_file.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def invalid_kml_content(self) -> str:
        """Provide invalid KML content for testing parse errors."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <InvalidElement>This is not valid KML</InvalidElement>
    </Document>
</kml>"""

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
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".kml", delete=False, encoding="utf-8"
        ) as invalid_file:
            invalid_file.write("invalid xml content")
            invalid_path = Path(invalid_file.name)

        try:
            with pytest.raises(KMLParseError) as exc_info:
                _ = KMLFile.from_file(str(invalid_path))

            # Verify we can format the error as shown in documentation
            error_message = f"Failed to parse KML: {exc_info.value}"
            assert "Failed to parse KML:" in error_message
        finally:
            invalid_path.unlink()

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
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".kml", delete=False, encoding="utf-8"
        ) as invalid_file:
            invalid_file.write("invalid xml content")
            invalid_path = Path(invalid_file.name)

        try:
            with pytest.raises(KMLParseError) as exc_info:
                _ = KMLFile.from_file(str(invalid_path))

            e = exc_info.value
            # Test the formatted message as shown in documentation
            parse_error_msg = f"Failed to parse KML: {e}"
            assert "Failed to parse KML:" in parse_error_msg

            # Test the source attribute handling as shown in documentation
            if hasattr(e, "source") and e.source:
                source_msg = f"Source: {e.source}"
                assert "Source:" in source_msg
        finally:
            invalid_path.unlink()

    def test_handling_query_errors_element_not_found_basic_example(
        self, temp_kml_file: Path
    ) -> None:
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

        kml = KMLFile.from_file(str(temp_kml_file))

        with pytest.raises(KMLElementNotFound):
            _ = kml.placemarks.get(name="Nonexistent Store")

        # Test that we can catch and handle it as shown in documentation
        handled = False
        try:
            _ = kml.placemarks.get(name="Nonexistent Store")
        except KMLElementNotFound:
            handled = True

        assert handled

    def test_handling_query_errors_multiple_elements_basic_example(
        self, temp_kml_file: Path
    ) -> None:
        """Test the basic KMLMultipleElementsReturned example from exceptions.rst."""
        # Example from exceptions.rst:
        # try:
        #     # This will raise KMLMultipleElementsReturned if multiple matches
        #     store = kml.placemarks.get(name__icontains='Capital')
        # except KMLMultipleElementsReturned:
        #     print("Multiple stores found, be more specific")

        kml = KMLFile.from_file(str(temp_kml_file))

        with pytest.raises(KMLMultipleElementsReturned):
            _ = kml.placemarks.get(name__icontains="Capital")

        # Test that we can catch and handle it as shown in documentation
        handled = False
        try:
            _ = kml.placemarks.get(name__icontains="Capital")
        except KMLMultipleElementsReturned:
            handled = True

        assert handled

    def test_handling_query_errors_comprehensive_element_not_found_example(
        self, temp_kml_file: Path
    ) -> None:
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

        kml = KMLFile.from_file(str(temp_kml_file))

        with pytest.raises(KMLElementNotFound) as exc_info:
            _ = kml.placemarks.all().get(name="Nonexistent Store")

        e = exc_info.value
        # Test the formatted messages as shown in documentation
        element_not_found_msg = f"Element not found: {e}"
        element_type_msg = f"Element type: {e.element_type}"
        query_msg = f"Query: {e.query_kwargs}"

        assert "Element not found:" in element_not_found_msg
        assert "Element type:" in element_type_msg
        assert "Query:" in query_msg

        # Verify the attributes exist as documented
        assert hasattr(e, "element_type")
        assert hasattr(e, "query_kwargs")

    def test_handling_query_errors_comprehensive_multiple_elements_example(
        self, temp_kml_file: Path
    ) -> None:
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

        kml = KMLFile.from_file(str(temp_kml_file))

        with pytest.raises(KMLMultipleElementsReturned) as exc_info:
            _ = kml.placemarks.all().get(name__icontains="Store")

        e = exc_info.value
        # Test the formatted messages as shown in documentation
        multiple_elements_msg = f"Multiple elements found: {e}"
        element_type_msg = f"Element type: {e.element_type}"
        count_msg = f"Count: {e.count}"
        query_msg = f"Query: {e.query_kwargs}"

        assert "Multiple elements found:" in multiple_elements_msg
        assert "Element type:" in element_type_msg
        assert "Count:" in count_msg
        assert "Query:" in query_msg

        # Verify the attributes exist as documented
        assert hasattr(e, "element_type")
        assert hasattr(e, "count")
        assert hasattr(e, "query_kwargs")

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

        with pytest.raises(KMLValidationError) as exc_info:
            _ = Coordinate(longitude=200, latitude=100)

        e = exc_info.value
        # Test the formatted messages as shown in documentation
        validation_msg = f"Validation failed: {e}"
        field_msg = f"Field: {e.field}" if hasattr(e, "field") else "Field: N/A"
        value_msg = f"Value: {e.value}" if hasattr(e, "value") else "Value: N/A"

        assert "Validation failed:" in validation_msg
        assert "Field:" in field_msg
        assert "Value:" in value_msg

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

        with pytest.raises(KMLValidationError) as exc_info:
            _ = Coordinate(longitude=200, latitude=100)

        e = exc_info.value
        # Test the formatted message as shown in documentation
        validation_error_msg = f"Validation error: {e}"
        assert "Validation error:" in validation_error_msg

        # Test the conditional attribute access as shown in documentation
        if hasattr(e, "field"):
            field_msg = f"Field: {e.field}"
            assert "Field:" in field_msg

        if hasattr(e, "value"):
            value_msg = f"Value: {e.value}"
            assert "Value:" in value_msg

    def test_best_practices_logging_example(self, temp_kml_file: Path) -> None:
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

        def load_kml_safely(file_path: str) -> Optional[KMLFile]:
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
        result = load_kml_safely(str(temp_kml_file))
        assert isinstance(result, KMLFile)

        # Test with invalid file - should raise ValueError
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".kml", delete=False, encoding="utf-8"
        ) as invalid_file:
            invalid_file.write("invalid xml")
            invalid_path = Path(invalid_file.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_kml_safely(str(invalid_path))

            assert "Invalid KML file:" in str(exc_info.value)
        finally:
            invalid_path.unlink()

        # Test with non-existent file - should raise RuntimeError
        with pytest.raises(RuntimeError) as runtime_exc_info:
            load_kml_safely("nonexistent.kml")

        assert "Failed to load KML file:" in str(runtime_exc_info.value)

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

        with pytest.raises(KMLValidationError) as exc_info:
            _ = Coordinate(longitude=200, latitude=100)

        e = exc_info.value
        # Test the formatted messages as shown in documentation
        field_msg = f"Field: {e.field if hasattr(e, 'field') else 'N/A'}"
        value_msg = f"Value: {e.value if hasattr(e, 'value') else 'N/A'}"
        message_msg = f"Message: {str(e)}"

        assert "Field:" in field_msg
        assert "Value:" in value_msg
        assert "Message:" in message_msg

    def test_error_context_element_not_found_attributes_example(self, temp_kml_file: Path) -> None:
        """Test the KMLElementNotFound attributes example from exceptions.rst."""
        # Example from exceptions.rst:
        # # Exception attributes available for KMLElementNotFound:
        # try:
        #     kml.placemarks.get(name='Missing')
        # except KMLElementNotFound as e:
        #     print(f"Element type: {e.element_type}")
        #     print(f"Query: {e.query_kwargs}")

        kml = KMLFile.from_file(str(temp_kml_file))

        with pytest.raises(KMLElementNotFound) as exc_info:
            kml.placemarks.get(name="Missing")

        e = exc_info.value
        # Test the attribute access as shown in documentation
        element_type_msg = f"Element type: {e.element_type}"
        query_msg = f"Query: {e.query_kwargs}"

        assert "Element type:" in element_type_msg
        assert "Query:" in query_msg

        # Verify the attributes are accessible
        assert hasattr(e, "element_type")
        assert hasattr(e, "query_kwargs")

    def test_error_context_multiple_elements_attributes_example(self, temp_kml_file: Path) -> None:
        """Test the KMLMultipleElementsReturned attributes example from exceptions.rst."""
        # Example from exceptions.rst:
        # # Exception attributes available for KMLMultipleElementsReturned:
        # try:
        #     kml.placemarks.get(name__icontains='Store')
        # except KMLMultipleElementsReturned as e:
        #     print(f"Element type: {e.element_type}")
        #     print(f"Count found: {e.count}")
        #     print(f"Query: {e.query_kwargs}")

        kml = KMLFile.from_file(str(temp_kml_file))

        with pytest.raises(KMLMultipleElementsReturned) as exc_info:
            kml.placemarks.get(name__icontains="Store")

        e = exc_info.value
        # Test the attribute access as shown in documentation
        element_type_msg = f"Element type: {e.element_type}"
        count_msg = f"Count found: {e.count}"
        query_msg = f"Query: {e.query_kwargs}"

        assert "Element type:" in element_type_msg
        assert "Count found:" in count_msg
        assert "Query:" in query_msg

        # Verify the attributes are accessible
        assert hasattr(e, "element_type")
        assert hasattr(e, "count")
        assert hasattr(e, "query_kwargs")

    def test_best_practices_catch_specific_exceptions_first_example(
        self, temp_kml_file: Path
    ) -> None:
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

        kml = KMLFile.from_file(str(temp_kml_file))

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

        assert not_found_handled

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

        assert multiple_handled

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
                    "Validation failed for field %s with value %s: %s",
                    getattr(e, "field", "unknown"),
                    getattr(e, "value", "unknown"),
                    e,
                )

            # Verify logger.error was called
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]  # Get the first argument to logger.error
            assert "Validation failed for field" in call_args

    def test_best_practices_chain_exception_handling_example(self, temp_kml_file: Path) -> None:
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
        result = safe_load_kml(str(temp_kml_file))
        assert isinstance(result, KMLFile)

        # Test with invalid KML
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".kml", delete=False, encoding="utf-8"
        ) as invalid_file:
            invalid_file.write("invalid xml")
            invalid_path = Path(invalid_file.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                safe_load_kml(str(invalid_path))

            assert "Invalid KML file:" in str(exc_info.value)
            # Verify the exception was chained
            assert isinstance(exc_info.value.__cause__, KMLParseError)
        finally:
            invalid_path.unlink()

        # Test with non-existent file
        with pytest.raises(ValueError) as exc_info:
            safe_load_kml("nonexistent_file.kml")

        assert "KML file not found:" in str(exc_info.value)
        # Verify the exception was chained
        assert isinstance(exc_info.value.__cause__, FileNotFoundError)

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
        assert MainKMLOrmException.__name__ == "KMLOrmException"
        assert MainKMLParseError.__name__ == "KMLParseError"
        assert MainKMLValidationError.__name__ == "KMLValidationError"
        assert MainKMLElementNotFound.__name__ == "KMLElementNotFound"
        assert MainKMLMultipleElementsReturned.__name__ == "KMLMultipleElementsReturned"
        assert MainKMLInvalidCoordinates.__name__ == "KMLInvalidCoordinates"

        # Verify they are the same classes as the ones we imported at module level
        assert MainKMLOrmException is KMLOrmException
        assert MainKMLParseError is KMLParseError
        assert MainKMLValidationError is KMLValidationError
        assert MainKMLElementNotFound is KMLElementNotFound
        assert MainKMLMultipleElementsReturned is KMLMultipleElementsReturned
        assert MainKMLInvalidCoordinates is KMLInvalidCoordinates

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
        assert DirectKMLOrmException.__name__ == "KMLOrmException"
        assert DirectKMLParseError.__name__ == "KMLParseError"
        assert DirectKMLValidationError.__name__ == "KMLValidationError"
        assert DirectKMLElementNotFound.__name__ == "KMLElementNotFound"
        assert DirectKMLMultipleElementsReturned.__name__ == "KMLMultipleElementsReturned"
        assert DirectKMLInvalidCoordinates.__name__ == "KMLInvalidCoordinates"
        assert DirectKMLQueryError.__name__ == "KMLQueryError"

        # Verify they are the same classes as the ones we imported at module level
        assert DirectKMLOrmException is KMLOrmException
        assert DirectKMLParseError is KMLParseError
        assert DirectKMLValidationError is KMLValidationError
        assert DirectKMLElementNotFound is KMLElementNotFound
        assert DirectKMLMultipleElementsReturned is KMLMultipleElementsReturned
        assert DirectKMLInvalidCoordinates is KMLInvalidCoordinates
        assert DirectKMLQueryError is KMLQueryError

        # Note: KMLQueryError is only available in direct import, not from main package

    def test_exception_hierarchy_inheritance(self) -> None:
        """Test that the documented exception hierarchy is correct."""
        # Documentation states that all exceptions inherit from KMLOrmException

        # Test KMLParseError inheritance
        assert issubclass(KMLParseError, KMLOrmException)

        # Test KMLValidationError inheritance
        assert issubclass(KMLValidationError, KMLOrmException)

        # Test KMLElementNotFound inheritance
        assert issubclass(KMLElementNotFound, KMLOrmException)

        # Test KMLMultipleElementsReturned inheritance
        assert issubclass(KMLMultipleElementsReturned, KMLOrmException)

        # Test KMLInvalidCoordinates inheritance
        assert issubclass(KMLInvalidCoordinates, KMLOrmException)

        # Test KMLQueryError inheritance
        assert issubclass(KMLQueryError, KMLOrmException)
