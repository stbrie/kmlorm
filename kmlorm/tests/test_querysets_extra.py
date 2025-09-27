# mypy: disable-error-code=list-item
# mypy: disable-error-code=arg-type
# mypy: disable-error-code=assignment
# pylint: disable=import-outside-toplevel
# pylint: disable=protected-access
# pyright: reportGeneralTypeIssues=false
# pyright: reportArgumentType=false
# pyright: reportAttributeAccessIssue=false
"""
Test suite for the KMLQuerySet extra functionality.

This module contains a comprehensive set of unit tests for the `KMLQuerySet` class,
covering advanced querying, filtering, ordering, geospatial operations, and edge cases.
The tests ensure correct behavior for nested field lookups, missing attributes, ordering,
coordinate parsing and validation, bounding box and proximity queries, distinctness,
values extraction, string and comparison lookups, and error handling.

Tested features include:
- Nested and missing field value retrieval.
- Ordering by fields, including error handling for missing fields.
- Coordinate parsing, validation, and error logging.
- Filtering elements with valid coordinates and within geographic bounds, including
    antimeridian wraparound.
- Proximity queries using haversine distance.
- Handling of empty querysets and missing elements.
- Support for various lookup types: regex, iregex, in, range, isnull, startswith,
    endswith, contains, icontains, iexact, comparison operators.
- Distinctness and order preservation.
- Extraction of values and values_list, including flat and non-flat modes.
- Exclusion and combination of filters.
- Handling of elements with different coordinate attribute names.
- Robustness against type errors and unsupported lookups.
- Ensuring correct behavior for __getitem__, __repr__, __bool__, and property setters.
- Edge cases for empty or falsy coordinates and multiple element retrieval.

Fixtures and monkeypatching are used to simulate various behaviors and error conditions.
"""
# pylint: disable=too-few-public-methods, too-many-public-methods
import logging
from types import SimpleNamespace
from typing import Any, cast
import pytest
from kmlorm.core.querysets import KMLQuerySet
from kmlorm.core.exceptions import KMLQueryError, KMLInvalidCoordinates, KMLElementNotFound
from kmlorm.models.base import KMLElement
from kmlorm.models.placemark import Placemark
from kmlorm.models.point import Point, Coordinate


