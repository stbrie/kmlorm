"""
Tests that validate the kmlorm.models package documentation and functionality.

These tests ensure that all examples shown in docs/source/api/models.rst
work exactly as documented.
"""

import unittest

from kmlorm import Placemark, Folder


class TestModelsDocsExamples(unittest.TestCase):
    """Test cases that validate all models.rst documentation examples."""

    def test_example_usage_placemark_creation(self) -> None:
        """Test the placemark creation example from models.rst."""
        # Create a placemark with coordinates
        store = Placemark(
            name="Capital Electric", address="123 Main St, Baltimore, MD", coordinates=(-76.5, 39.3)
        )

        # Verify the placemark was created correctly
        assert store is not None
        self.assertEqual(store.name, "Capital Electric")
        self.assertEqual(store.address, "123 Main St, Baltimore, MD")
        self.assertIsNotNone(store.coordinates)
        # pylint's static analysis is a bit limited, unfortunately
        if store.coordinates:
            self.assertEqual(store.coordinates.longitude, -76.5)  # pylint: disable=E1101
            self.assertEqual(store.coordinates.latitude, 39.3)  # pylint: disable=E1101

    def test_example_usage_folder_organization(self) -> None:
        """Test the folder organization example from models.rst."""
        # Create a placemark with coordinates
        store = Placemark(
            name="Capital Electric", address="123 Main St, Baltimore, MD", coordinates=(-76.5, 39.3)
        )

        # Create a folder to organize placemarks
        stores_folder = Folder(name="Electric Stores")
        stores_folder.placemarks.add(store)

        # Verify the folder was created correctly
        self.assertEqual(stores_folder.name, "Electric Stores")
        self.assertIn(store, stores_folder.placemarks.all())

    def test_example_usage_coordinate_access(self) -> None:
        """Test the coordinate access example from models.rst."""
        # Create a placemark with coordinates
        store = Placemark(
            name="Capital Electric", address="123 Main St, Baltimore, MD", coordinates=(-76.5, 39.3)
        )

        # Access coordinates
        longitude_latitude = f"{store.longitude}, {store.latitude}"
        expected = "-76.5, 39.3"
        self.assertEqual(longitude_latitude, expected)

    def test_example_usage_validation(self) -> None:
        """Test the validation example from models.rst."""
        # Create a placemark with coordinates
        store = Placemark(
            name="Capital Electric", address="123 Main St, Baltimore, MD", coordinates=(-76.5, 39.3)
        )

        # Validate the placemark
        is_valid = store.validate()
        self.assertTrue(is_valid)

    def test_complete_example_usage_workflow(self) -> None:
        """Test the complete example workflow from models.rst."""
        # Complete example from the documentation
        # Create a placemark with coordinates
        store = Placemark(
            name="Capital Electric", address="123 Main St, Baltimore, MD", coordinates=(-76.5, 39.3)
        )

        # Create a folder to organize placemarks
        stores_folder = Folder(name="Electric Stores")
        stores_folder.placemarks.add(store)

        # Access coordinates
        longitude_latitude = f"{store.longitude}, {store.latitude}"

        # Validate the placemark
        is_valid = store.validate()

        # Verify the complete workflow
        self.assertEqual(store.name, "Capital Electric")
        self.assertEqual(stores_folder.name, "Electric Stores")
        self.assertEqual(longitude_latitude, "-76.5, 39.3")
        self.assertTrue(is_valid)
        self.assertIn(store, stores_folder.placemarks.all())

    def test_imports_work_as_documented(self) -> None:
        """Test that the imports shown in models.rst work correctly."""
        # Test the import statement from the documentation
        from kmlorm import Point  # pylint: disable=import-outside-toplevel

        # Verify the imported classes are available and correct
        # These are instance properties, not class attributes
        placemark_instance = Placemark()
        folder_instance = Folder()
        point_instance = Point()

        self.assertTrue(hasattr(placemark_instance, "name"))
        self.assertTrue(hasattr(placemark_instance, "coordinates"))
        self.assertTrue(hasattr(folder_instance, "name"))
        self.assertTrue(hasattr(point_instance, "coordinates"))

    def test_placemark_attributes_exist(self) -> None:
        """Test that Placemark has the attributes used in documentation."""
        store = Placemark(name="Test Store", address="Test Address", coordinates=(-76.5, 39.3))

        # Verify documented attributes exist
        self.assertTrue(hasattr(store, "name"))
        self.assertTrue(hasattr(store, "address"))
        self.assertTrue(hasattr(store, "coordinates"))
        self.assertTrue(hasattr(store, "longitude"))
        self.assertTrue(hasattr(store, "latitude"))
        self.assertTrue(hasattr(store, "validate"))

    def test_folder_placemarks_manager_exists(self) -> None:
        """Test that Folder has the placemarks manager as documented."""
        folder = Folder(name="Test Folder")

        # Verify placemarks manager exists and has expected methods
        self.assertTrue(hasattr(folder, "placemarks"))
        self.assertTrue(hasattr(folder.placemarks, "add"))
        self.assertTrue(hasattr(folder.placemarks, "all"))

    def test_coordinate_tuple_assignment(self) -> None:
        """Test that coordinates can be assigned as tuple as shown in docs."""
        # Test coordinate assignment as shown in documentation
        store = Placemark(
            name="Capital Electric",
            address="123 Main St, Baltimore, MD",
            coordinates=(-76.5, 39.3),  # Tuple assignment
        )

        # Verify coordinates are properly stored
        self.assertIsNotNone(store.coordinates)
        assert store is not None
        if store.coordinates:
            self.assertEqual(store.coordinates.longitude, -76.5)  # pylint: disable=E1101
            self.assertEqual(store.coordinates.latitude, 39.3)  # pylint: disable=E1101
        self.assertEqual(store.longitude, -76.5)
        self.assertEqual(store.latitude, 39.3)

    def test_coordinate_property_access(self) -> None:
        """Test that coordinate properties work as documented."""
        store = Placemark(name="Test Store", coordinates=(-76.5, 39.3))

        # Test individual coordinate access as shown in documentation
        self.assertEqual(store.longitude, -76.5)
        self.assertEqual(store.latitude, 39.3)

        # Verify they are the correct types
        self.assertIsInstance(store.longitude, float)
        self.assertIsInstance(store.latitude, float)

    def test_validation_method_returns_boolean(self) -> None:
        """Test that validate() method returns boolean as used in docs."""
        store = Placemark(name="Test Store", coordinates=(-76.5, 39.3))

        # Test that validate returns a boolean
        result = store.validate()
        self.assertIsInstance(result, bool)
        self.assertTrue(result)  # Should be valid

    def test_folder_add_method_works(self) -> None:
        """Test that folder.placemarks.add() works as documented."""
        store = Placemark(name="Test Store", coordinates=(-76.5, 39.3))
        folder = Folder(name="Test Folder")

        # Test the add method as shown in documentation
        folder.placemarks.add(store)

        # Verify the placemark was added
        all_placemarks = folder.placemarks.all()
        self.assertIn(store, all_placemarks)

    def test_model_string_formatting_output(self) -> None:
        """Test that coordinate access works in string formatting context."""
        store = Placemark(name="Capital Electric", coordinates=(-76.5, 39.3))

        # Test the exact string formatting from documentation
        output = f"Store location: {store.longitude}, {store.latitude}"
        expected = "Store location: -76.5, 39.3"
        self.assertEqual(output, expected)

    def test_documentation_example_coordinate_values(self) -> None:
        """Test that the specific coordinate values from docs work correctly."""
        # Use exact coordinates from documentation example
        longitude = -76.5
        latitude = 39.3

        store = Placemark(name="Capital Electric", coordinates=(longitude, latitude))

        # Verify the exact values match
        self.assertEqual(store.longitude, longitude)
        self.assertEqual(store.latitude, latitude)
        self.assertIsNotNone(store.coordinates)
        if store.coordinates:
            self.assertEqual(store.coordinates.longitude, longitude)  # pylint: disable=E1101
            self.assertEqual(store.coordinates.latitude, latitude)  # pylint: disable=E1101

    def test_point_class_importable(self) -> None:
        """Test that Point class is importable as shown in documentation."""
        # Verify Point can be imported as shown in docs
        from kmlorm import Point  # pylint: disable=import-outside-toplevel

        # Verify Point class has expected attributes
        self.assertTrue(hasattr(Point, "coordinates"))

        # Test basic Point creation
        point = Point(coordinates=(-76.5, 39.3))
        self.assertIsNotNone(point.coordinates)
        if point.coordinates:
            self.assertEqual(point.coordinates.longitude, -76.5)
            self.assertEqual(point.coordinates.latitude, 39.3)


if __name__ == "__main__":
    unittest.main()
