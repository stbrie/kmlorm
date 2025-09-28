"""
Unit tests for the extra functionality of KMLManager and RelatedManager classes in the
    kmlorm package.
Tested Features:
- Mapping of model classes to manager attribute names.
- Recursive collection of elements from nested Folder structures.
- Behavior of the `all(flatten=True)` method when no folders manager is set.
- Handling of duplicate elements in `get_or_create`.
- Wrappers for filtering, excluding, getting, ordering, and retrieving first/last elements.
- Geospatial query wrappers: `near`, `within_bounds`, `has_coordinates`, and `valid_coordinates`.
- Exception raising in `get` when no matching element is found.
- Contribution of manager to a class and correct attribute/model assignment.
- Requirement of model class for `create`.
- Creation, retrieval, counting, and existence checks for elements.
- Bulk creation of elements.
- Creation of related elements with parent assignment in RelatedManager.
Dependencies:
- pytest for exception testing.
- kmlorm core managers and model classes (Point, Folder, Placemark, Path, Polygon, MultiGeometry).
"""

# pylint: disable=duplicate-code
import pytest

from kmlorm.core.managers import KMLManager
from kmlorm.models.point import Point
from kmlorm.models.folder import Folder

# no custom exceptions needed here
from kmlorm.models.placemark import Placemark
from kmlorm.models.path import Path
from kmlorm.models.polygon import Polygon
from kmlorm.models.multigeometry import MultiGeometry
from kmlorm.core.managers import FolderRelatedManager, FolderManager
from kmlorm.core.managers import PointManager, PointRelatedManager