class TestKMLQuerySetExtra:
    """
    Test suite for the KMLQuerySet class, covering a wide range of query, filtering, ordering,
    and geospatial operations. This class contains tests for:

    - Nested and missing attribute lookups.
    - Ordering by fields, including error handling for missing fields.
    - Parsing and validation of point coordinates, including error logging and filtering
        out-of-range values.
    - Geospatial queries such as within_bounds (including antimeridian wraparound) and near
        (haversine distance).
    - Handling of invalid bounds and coordinates.
    - Filtering and exclusion using various lookup types (exact, regex, iregex, in, range,
        isnull, comparison, etc.).
    - Distinct and ordering operations, including stability and preservation of order flags.
    - Values and values_list extraction, including flat and non-flat results, and handling
        of missing fields.
    - Handling of elements with missing or multiple attributes.
    - String-based lookups (startswith, endswith, contains, icontains, iexact, etc.).
    - Edge cases such as empty querysets, missing attributes, and unsupported lookups.
    - Ensuring correct behavior for __getitem__, __repr__, __bool__, and property setters.
    - Ensuring correct exception types and attributes are raised for get() and multiple
        element queries.
    - Coverage for coordinate attribute variations (coord, coordinate).
    - Ensuring correct handling of falsy IDs in distinct queries.
    - Ensuring correct handling of empty or invalid coordinate sequences.

    Each test is designed to exercise a specific aspect of the KMLQuerySet API, including both
    expected functionality and error conditions, to ensure robust and predictable behavior.
    """

    class _E:
        """
        A simple helper class that initializes its attributes from keyword arguments.

        Attributes are dynamically set based on the provided keyword arguments during instantiation.

        Example:
            e = _E(foo=1, bar='baz')
            print(e.foo)  # Output: 1
            print(e.bar)  # Output: 'baz'
        """

        coordinates: Any
        id: Any
        name: Any
        rank: Any
        value: Any
        tag: Any

        def __init__(self, **kwargs: Any) -> None:
            """
            Initializes the object by setting attributes based on provided keyword arguments.

            Args:
                **kwargs: Arbitrary keyword arguments where each key-value pair is set as an
                    attribute on the instance.
            """
            for k, v in kwargs.items():
                setattr(self, k, v)

    def test_get_field_value_nested_and_missing(self) -> None:
        """
        Tests the `_get_field_value` method for handling nested attribute lookups and
            missing attributes.

        - Verifies that a nested attribute (e.g., "nested.value") can be accessed correctly.
        - Ensures that attempting to access a missing nested attribute (e.g., "nested.missing")
            raises an AttributeError.
        """
        # pylint: disable=protected-access
        coord = Coordinate(longitude=42, latitude=1)
        point = Point(coordinates=coord)
        e = Placemark(element_id=1, point=point)

        qs: KMLQuerySet = KMLQuerySet([e])
        # nested lookup should work
        assert qs._get_field_value(e, "point.coordinates.longitude") == 42

        # missing attribute raises AttributeError
        with pytest.raises(AttributeError):
            qs._get_field_value(e, "point.coordinates.missing")

    def test_order_by_raises_on_missing_field(self) -> None:
        """
        Test that ordering a KMLQuerySet by a non-existent field raises a KMLQueryError.

        This test creates an instance of the model, adds it to a KMLQuerySet, and attempts to order
        the queryset by an attribute that does not exist. It asserts that the appropriate exception
        (KMLQueryError) is raised in this scenario.
        """
        a = Point(element_id=1, rank=1)
        qs = KMLQuerySet([a])
        # ordering by a missing attribute should raise KMLQueryError
        with pytest.raises(KMLQueryError):
            qs.order_by("missing")

    def test_point_coords_logs_and_returns_none_on_parse_error(
        self, monkeypatch: Any, caplog: Any
    ) -> None:
        """
        Test that KMLQuerySet._point_coords logs a warning and returns None when
            Coordinate.from_any raises a ValueError.

        This test monkeypatches the Coordinate.from_any method to always raise a
            ValueError, simulating a parse error.
        It then verifies that:
        - The method returns None when parsing fails.
        - A warning message containing "Failed to parse coordinates" is logged.
        """

        # pylint: disable=import-outside-toplevel
        # pylint: disable=protected-access
        # Create a non-Point element with coordinates to test the from_any path
        e = self._E(id="x", coordinates=(10.0, 10.0))
        qs: KMLQuerySet = KMLQuerySet([e])

        # Monkeypatch Coordinate.from_any to raise ValueError for this test
        # pylint: disable=reimported
        from kmlorm.models.point import Coordinate as RealCoord

        def fake_from_any(val: Any) -> None:
            raise ValueError("bad coords")

        monkeypatch.setattr(RealCoord, "from_any", staticmethod(fake_from_any))

        caplog.set_level(logging.WARNING)
        coords = qs._point_coords(e)
        assert coords is None
        # ensure a warning was logged
        assert any("Failed to parse coordinates" in r.message for r in caplog.records)

    def test_valid_coordinates_filters_out_of_range(self, monkeypatch: Any) -> None:
        """
        Tests that the `valid_coordinates` method of `KMLQuerySet` correctly
        filters out elements with out-of-range coordinates.

        This test creates two elements: one with invalid coordinates (longitude and
        latitude out of valid range) and one with valid coordinates. It monkeypatches
        the `Coordinate.from_any` method to return the appropriate mocked coordinate
        objects. The test asserts that only the element with valid coordinates remains after
        calling `valid_coordinates`.
        """
        from ..models.placemark import Placemark as _Placemark

        bad = cast(_Placemark, self._E(id=1, coordinates=(200.0, 100.0)))
        good = cast(_Placemark, self._E(id=2, coordinates=(10.0, 10.0)))
        qs = KMLQuerySet([bad, good])
        # pylint: disable=reimported
        from kmlorm.models.point import Coordinate as RealCoord

        def fake_from_any(val: Any) -> SimpleNamespace:
            if val == bad.coordinates:
                return SimpleNamespace(longitude=200.0, latitude=100.0)
            return SimpleNamespace(longitude=10.0, latitude=10.0)

        monkeypatch.setattr(RealCoord, "from_any", staticmethod(fake_from_any))

        res = qs.valid_coordinates()
        # only the good element should remain
        assert [cast(int, e.id) for e in res.elements] == [2]

    def test_within_bounds_wraparound(self, monkeypatch: Any) -> None:
        """
        Test that the `within_bounds` method correctly handles bounding boxes that cross
            the antimeridian.

        This test creates three elements with longitudes near the antimeridian and verifies
        that a bounding box defined with west > east (crossing the antimeridian) includes
        only the elements on either side of the antimeridian and excludes those outside the bounds.

        Steps:
            - Mocks the Coordinate.from_any method to return a simple namespace for testing.
            - Defines a bounding box with west=170 and east=-170 (crossing the antimeridian).
            - Asserts that only elements with longitudes 179.0 and -179.0 are included, and
                the element at 0.0 is excluded.
        """
        a = Point(element_id=1, coordinates=(179.0, 0.0))
        b = Point(element_id=2, coordinates=(-179.0, 0.0))
        c = Point(element_id=3, coordinates=(0.0, 0.0))
        qs = KMLQuerySet([a, b, c])
        # pylint: disable=reimported
        from kmlorm.models.point import Coordinate as RealCoord

        def fake_from_any(val: Any) -> SimpleNamespace:
            """
            Converts a tuple containing longitude and latitude values into a SimpleNamespace object.

            Args:
                val (Any): A tuple or iterable containing two elements: longitude and latitude.

            Returns:
                SimpleNamespace: An object with 'longitude' and 'latitude' attributes set
                    from the input.

            Raises:
                ValueError: If 'val' does not contain exactly two elements.
            """
            lon, lat = val
            return SimpleNamespace(longitude=lon, latitude=lat)

        monkeypatch.setattr(RealCoord, "from_any", staticmethod(fake_from_any))

        # bounds that cross: west=170, east=-170 should include a and b but not c
        res = qs.within_bounds(north=10, south=-10, east=-170, west=170)
        assert set(cast(int, e.id) for e in res.elements) == {1, 2}

    def test_within_bounds_invalid_raises(self) -> None:
        """
        Tests that the `within_bounds` method of `KMLQuerySet` raises a `KMLInvalidCoordinates`
        exception when provided with invalid latitude bounds (north and south values outside
        the valid range).
        """
        qs: KMLQuerySet = KMLQuerySet([])
        # invalid lat bounds
        with pytest.raises(KMLInvalidCoordinates):
            qs.within_bounds(north=-100, south=-200, east=10, west=-10)

    def test_near_and_haversine(self, monkeypatch: Any) -> None:
        """
        Tests the 'near' and 'haversine' functionality of the KMLQuerySet.

        This test verifies that a point located approximately 111 km north of the origin (0,0)
        is correctly identified as being within a 120 km radius using the 'near' method.
        It uses monkeypatching to replace the 'from_any' method of the Coordinate class
        with a fake implementation for testing purposes.

        Args:
            monkeypatch (Any): pytest's monkeypatch fixture for patching objects.

        Asserts:
            The point with id "1" is included in the queryset when searching within 120 km of (0,0).
        """
        # center at (0,0); element at ~111 km north (1 degree latitude)
        a = Point(element_id=1, coordinates=(0.0, 1.0))
        qs = KMLQuerySet([a])
        # pylint: disable=reimported
        from kmlorm.models.point import Coordinate as RealCoord

        def fake_from_any(val: Any) -> SimpleNamespace:
            lon, lat = val
            return SimpleNamespace(longitude=lon, latitude=lat)

        monkeypatch.setattr(RealCoord, "from_any", staticmethod(fake_from_any))

        # near within 120 km should include the point
        near = qs.near(longitude=0.0, latitude=0.0, radius_km=120)
        assert [cast(int, e.id) for e in near.elements] == [1]

    def test_order_by_no_fields_and_get_empty(self) -> None:
        """
        Tests the behavior of KMLQuerySet's order_by and get methods:
        - Verifies that calling order_by with no fields returns a new
            KMLQuerySet instance containing the same elements as the original,
            but as a different object.
        - Ensures that calling get on an empty KMLQuerySet raises an exception
            with an 'element_type' attribute set to 'KMLElement'.
        """
        a = Point(element_id=1, rank=1)
        qs = KMLQuerySet([a])
        # order_by with no fields should return a copy (all)
        all_qs = qs.order_by()
        assert isinstance(all_qs, KMLQuerySet)
        assert all_qs.elements == qs.elements
        assert all_qs is not qs

        # get() on empty queryset should raise with element_type 'KMLElement'
        empty: KMLQuerySet = KMLQuerySet([])
        with pytest.raises(KMLElementNotFound) as excinfo:
            empty.get(name__exact="x")
        # ensure the raised exception is KMLElementNotFound and has element_type attr
        exc = excinfo.value
        assert hasattr(exc, "element_type")
        assert exc.element_type == "KMLElement"

    def test_near_no_radius_returns_all(self, monkeypatch: Any) -> None:
        """
        Test that the `near` method returns all elements when no radius is specified.

        This test verifies that when `radius_km` is set to `None`, the `near` method
        of `KMLQuerySet` returns all elements in the queryset, regardless of their
        coordinates. It uses monkeypatching to mock the coordinate conversion and
        checks that the result contains the expected element.
        """
        a = Point(element_id=1, coordinates=(0.0, 0.0))
        qs = KMLQuerySet([a])

        # pylint: disable=reimported
        from kmlorm.models.point import Coordinate as RealCoord

        monkeypatch.setattr(
            RealCoord,
            "from_any",
            staticmethod(lambda v: SimpleNamespace(longitude=0.0, latitude=0.0)),
        )

        res = qs.near(longitude=0.0, latitude=0.0, radius_km=None)
        assert isinstance(res, KMLQuerySet)
        assert [cast(int, e.id) for e in res.elements] == [1]

    def test_within_bounds_invalid_longitude_raises(self) -> None:
        """
        Test that KMLQuerySet.within_bounds raises an Exception when the 'west' longitude
        parameter is out of the valid range, even if 'east' is valid. Specifically, this
        test passes an invalid 'west' value (200) and expects an exception to be raised.
        """
        qs: KMLQuerySet = KMLQuerySet([])
        # west out of range but east valid should raise per the odd condition in code
        with pytest.raises(Exception):
            qs.within_bounds(north=10, south=-10, east=0, west=200)

    def test_has_coordinates_with_coordinates_attrs(self, monkeypatch: Any) -> None:
        """
        Test that the `has_coordinates` method of `KMLQuerySet` correctly identifies elements
        with 'coordinates' attributes, using a monkeypatched `Coordinate.from_any`
        to simulate coordinate extraction.

        Args:
            monkeypatch (Any): pytest fixture for monkeypatching.

        Asserts:
            The resulting queryset contains elements with ids "1" and "2", indicating
            'coordinates' attributes are recognized as valid coordinates.
        """
        # Use _E elements with coordinates attribute (the only one supported by _point_coords)
        a = self._E(id=1, coordinates=(1.0, 2.0))
        b = self._E(id=2, coordinates=(3.0, 4.0))
        qs: KMLQuerySet = KMLQuerySet([a, b])

        # pylint: disable=reimported
        from kmlorm.models.point import Coordinate as RealCoord

        monkeypatch.setattr(
            RealCoord,
            "from_any",
            staticmethod(lambda v: SimpleNamespace(longitude=v[0], latitude=v[1])),
        )
        res = qs.has_coordinates()
        assert set(cast(int, e.id) for e in res.elements) == {1, 2}

    def test_point_coords_with_point_instance_and_haversine_zero(self) -> None:
        """
        Tests that the _point_coords method correctly returns the coordinates of a Point instance,
        and verifies that the _haversine_distance method returns approximately zero when calculating
        the distance between identical coordinates.
        """
        # create a real Point instance with valid coordinates to exercise direct path
        # pylint: disable=reimported,redefined-outer-name
        from kmlorm.models.point import Point

        p = Point(id="p", coordinates=(10.0, 10.0))
        qs = KMLQuerySet([p])
        coords = qs._point_coords(p)
        assert coords is p.coordinates

        # haversine distance between same points is ~0
        assert coords is not None  # Ensure coords is not None for type checking
        d = qs._haversine_distance(coords, coords)
        assert abs(d) < 1e-6

    def test_apply_lookup_regex_and_membership(self) -> None:
        """
        Tests the application of various lookup filters on a queryset, including:
        - `regex`: Filters elements where the field matches a case-sensitive regular expression.
        - `iregex`: Filters elements where the field matches a case-insensitive regular expression.
        - `in`: Filters elements where the field's value is in a given list.
        - `range`: Filters elements where the field's value falls within a specified range.

        Asserts that the correct elements are returned for each filter type.
        """
        # cover regex, iregex, in and range
        a = Point(element_id=1, name="Abc", rank=5)
        b = Point(element_id=2, name="xyz", rank=10)
        qs = KMLQuerySet([a, b])

        # regex (case-sensitive)
        r = qs.filter(name__regex=r"^A")
        assert [cast(int, e.id) for e in r.elements] == [1]

        # iregex (case-insensitive)
        ir = qs.filter(name__iregex=r"^a")
        assert [cast(int, e.id) for e in ir.elements] == [1]

        # in membership
        inn = qs.filter(rank__in=[5, 99])
        assert [cast(int, e.id) for e in inn.elements] == [1]

        # range
        rng = qs.filter(rank__range=(6, 15))
        assert [cast(int, e.id) for e in rng.elements] == [2]

    def test_getitem_type_error_and_repr_bool(self) -> None:
        """
        Tests the behavior of KMLQuerySet for invalid indexing, string representation,
        and boolean evaluation.

        - Verifies that accessing KMLQuerySet with a non-integer key raises a TypeError.
        - Checks that the string representation (`repr`) of a non-empty KMLQuerySet includes
            the correct element count.
        - Asserts that a non-empty KMLQuerySet evaluates to True in a boolean context.
        - Checks that the string representation (`repr`) of an empty KMLQuerySet includes
            the correct element count.
        - Asserts that an empty KMLQuerySet evaluates to False in a boolean context.
        """
        a = Point(element_id=1)
        qs = KMLQuerySet([a])
        with pytest.raises(TypeError):
            _ = qs["bad"]  # type: ignore

        # repr and bool
        assert "1 elements" in repr(qs)
        assert bool(qs) is True

        empty: KMLQuerySet = KMLQuerySet([])
        assert "0 elements" in repr(empty)
        assert bool(empty) is False

    def test_elements_setter_and_order_properties(self) -> None:
        """
        Tests the setter and order-related properties of the KMLQuerySet class.

        This test verifies the following behaviors:
        - Assigning None to the `elements` property does not alter its value.
        - Assigning a new list to the `elements` property updates its value accordingly.
        - Setting the `is_ordered` property to True correctly updates its state.
        - Assigning a list to the `order_by_fields` property updates its value as expected.
        """
        # pylint: disable=reimported,redefined-outer-name
        from kmlorm.models.point import Point

        # Create real KMLElement instances
        point_a = Point(element_id=1, name="Point A")
        point_b = Point(element_id=2, name="Point B")

        qs = KMLQuerySet([point_a])
        # setting None should do nothing
        old = qs.elements
        qs.elements = None
        assert qs.elements == old

        qs.elements = [point_b]
        assert qs.elements == [point_b]

        qs.is_ordered = True
        assert qs.is_ordered is True
        qs.order_by_fields = ["rank"]
        assert qs.order_by_fields == ["rank"]

    def test_elements_setter_type_validation(self) -> None:
        """
        Tests that the elements setter properly validates element types.

        This test verifies that:
        - Assigning valid KMLElement instances works correctly.
        - Assigning non-KMLElement objects raises TypeError.
        """

        # pylint: disable=reimported,redefined-outer-name
        from kmlorm.models.point import Point

        # Create a valid KMLElement and an invalid object
        valid_point = Point(element_id=1, name="Valid Point")
        invalid_object = self._E(id=1, name="Not a KMLElement")

        qs: KMLQuerySet = KMLQuerySet([])

        # Valid assignment should work
        qs.elements = [valid_point]
        assert len(qs.elements) == 1
        assert qs.elements[0] == valid_point

        # Invalid assignment should raise TypeError
        with pytest.raises(
            TypeError, match="Elements assignment must contain only KMLElement instances"
        ):
            qs.elements = [invalid_object]

        # Mixed valid/invalid should also raise TypeError
        with pytest.raises(
            TypeError, match="Elements assignment must contain only KMLElement instances"
        ):
            qs.elements = [valid_point, invalid_object]

    def test_values_missing_field_and_values_list_flat(self) -> None:
        """
        Tests the behavior of the KMLQuerySet 'values' and 'values_list' methods.

        This test verifies two scenarios:
        1. When querying for a missing field using 'values', the result should be a list
            containing a dictionary with the missing field set to None.
        2. When using 'values_list' with the 'flat' parameter set to True for an
            existing field, the result should be a flat list of the field's values.
        """
        a = Point(element_id=1, name="A")
        qs = KMLQuerySet([a])
        vals = qs.values("missing")
        assert vals == [{"missing": None}]

        vflat = qs.values_list("id", flat=True)
        assert vflat == [1]

    def test_isnull_lookup_and_matches_filters_missing_attribute(self) -> None:
        """
        Tests the behavior of the KMLQuerySet filter method when handling:
        1. The `isnull` lookup on an attribute that is explicitly set to None
            versus a non-None value.
        2. Filtering on a missing attribute, which should result in no matches
            rather than raising an error.
        """
        a = Point(element_id=1, maybe=None)
        b = Point(element_id=2, maybe=0)
        qs = KMLQuerySet([a, b])
        res = qs.filter(maybe__isnull=True)
        assert [cast(int, e.id) for e in res.elements] == [1]

        # missing attribute in filter should simply not match
        res2 = qs.filter(nope__exact=1)
        assert res2.elements == []

    def test_near_skips_on_point_coords_error(self, monkeypatch: Any) -> None:
        """
        Test that the `near` method of `KMLQuerySet` skips elements when `_point_coords`
        raises a TypeError.

        This test uses monkeypatching to force `_point_coords` to raise a TypeError,
        simulating a failure to extract coordinates. It verifies that the `near` method
        does not include such elements in its results, and the resulting queryset is empty.
        """
        a = Point(element_id=1, coordinates=(0.0, 0.0))
        qs = KMLQuerySet([a])

        def fake_point_coords(self: Any, elem: Any) -> None:
            raise TypeError("boom")

        monkeypatch.setattr(KMLQuerySet, "_point_coords", fake_point_coords)
        near = qs.near(longitude=0.0, latitude=0.0, radius_km=100)
        assert near.elements == []

    def test_has_coordinates_none(self) -> None:
        """
        Test that the `has_coordinates` method returns an empty list when the queryset
        contains an element with no coordinates.
        """
        a = Point(element_id=1)
        qs = KMLQuerySet([a])
        assert qs.has_coordinates().elements == []

    def test_apply_lookup_unsupported_raises_and_string_ops(self) -> None:
        """
        Tests the behavior of KMLQuerySet's _apply_lookup method for unsupported
        lookups and string operations.

        This test verifies that:
        - An exception is raised when an unsupported lookup type is provided to _apply_lookup.
        - The 'startswith' and 'endswith' string lookups correctly filter elements in the queryset.
        """
        qs: KMLQuerySet = KMLQuerySet([])
        with pytest.raises(Exception):
            qs._apply_lookup("x", "unknown", "y")

        # startswith/endswith
        a = Point(element_id=1, name="startend")
        qs2 = KMLQuerySet([a])
        assert qs2.filter(name__startswith="start").elements == [a]
        assert qs2.filter(name__endswith="end").elements == [a]

    def test_haversine_direct(self) -> None:
        """
        Tests the direct calculation of the Haversine distance between two
        points using the `_haversine_distance` method of `KMLQuerySet`.

        Verifies that the computed distance between two points with the
        same longitude but different latitudes is greater than zero.
        """
        from ..models.point import Coordinate as _Coordinate

        qs: KMLQuerySet = KMLQuerySet([])
        p = _Coordinate(longitude=0.0, latitude=0.0)
        q = _Coordinate(longitude=0.0, latitude=1.0)
        d = qs._haversine_distance(p, q)
        assert d > 0

    def test_comparison_lookups_and_isnull_false(self) -> None:
        """
        Tests comparison lookups and the 'isnull=False' filter on a KMLQuerySet.

        This test verifies that:
        - Filtering with 'value__gt', 'value__gte', 'value__lt', and 'value__lte'
            returns the correct elements based on the 'value' attribute.
        - Filtering with 'value__isnull=False' returns all elements where 'value'
            is not None.
        """
        a = Point(element_id=1, value=5)
        b = Point(element_id=2, value=10)
        qs = KMLQuerySet([a, b])
        assert [cast(int, e.id) for e in qs.filter(value__gt=6).elements] == [2]
        assert [cast(int, e.id) for e in qs.filter(value__gte=5).elements] == [1, 2]
        assert [cast(int, e.id) for e in qs.filter(value__lt=10).elements] == [1]
        assert [cast(int, e.id) for e in qs.filter(value__lte=5).elements] == [1]

        # isnull with a non-None value should return True for False filter
        res = qs.filter(value__isnull=False)
        assert [cast(int, e.id) for e in res.elements] == [1, 2]

    def test_distinct_uses_object_id_when_id_falsy(self) -> None:
        """
        Tests that the `distinct` method uses the object's identity (object id) to
        determine uniqueness when the object's `id` attribute is falsy (e.g., None),
        ensuring that duplicate references to the same object are not counted as
        distinct elements in the queryset.
        """
        obj = Point(element_id=None, name="dup")
        qs = KMLQuerySet([obj, obj])
        distinct = qs.distinct()
        assert len(distinct.elements) == 1

    def test_order_by_multiple_fields_stable(self) -> None:
        """
        Tests that ordering a queryset by multiple fields is stable and correctly breaks ties.
        Specifically, verifies that when the primary field ('a') has duplicate values,
        the secondary field ('b') is used to determine the order among those duplicates.
        """
        # primary 'a' ties, secondary 'b' breaks ties
        x1 = Point(element_id=1, a=1, b=2)
        x2 = Point(element_id=2, a=1, b=1)
        x3 = Point(element_id=3, a=2, b=0)
        qs = KMLQuerySet([x1, x2, x3])
        res = qs.order_by("a", "b")
        assert [cast(int, e.id) for e in res.elements] == [2, 1, 3]

    def test_values_list_nonflat_and_exclude_and_filter_combo(self) -> None:
        """
        Tests the combination of `values_list`, `exclude`, and `filter` methods on the KMLQuerySet.

        - Verifies that `values_list` with multiple fields returns tuples.
        - Checks that `exclude` removes elements matching the specified condition.
        - Ensures that `filter` with multiple lookup arguments applies AND semantics and
            returns only matching elements.
        """
        a = Point(element_id=1, name="A", tag="x")
        b = Point(element_id=2, name="B", tag="y")
        qs = KMLQuerySet([a, b])
        v = qs.values_list("id", "name")
        assert isinstance(v[0], tuple)

        # exclude should remove matching elements
        out = qs.exclude(tag__exact="x")
        assert [cast(int, e.id) for e in out.elements] == [2]

        # filter with multiple lookups (AND semantics)
        both = qs.filter(tag__exact="y", name__exact="B")
        assert [cast(int, e.id) for e in both.elements] == [2]

    def test_string_lookups_and_values_all_fields(self) -> None:
        """
        Tests various string lookup filters and the `values()` method on the `KMLQuerySet` class.

        This test covers:
        - Case-insensitive string lookups: `istartswith`, `iexact`, `icontains`, `iendswith`.
        - Case-sensitive string lookups: `contains`.
        - Membership lookup: `in`.
        - The behavior of `values()` with no specified fields, ensuring it calls `to_dict()`
            on elements.

        Assertions verify that the correct elements are returned for each filter and that
            `values()` returns a list of dictionaries.
        """

        class WithDict:
            """
            A simple class that initializes its attributes from keyword arguments and provides
            a method to convert its attributes to a dictionary.

            Attributes:
                None explicitly defined. All attributes are set dynamically via keyword arguments.

            Methods:
                __init__(**kwargs):
                    Initializes the instance with attributes set from the provided keyword
                        arguments.

                to_dict() -> None:
                    Returns a dictionary representation of the instance's attributes.
            """

            def __init__(self, **kwargs: Any) -> None:
                for k, v in kwargs.items():
                    setattr(self, k, v)

            def to_dict(self) -> dict[Any, Any]:
                """
                Converts the object's instance attributes into a dictionary.

                Returns:
                    dict[Any, Any]: A dictionary containing all attribute names and their
                        corresponding values from the instance.
                """
                return dict(self.__dict__)

        wa = WithDict(id=1, name="HelloWorld")
        wb = WithDict(id=2, name="hello")
        a = cast(KMLElement, wa)
        b = cast(KMLElement, wb)
        qs = KMLQuerySet([a, b])

        # both 'HelloWorld' and 'hello' start with 'he' (case-insensitive)
        assert [cast(int, e.id) for e in qs.filter(name__istartswith="he").elements] == [1, 2]

        assert [cast(int, e.id) for e in qs.filter(name__iexact="hello").elements] == [2]
        assert [cast(int, e.id) for e in qs.filter(name__contains="World").elements] == [1]
        assert [cast(int, e.id) for e in qs.filter(name__icontains="world").elements] == [1]
        assert [cast(int, e.id) for e in qs.filter(name__iendswith="ld").elements] == [1]

        # 'in' membership where field_value in filter_value
        x = Point(element_id=3, tag="x")
        qs2 = KMLQuerySet([x])
        assert [cast(int, e.id) for e in qs2.filter(tag__in=["x", "y"]).elements] == [3]

        # values() with no fields should call to_dict on elements
        vals = qs.values()
        assert isinstance(vals, list) and isinstance(vals[0], dict)

    def test_point_coords_type_error_and_numeric_iexact(self, monkeypatch: Any) -> None:
        """
        Tests two behaviors in KMLQuerySet:
        1. Ensures that if Coordinate.from_any raises a TypeError when called by
            _point_coords, the method returns None.
        2. Verifies that the 'iexact' filter works correctly for numeric fields by
            coercing the value to a string for comparison.
        """
        # Ensure Coordinate.from_any raising TypeError is handled and returns None
        # Use _E element instead of Point to test the from_any path
        e = self._E(id=1, coordinates=(1.0, 2.0))
        qs: KMLQuerySet = KMLQuerySet([e])

        from kmlorm.models.point import Coordinate as RealCoord  # pylint: disable=reimported

        def fake_from_any(val: Any) -> None:
            raise TypeError("bad type")

        monkeypatch.setattr(RealCoord, "from_any", staticmethod(fake_from_any))
        assert qs._point_coords(e) is None

        # numeric iexact should work (coerce to string in implementation)
        a = Point(element_id=2, num=42)
        qs2 = KMLQuerySet([a])
        assert qs2.filter(num__iexact=42).elements == [a]

    def test_values_list_flat_requires_one_field(self) -> None:
        """
        Test that calling `values_list` with `flat=True` and more than one field raises
        a ValueError.

        This test ensures that when the `flat` argument is set to True, only a single
            field can be specified.
        If more than one field is provided, a ValueError should be raised, as returning
            a flat list of tuples with multiple fields is not supported.
        """
        a = Point(element_id=1, name="A")
        qs = KMLQuerySet([a])
        # flat=True with more than one field should raise
        with pytest.raises(ValueError):
            qs.values_list("id", "name", flat=True)

    def test_distinct_preserves_order_flags(self) -> None:
        """
        Test that calling `distinct()` on a `KMLQuerySet` instance
        preserves the `is_ordered` flag and the `order_by_fields` attribute,
        while setting the `is_distinct` flag to True.
        """
        a = Point(element_id=1, name="A")
        b = Point(element_id=2, name="B")
        qs = KMLQuerySet([a, b])
        qs.is_ordered = True
        qs.order_by_fields = ["name"]
        d = qs.distinct()
        assert d.is_distinct is True
        assert d.is_ordered is True
        assert d.order_by_fields == ["name"]

    def test_apply_lookup_field_value_none_isnull_behavior(self) -> None:
        """
        Tests the behavior of the _apply_lookup method in KMLQuerySet when the
        field value is None and the lookup type is 'isnull'.

        Verifies that:
        - When 'isnull' is True, the method returns True for a None value.
        - When 'isnull' is False, the method returns False for a None value.
        """
        qs: KMLQuerySet = KMLQuerySet([])
        # when field_value is None and lookup is isnull
        assert qs._apply_lookup(None, "isnull", True) is True
        assert qs._apply_lookup(None, "isnull", False) is False

    def test_get_multiple_elements_raises(self) -> None:
        """
        Test that KMLQuerySet.get() raises KMLMultipleElementsReturned when multiple
        elements match the query.

        This test creates two elements with the same ID, adds them to a KMLQuerySet,
        and asserts that calling get() with a filter that matches both elements
        raises the expected exception.
        """
        from kmlorm.core.exceptions import KMLMultipleElementsReturned

        a = Point(element_id=1)
        b = Point(element_id=1)
        qs = KMLQuerySet([a, b])
        with pytest.raises(KMLMultipleElementsReturned):
            qs.get(id__exact=1)

    def test_point_coords_empty_sequence_returns_none(self) -> None:
        """
        Test that the _point_coords method returns None when the coordinates attribute of
        the element is an empty sequence.

        This ensures that empty or falsey coordinates do not raise an error and are handled
        gracefully by returning None.
        """
        # Use _E element with empty coordinates instead of Point to avoid validation error
        e = self._E(id=9, coordinates=[])
        qs: KMLQuerySet = KMLQuerySet([e])
        # empty/falsey coordinates should result in None without error
        assert qs._point_coords(e) is None
