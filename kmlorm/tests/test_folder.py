"""
Unit tests for the Folder model and its relationships with Placemark, Path, Polygon, and
    nested Folder elements.

TestFolder:
    - test_folder_basic_relationships:
        Verifies the creation and attachment of Placemark, Path, and Polygon instances to a Folder.
        Checks that related managers correctly track counts and parent relationships.
        Ensures the Folder's aggregation methods (all_elements, to_dict) function as expected.

    - test_folder_nested_folders_and_counts:
        Tests the creation of nested Folder structures and the correct management of child elements.
        Validates that element counts and string representations are accurate for nested Folders.
"""

from kmlorm.models.folder import Folder
from kmlorm.models.placemark import Placemark
from kmlorm.models.path import Path
from kmlorm.models.polygon import Polygon


class TestFolder:
    """
    Test suite for the Folder model, verifying its basic relationships, aggregation logic,
    and nested folder handling.

    Tests:
    - Creation and attachment of Placemark, Path, and Polygon elements to a Folder.
    - Correctness of related managers (add, count) and parent relationships.
    - Aggregation of all elements within a folder.
    - Serialization of Folder to dictionary including element counts.
    - Handling of nested folders and correct element counting across hierarchy.
    - String representation of Folder instances.
    """

    def test_folder_basic_relationships(self) -> None:
        """
        Test the basic relationships and aggregation logic of the Folder model.
        This test verifies:
        - Creation of a Folder instance.
        - Creation of Placemark, Path, and Polygon instances via their respective managers.
        - Attaching these elements to the Folder using related managers.
        - Correctness of related manager counts after attachment.
        - That the parent relationship is set when elements are added to the Folder.
        - The `all_elements` method aggregates all attached elements and their types.
        - The `to_dict` method includes correct counts for placemarks, paths, and polygons.
        """

        root = Folder(name="Root")

        # Create elements via class-level managers and attach them to the folder
        pm = Placemark.objects.create(name="P1")
        # Create Path and Polygon via their class managers
        p = Path.objects.create(coordinates=[(0.0, 0.0), (1.0, 1.0)])
        poly = Polygon.objects.create(outer_boundary=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)])

        # Attach to the folder using the related managers
        root.placemarks.add(pm)
        root.paths.add(p)
        root.polygons.add(poly)

        assert root.placemarks.count() == 1
        assert root.paths.count() == 1
        assert root.polygons.count() == 1

        # parent relationship set by RelatedManager.add
        assert pm.parent is root

        # all_elements aggregates managers for this folder
        elems = root.all_elements()
        assert any(isinstance(e, Placemark) for e in elems)
        assert any(isinstance(e, Path) for e in elems)
        assert any(isinstance(e, Polygon) for e in elems)

        # to_dict includes counts
        d = root.to_dict()
        assert d["placemark_count"] == 1
        assert d["path_count"] == 1
        assert d["polygon_count"] == 1

    def test_folder_nested_folders_and_counts(self) -> None:
        """
        Test the behavior of nested Folder objects and their related element counts.

        This test verifies:
        - Creation of a root Folder and a child Folder using the class-level manager.
        - Attaching a child Folder to the root Folder.
        - Creation and attachment of a Placemark to the child Folder.
        - Correctness of related object counts using the respective managers (folders, placemarks).
        - The `total_element_count` method accurately sums the counts of placemarks, folders,
            paths, and polygons for the root Folder.
        - The string representation of a Folder object starts with "Folder".
        """
        root = Folder(name="Root")

        # Create child folder via class-level manager and attach it
        child = Folder.objects.create(name="Child")
        root.folders.add(child)

        # add placemark to child via class-level manager then attach
        child_pm = Placemark.objects.create(name="ChildPlacemark")
        child.placemarks.add(child_pm)

        # Use the managers directly to inspect counts on the objects themselves
        assert root.folders.count() == 1
        assert child.placemarks.count() == 1

        # total_element_count sums counts across managers for this folder only
        assert (
            root.total_element_count()
            == root.placemarks.count()
            + root.folders.count()
            + root.paths.count()
            + root.polygons.count()
        )

        # string representation
        assert str(root).startswith("Folder")