class TestManagersExtra:
    """
    TestManagersExtra contains unit tests for the KMLManager and RelatedManager classes,
    verifying their behavior for KML-like object management. The tests cover:

    - Mapping model classes to manager attribute names.
    - Recursive collection of elements from nested folder structures.
    - Flattening queries when no folders manager is set.
    - Handling of duplicate elements in get_or_create.
    - Wrappers for filter, exclude, get, first, last, and order_by methods.
    - Geospatial queries: near, within_bounds, and coordinate validation.
    - Exception raising when get is called on empty data.
    - Proper setup of manager attributes via contribute_to_class.
    - Enforcement of model class requirement for create.
    - Counting, existence checks, and get_or_create logic.
    - Bulk creation of elements.
    - RelatedManager's create method setting parent and adding elements.

    These tests ensure the correctness and robustness of the KMLManager API for managing geospatial
        and hierarchical KML data structures.
    """

    def test_get_manager_attribute_name_mapping(self) -> None:
        """
        Tests that the KMLManager correctly maps model classes to their corresponding
            manager attribute names.

        This test verifies that for each model class (Placemark, Folder, Path, Polygon,
            Point, MultiGeometry), the `_get_manager_attribute_name` method returns the
            expected attribute name. It also checks that when the model class is set to
            None, the method returns None.
        """
        # pylint: disable=protected-access
        mgr: KMLManager = KMLManager()
        mapping = {
            Placemark: "placemarks",
            Folder: "folders",
            Path: "paths",
            Polygon: "polygons",
            Point: "points",
            MultiGeometry: "multigeometries",
        }

        for cls, name in mapping.items():

            mgr._model_class = cls
            assert mgr._get_manager_attribute_name() == name

        mgr._model_class = None
        assert mgr._get_manager_attribute_name() is None

    def test_collect_folder_elements_recursive(self) -> None:
        """
        Test that the `_collect_folder_elements` method of `KMLManager` correctly traverses
        nested `Folder` structures recursively and collects all `Point` elements, including
        those in deeply nested folders.

        This test constructs a hierarchy of `Folder` objects, where the deepest folder
        contains a `Point` managed by a `KMLManager`. It verifies that the recursive
        collection method can find and return the deeply nested `Point` instance.
        """
        # pylint: disable=protected-access
        mgr: KMLManager = KMLManager()
        mgr._model_class = Point

        top = Folder(element_id="top")
        sub1 = Folder(element_id="s1")
        sub2 = Folder(element_id="s2")

        # deepest folder has a points manager with a point
        deep_point = Point(id="deep", coordinates=(3.0, 3.0))
        sub2_points: KMLManager = KMLManager()
        sub2_points._elements = [deep_point]
        setattr(sub2, "points", sub2_points)

        # wire folders managers
        sub1.folders = FolderRelatedManager(sub1, "folders")
        sub1.folders._elements = [sub2]
        top.folders = FolderRelatedManager(top, "folders")
        top.folders._elements = [sub1]

        # top-level folders manager
        folders_manager = FolderManager()
        folders_manager._elements = [top]
        mgr._folders_manager = folders_manager

        collected = mgr._collect_folder_elements()
        assert any(isinstance(x, Point) and x.id == "deep" for x in collected)

    def test_all_flatten_without_folders_manager_returns_queryset(self) -> None:
        """
        Test that calling `all(flatten=True)` on a `KMLManager` instance without a folders manager
        returns a queryset containing the same elements as `get_queryset()`.
        """
        # pylint: disable=protected-access
        mgr = PointManager()
        mgr._model_class = Point
        p = Point(id="p", coordinates=(0.0, 0.0))
        mgr.add(p)
        # no folders manager set
        res = mgr.all()
        assert res.elements == mgr.get_queryset().elements

    def test_get_or_create_handles_multiple_elements(self) -> None:
        """
        Test that `get_or_create` creates a new element when multiple existing elements
            match the query.

        This test ensures that if multiple elements with the same identifier exist in the manager,
        calling `get_or_create` with that identifier will not return one of the existing elements,
        but instead will create and return a new one. This behavior is expected because
        the underlying `get()` method would raise an error due to multiple matches, so
        `get_or_create` should handle this case by creating a new element.

        Asserts:
            - The `created` flag is True, indicating a new element was created.
            - At least one element with the specified id exists in the manager's elements.
        """
        # pylint: disable=protected-access
        mgr = PointManager()
        mgr._model_class = Point
        a = Point(id="dup", coordinates=(0.0, 0.0))
        b = Point(id="dup", coordinates=(1.0, 1.0))
        mgr.add(a)
        mgr.add(b)

        _e, created = mgr.get_or_create(id="dup")
        # since get() would raise multiple elements, get_or_create should create a new one
        assert created is True
        assert any(x.id == "dup" for x in mgr._elements)

    def test_filter_exclude_get_first_last_and_order_by_wrappers(self) -> None:
        """
        Tests the KMLManager's query-like methods for filtering, excluding, retrieving,
            and ordering elements.

        This test verifies the following behaviors:
        - `filter`: Returns elements matching the given criteria.
        - `exclude`: Returns elements not matching the given criteria.
        - `get`: Retrieves a single element matching the criteria.
        - `first`: Returns the first element in the manager.
        - `last`: Returns the last element in the manager.
        - `order_by`: Orders the elements by the specified attribute.

        The test uses two Point instances with different ids and ranks to check
            the correctness of each method.
        """
        from ..models.base import KMLElement  # pylint: disable=import-outside-toplevel

        mgr = PointManager()
        p1 = Point(id="p1", coordinates=(0.0, 0.0), rank=2)
        p2 = Point(id="p2", coordinates=(1.0, 1.0), rank=1)
        mgr._elements = [p1, p2]  # pylint: disable=protected-access

        f = mgr.filter(id__exact="p1")
        assert [e.id for e in f.elements] == ["p1"]

        ex = mgr.exclude(id__exact="p1")
        assert [e.id for e in ex.elements] == ["p2"]

        assert mgr.get(id__exact="p1").id == "p1"
        first = mgr.first()
        last = mgr.last()
        assert first is not None
        assert last is not None
        assert isinstance(first, KMLElement)
        assert isinstance(last, KMLElement)
        assert first.id == "p1"
        assert last.id == "p2"

        ob = mgr.order_by("rank")
        assert [e.id for e in ob.elements] == ["p2", "p1"]

    def test_geospatial_wrappers_near_within_has_valid(self) -> None:
        """
        Test the geospatial wrapper methods of KMLManager for correct behavior.

        This test verifies:
        - The `near` method correctly includes or excludes elements based on the specified radius.
        - The `within_bounds` method correctly identifies elements within given geographic bounds.
        - The `has_coordinates` and `valid_coordinates` methods correctly identify elements
            with valid coordinates.

        Scenarios:
        - A point at (0.0, 1.0) is excluded by a small radius (10 km) and included by a larger
            radius (200 km) from (0.0, 0.0).
        - The point is included when within specified bounds.
        - The point is returned by both `has_coordinates` and `valid_coordinates`.
        """
        # pylint: disable=protected-access
        mgr = PointManager()
        p = Point(id="near", coordinates=(0.0, 1.0))
        mgr._elements = [p]

        # near with small radius excludes, larger includes
        near_small = mgr.near(0.0, 0.0, radius_km=10)
        assert near_small.elements == []

        near_large = mgr.near(0.0, 0.0, radius_km=200)
        assert [e.id for e in near_large.elements] == ["near"]

        # within_bounds that includes the point
        wb = mgr.within_bounds(north=10, south=-10, east=10, west=-10)
        assert [e.id for e in wb.elements] == ["near"]

        assert mgr.has_coordinates().elements == [p]
        assert mgr.valid_coordinates().elements == [p]

    def test_get_raises_not_found_on_empty(self) -> None:
        """
        Test that the `get` method of `KMLManager` raises an exception when no
            matching object is found.

        This test verifies that calling `mgr.get` with a filter that does not match any objects
        results in an exception being raised, ensuring correct error handling for empty querysets.
        """
        mgr = PointManager()
        with pytest.raises(Exception):
            mgr.get(id__exact="nope")

    def test_contribute_to_class_sets_model_and_attribute(self) -> None:
        """
        Test that the `contribute_to_class` method of `KMLManager` correctly sets the manager
        as an attribute on the given model class and assigns the model class to the manager's
        `_model_class` attribute.

        This test verifies:
        - The manager is set as an attribute (e.g., 'objects') on the model class.
        - The attribute on the model class references the manager instance.
        - The manager's `_model_class` attribute is set to the model class.
        """

        # pylint: disable=too-few-public-methods
        class Dummy:
            """
            A placeholder class used for testing or demonstration purposes.

            This class does not implement any functionality.
            """

            objects: KMLManager

        mgr = PointManager()
        mgr.contribute_to_class(Dummy, "objects")
        assert hasattr(Dummy, "objects")
        assert Dummy.objects is mgr
        assert getattr(mgr, "_model_class") is Dummy

    def test_create_and_get_or_create_and_count_exists(self) -> None:
        """
        Test the KMLManager's create, get_or_create, count, and exists methods.

        This test verifies the following behaviors:
        - The manager is initially empty, with count() returning 0 and exists() returning False.
        - The create() method adds a new Point instance, increasing the count.
        - The get_or_create() method returns the existing element and created=False
            if the element exists.
        - The get_or_create() method creates a new element and returns created=True
            if the element does not exist.
        - The internal elements list contains the newly created element.
        """
        # pylint: disable=protected-access
        mgr = PointManager()
        mgr._model_class = Point
        # initially empty
        assert mgr.count() == 0
        assert not mgr.exists()

        p = mgr.create(id="p1", coordinates=(0.0, 0.0))
        assert isinstance(p, Point)
        assert mgr.count() == 1

        # get_or_create should return existing element and created False
        e, created = mgr.get_or_create(id="p1")
        assert created is False
        assert e is p

        # get_or_create for new id should create
        _e2, created2 = mgr.get_or_create(id="p2")
        assert created2 is True
        assert any(x.id == "p2" for x in mgr._elements)

    def test_bulk_create_appends_and_returns_list(self) -> None:
        """
        Test that the `bulk_create` method of `KMLManager` appends multiple elements to the manager,
        returns the list of created elements, updates the count accordingly, and ensures
        the elements are present in the manager's internal storage.
        """
        mgr = PointManager()
        a = Point(id="ba", coordinates=(0.0, 0.0))
        b = Point(id="bb", coordinates=(1.0, 1.0))

        out = mgr.bulk_create([a, b])
        assert out == [a, b]
        assert mgr.count() == 2
        assert a in mgr._elements and b in mgr._elements  # pylint: disable=protected-access

    def test_related_manager_create_sets_parent_and_returns_element(self) -> None:
        """
        Tests that the RelatedManager.create method:
        - Instantiates a new related element of the correct model class.
        - Sets the parent attribute of the new element to the manager's parent.
        - Returns the newly created element.
        - Adds the new element to the manager's internal list of related elements.
        """
        # pylint: disable=protected-access
        parent = Folder(element_id="pf2", name="Parent2")
        rel = PointRelatedManager(parent, "points")
        # RelatedManager.create relies on _model_class being set on the manager
        rel._model_class = Point

        new = rel.create(id="cr1", coordinates=(2.0, 2.0))
        assert isinstance(new, Point)
        assert new.parent is parent
        # ensure it's been added to the related manager's internal list
        assert any(x.id == "cr1" for x in rel._elements)
