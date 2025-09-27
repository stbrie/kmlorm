"""
Tests that validate the kmlorm.core package documentation and functionality.

Since docs/source/api/kmlorm.core.rst is primarily a package overview using autodoc,
this test suite validates that the core package structure, imports, and exports
work as documented and expected.
"""

# pylint: disable=duplicate-code
import unittest
import inspect
from typing import Any


class TestCoreDocsExamples(unittest.TestCase):
    """Test cases that validate kmlorm.core package functionality."""

    def test_core_package_imports(self) -> None:
        """Test that all documented imports from kmlorm.core work correctly."""
        # Test importing the core package
        import kmlorm.core  # pylint: disable=import-outside-toplevel

        # Verify the package has the expected docstring
        self.assertIsNotNone(kmlorm.core.__doc__)
        if kmlorm.core.__doc__:
            self.assertIn("Core functionality for KML ORM", kmlorm.core.__doc__)

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
        self.assertTrue(inspect.isclass(KMLOrmException))
        self.assertTrue(inspect.isclass(KMLParseError))
        self.assertTrue(inspect.isclass(KMLElementNotFound))
        self.assertTrue(inspect.isclass(KMLMultipleElementsReturned))
        self.assertTrue(inspect.isclass(KMLInvalidCoordinates))
        self.assertTrue(inspect.isclass(KMLValidationError))
        self.assertTrue(inspect.isclass(KMLQueryError))

        # Verify inheritance hierarchy
        self.assertTrue(issubclass(KMLParseError, KMLOrmException))
        self.assertTrue(issubclass(KMLElementNotFound, KMLOrmException))
        self.assertTrue(issubclass(KMLMultipleElementsReturned, KMLOrmException))
        self.assertTrue(issubclass(KMLInvalidCoordinates, KMLOrmException))
        self.assertTrue(issubclass(KMLValidationError, KMLOrmException))
        self.assertTrue(issubclass(KMLQueryError, KMLOrmException))

    def test_core_managers_import(self) -> None:
        """Test that manager classes can be imported from kmlorm.core."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLManager, RelatedManager

        # Verify manager classes are available
        self.assertTrue(inspect.isclass(KMLManager))
        self.assertTrue(inspect.isclass(RelatedManager))

        # Verify RelatedManager inherits from KMLManager
        self.assertTrue(issubclass(RelatedManager, KMLManager))

    def test_core_querysets_import(self) -> None:
        """Test that QuerySet class can be imported from kmlorm.core."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLQuerySet

        # Verify QuerySet class is available
        self.assertTrue(inspect.isclass(KMLQuerySet))

        # Verify it's a generic class
        self.assertTrue(hasattr(KMLQuerySet, "__orig_bases__"))

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
        self.assertTrue(hasattr(kmlorm.core, "__all__"))
        self.assertIsInstance(kmlorm.core.__all__, list)

        for export in expected_exports:
            self.assertIn(export, kmlorm.core.__all__)

        # Verify all exports in __all__ are actually available
        for export in kmlorm.core.__all__:
            self.assertTrue(hasattr(kmlorm.core, export))

    def test_core_exception_functionality(self) -> None:
        """Test that core exceptions work as expected."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import (
            KMLElementNotFound,
            KMLMultipleElementsReturned,
            KMLValidationError,
        )

        # Test that exceptions can be raised and caught
        with self.assertRaises(KMLElementNotFound):
            raise KMLElementNotFound("Placemark")

        with self.assertRaises(KMLMultipleElementsReturned):
            raise KMLMultipleElementsReturned("Placemark", 2)

        with self.assertRaises(KMLValidationError):
            raise KMLValidationError("Validation failed")

        # Test exception messages
        try:
            raise KMLElementNotFound("TestElement")
        except KMLElementNotFound as e:
            self.assertEqual(str(e), "TestElement does not exist.")

    def test_core_manager_instantiation(self) -> None:
        """Test that core manager classes can be instantiated."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLManager, RelatedManager

        # Test KMLManager instantiation
        manager: Any = KMLManager()
        self.assertIsInstance(manager, KMLManager)

        # Test RelatedManager instantiation
        related_manager: Any = RelatedManager()
        self.assertIsInstance(related_manager, RelatedManager)
        self.assertIsInstance(related_manager, KMLManager)  # Should inherit

    def test_core_queryset_instantiation(self) -> None:
        """Test that core QuerySet class can be instantiated."""
        # pylint: disable=import-outside-toplevel
        from kmlorm.core import KMLQuerySet

        # Test QuerySet instantiation with empty list
        queryset: Any = KMLQuerySet([])
        self.assertIsInstance(queryset, KMLQuerySet)
        self.assertEqual(len(queryset), 0)

        # Test QuerySet with some mock elements (using Any to avoid type errors)
        mock_elements: Any = ["element1", "element2", "element3"]
        queryset = KMLQuerySet(mock_elements)
        self.assertEqual(len(queryset), 3)
        self.assertIn("element1", queryset)

    def test_core_package_structure(self) -> None:
        """Test that the core package structure matches documentation."""
        # pylint: disable=import-outside-toplevel
        import kmlorm.core
        import kmlorm.core.exceptions
        import kmlorm.core.managers
        import kmlorm.core.querysets

        # Verify submodules are accessible
        self.assertTrue(hasattr(kmlorm.core, "exceptions"))
        self.assertTrue(hasattr(kmlorm.core, "managers"))
        self.assertTrue(hasattr(kmlorm.core, "querysets"))

        # Verify submodules have expected content
        self.assertTrue(hasattr(kmlorm.core.exceptions, "KMLOrmException"))
        self.assertTrue(hasattr(kmlorm.core.managers, "KMLManager"))
        self.assertTrue(hasattr(kmlorm.core.querysets, "KMLQuerySet"))

    def test_core_star_import(self) -> None:
        """Test that star import from kmlorm.core works correctly."""
        # This test verifies that 'from kmlorm.core import *' would work
        # pylint: disable=import-outside-toplevel
        import kmlorm.core

        # Get all public names that should be importable with *
        public_names = [name for name in dir(kmlorm.core) if not name.startswith("_")]

        # Verify __all__ covers the main exports
        for name in kmlorm.core.__all__:
            self.assertIn(name, public_names)

        # Verify each item in __all__ is actually accessible
        for name in kmlorm.core.__all__:
            attr = getattr(kmlorm.core, name)
            self.assertIsNotNone(attr)

    def test_core_docstring_content(self) -> None:
        """Test that core package docstring contains expected information."""
        # pylint: disable=import-outside-toplevel
        import kmlorm.core

        docstring = kmlorm.core.__doc__
        self.assertIsNotNone(docstring)

        # Verify key concepts are mentioned
        if docstring:
            self.assertIn("Core functionality", docstring)
            self.assertIn("KML ORM", docstring)
            self.assertIn("Django-style", docstring)
            self.assertIn("ORM interface", docstring)

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
            self.assertIsInstance(hints, dict)
        except (NameError, AttributeError):
            # Type hints may not be available in all contexts
            pass

        # KMLQuerySet should be generic
        self.assertTrue(hasattr(KMLQuerySet, "__class_getitem__"))

    def test_core_integration_with_main_package(self) -> None:
        """Test that core classes integrate properly with main kmlorm package."""
        # Test that core exceptions are available from main package
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLValidationError
        from kmlorm.core import KMLValidationError as CoreKMLValidationError

        # Should be the same class
        self.assertIs(KMLValidationError, CoreKMLValidationError)

        # Test that Coordinate class is available
        from kmlorm.models.point import Coordinate

        # Test that core exception is raised by coordinate validation
        with self.assertRaises(KMLValidationError):
            Coordinate(longitude=200, latitude=100)  # Invalid coordinates

    def test_core_module_metadata(self) -> None:
        """Test that core module has proper metadata."""
        # pylint: disable=import-outside-toplevel
        import kmlorm.core

        # Should have a docstring
        self.assertIsNotNone(kmlorm.core.__doc__)
        self.assertIsInstance(kmlorm.core.__doc__, str)
        if kmlorm.core.__doc__:
            self.assertGreater(len(kmlorm.core.__doc__.strip()), 0)

        # Should have __all__ defined
        self.assertTrue(hasattr(kmlorm.core, "__all__"))
        self.assertIsInstance(kmlorm.core.__all__, list)
        self.assertGreater(len(kmlorm.core.__all__), 0)

        # Should have a package path
        self.assertTrue(hasattr(kmlorm.core, "__path__"))


if __name__ == "__main__":
    unittest.main()
