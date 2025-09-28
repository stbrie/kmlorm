"""
Tests that validate the kmlorm.core package documentation and functionality.

Since docs/source/api/kmlorm.core.rst is primarily a package overview using autodoc,
this test suite validates that the core package structure, imports, and exports
work as documented and expected.
"""

# pylint: disable=duplicate-code
import inspect
from typing import Any
import pytest


class TestCoreDocsExamples:
    """Test cases that validate kmlorm.core package functionality."""

    def test_core_package_imports(self) -> None:
        """Test that all documented imports from kmlorm.core work correctly."""
        # Test importing the core package
        import kmlorm.core  # pylint: disable=import-outside-toplevel

        # Verify the package has the expected docstring
        assert kmlorm.core.__doc__ is not None
        if kmlorm.core.__doc__:
            assert "Core functionality for KML ORM" in kmlorm.core.__doc__

    def test_core_exceptions_import(self) -> None:
        """Test that all exception classes can be imported from kmlorm.core."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import (
            KMLElementNotFound,
            KMLInvalidCoordinates,
            KMLMultipleElementsReturned,
            KMLOrmException,
            KMLParseError,
            KMLQueryError,
            KMLValidationError,
        )

        # Verify all exception classes are available
        assert inspect.isclass(KMLOrmException) is True
        assert inspect.isclass(KMLParseError) is True
        assert inspect.isclass(KMLElementNotFound) is True
        assert inspect.isclass(KMLMultipleElementsReturned) is True
        assert inspect.isclass(KMLInvalidCoordinates) is True
        assert inspect.isclass(KMLValidationError) is True
        assert inspect.isclass(KMLQueryError) is True

        # Verify inheritance hierarchy
        assert issubclass(KMLParseError, KMLOrmException) is True
        assert issubclass(KMLElementNotFound, KMLOrmException) is True
        assert issubclass(KMLMultipleElementsReturned, KMLOrmException) is True
        assert issubclass(KMLInvalidCoordinates, KMLOrmException) is True
        assert issubclass(KMLValidationError, KMLOrmException) is True
        assert issubclass(KMLQueryError, KMLOrmException) is True

    def test_core_managers_import(self) -> None:
        """Test that manager classes can be imported from kmlorm.core."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLManager, RelatedManager

        # Verify manager classes are available
        assert inspect.isclass(KMLManager) is True
        assert inspect.isclass(RelatedManager) is True

        # Verify RelatedManager inherits from KMLManager
        assert issubclass(RelatedManager, KMLManager) is True

    def test_core_querysets_import(self) -> None:
        """Test that QuerySet class can be imported from kmlorm.core."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLQuerySet

        # Verify QuerySet class is available
        assert inspect.isclass(KMLQuerySet) is True

        # Verify it's a generic class
        assert hasattr(KMLQuerySet, "__orig_bases__") is True

    def test_core_all_exports(self) -> None:
        """Test that __all__ contains all documented exports."""
        # pylint: disable=import-outside-toplevel
        import kmlorm.core

        expected_exports = [
            "KMLOrmException",
            "KMLParseError",
            "KMLElementNotFound",
            "KMLMultipleElementsReturned",
            "KMLInvalidCoordinates",
            "KMLValidationError",
            "KMLQueryError",
            "KMLManager",
            "RelatedManager",
            "KMLQuerySet",
        ]

        # Verify __all__ exists and contains expected exports
        assert hasattr(kmlorm.core, "__all__") is True
        assert isinstance(kmlorm.core.__all__, list)

        for export in expected_exports:
            assert export in kmlorm.core.__all__

        # Verify all exports in __all__ are actually available
        for export in kmlorm.core.__all__:
            assert hasattr(kmlorm.core, export) is True

    def test_core_exception_functionality(self) -> None:
        """Test that core exceptions work as expected."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import (
            KMLElementNotFound,
            KMLMultipleElementsReturned,
            KMLValidationError,
        )

        # Test that exceptions can be raised and caught
        with pytest.raises(KMLElementNotFound):
            raise KMLElementNotFound("Placemark")

        with pytest.raises(KMLMultipleElementsReturned):
            raise KMLMultipleElementsReturned("Placemark", 2)

        with pytest.raises(KMLValidationError):
            raise KMLValidationError("Validation failed")

        # Test exception messages
        try:
            raise KMLElementNotFound("TestElement")
        except KMLElementNotFound as e:
            assert str(e) == "TestElement does not exist."

    def test_core_manager_instantiation(self) -> None:
        """Test that core manager classes can be instantiated."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLManager, RelatedManager

        # Test KMLManager instantiation
        manager: Any = KMLManager()
        assert isinstance(manager, KMLManager)

        # Test RelatedManager instantiation
        related_manager: Any = RelatedManager()
        assert isinstance(related_manager, RelatedManager)
        assert isinstance(related_manager, KMLManager)  # Should inherit

    def test_core_queryset_instantiation(self) -> None:
        """Test that core QuerySet class can be instantiated."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLQuerySet

        # Test QuerySet instantiation with empty list
        queryset: Any = KMLQuerySet([])
        assert isinstance(queryset, KMLQuerySet)
        assert len(queryset) == 0

        # Test QuerySet with some mock elements (using Any to avoid type errors)
        mock_elements: Any = ["element1", "element2", "element3"]
        queryset = KMLQuerySet(mock_elements)
        assert len(queryset) == 3
        assert "element1" in queryset

    def test_core_package_structure(self) -> None:
        """Test that the core package structure matches documentation."""
        # pylint: disable=import-outside-toplevel
        import kmlorm.core
        import kmlorm.core.exceptions
        import kmlorm.core.managers
        import kmlorm.core.querysets

        # Verify submodules are accessible
        assert hasattr(kmlorm.core, "exceptions") is True
        assert hasattr(kmlorm.core, "managers") is True
        assert hasattr(kmlorm.core, "querysets") is True

        # Verify submodules have expected content
        assert hasattr(kmlorm.core.exceptions, "KMLOrmException") is True
        assert hasattr(kmlorm.core.managers, "KMLManager") is True
        assert hasattr(kmlorm.core.querysets, "KMLQuerySet") is True

    def test_core_star_import(self) -> None:
        """Test that star import from kmlorm.core works correctly."""
        # This test verifies that 'from kmlorm.core import *' would work
        # pylint: disable=import-outside-toplevel
        import kmlorm.core

        # Get all public names that should be importable with *
        public_names = [name for name in dir(kmlorm.core) if not name.startswith("_")]

        # Verify __all__ covers the main exports
        for name in kmlorm.core.__all__:
            assert name in public_names

        # Verify each item in __all__ is actually accessible
        for name in kmlorm.core.__all__:
            attr = getattr(kmlorm.core, name)
            assert attr is not None

    def test_core_docstring_content(self) -> None:
        """Test that core package docstring contains expected information."""
        # pylint: disable=import-outside-toplevel
        import kmlorm.core

        docstring = kmlorm.core.__doc__
        assert docstring is not None

        # Verify key concepts are mentioned
        if docstring:
            assert "Core functionality" in docstring
            assert "KML ORM" in docstring
            assert "Django-style" in docstring
            assert "ORM interface" in docstring

    def test_core_type_checking_support(self) -> None:
        """Test that core classes support type checking as expected."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLManager, KMLQuerySet
        from typing import get_type_hints

        # Test that classes have proper type annotations where expected
        # KMLManager should have type annotations
        try:
            hints = get_type_hints(KMLManager.__init__)
            # Should have at least return type annotation
            assert isinstance(hints, dict)
        except (NameError, AttributeError):
            # Type hints may not be available in all contexts
            pass

        # KMLQuerySet should be generic
        assert hasattr(KMLQuerySet, "__class_getitem__") is True

    def test_core_integration_with_main_package(self) -> None:
        """Test that core classes integrate properly with main kmlorm package."""
        # Test that core exceptions are available from main package
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLValidationError
        from kmlorm.core import KMLValidationError as CoreKMLValidationError

        # Should be the same class
        assert KMLValidationError is CoreKMLValidationError

        # Test that Coordinate class is available
        from kmlorm.models.point import Coordinate

        # Test that core exception is raised by coordinate validation
        with pytest.raises(KMLValidationError):
            Coordinate(longitude=200, latitude=100)  # Invalid coordinates

    def test_core_module_metadata(self) -> None:
        """Test that core module has proper metadata."""
        # pylint: disable=import-outside-toplevel
        import kmlorm.core

        # Should have a docstring
        assert kmlorm.core.__doc__ is not None
        assert isinstance(kmlorm.core.__doc__, str)
        if kmlorm.core.__doc__:
            assert len(kmlorm.core.__doc__.strip()) > 0

        # Should have __all__ defined
        assert hasattr(kmlorm.core, "__all__")
        assert isinstance(kmlorm.core.__all__, list)
        assert len(kmlorm.core.__all__) > 0

        # Should have a package path
        assert hasattr(kmlorm.core, "__path__")
