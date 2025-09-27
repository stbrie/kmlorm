"""
Unit tests for the KMLQuerySet class and its API, covering filtering, ordering, slicing, and
value extraction.
Test Classes:
-------------
- TestKMLQuerySetLookups:
    Tests various lookup operations on KMLQuerySet, including:
    - Exact, case-insensitive contains, contains, regex, startswith, endswith, and their
        case-insensitive variants.
    - Comparison lookups (gt, lte).
    - Membership and range lookups (in, range).
    - Null checks (isnull).
    - Error handling for unsupported lookups.
- TestKMLQuerySetAPI:
    Tests the core API of KMLQuerySet, including:
    - get() method for single, not found, and multiple results.
    - order_by() and reverse() for sorting.
    - Error handling for invalid ordering.
    - values() and values_list() for extracting field values.
    - Error handling for invalid values_list() usage.
    - distinct(), none(), slicing, and boolean evaluation.
- TestQuerySet:
    Additional tests for KMLQuerySet, including:
    - Filtering with exact and icontains lookups.
    - get() method for not found, multiple, and single results.
    - none() method for empty queryset.
    - order_by() for ascending and descending order.
Helper Classes:
---------------
- _SimpleElement:
    A minimal element class used for testing, supporting attribute assignment,
    string representation, and dict conversion.
Exceptions:
-----------
- KMLElementNotFound: Raised when no element matches a query.
- KMLMultipleElementsReturned: Raised when multiple elements match a query
    expecting a single result.
- KMLQueryError: Raised for invalid queries or lookups.
Dependencies:
-------------
- pytest: For exception assertion and test running.
- kmlorm.core.querysets.KMLQuerySet: The class under test.
- kmlorm.core.exceptions: Custom exceptions used by KMLQuerySet.
"""

from typing import Any
import pytest

from kmlorm.core.querysets import KMLQuerySet
from kmlorm.core.exceptions import (
    KMLElementNotFound,
    KMLMultipleElementsReturned,
    KMLQueryError,
)
from kmlorm.models.base import KMLElement


class _SimpleElement(KMLElement):
    def __init__(self, **kwargs: Any) -> None:
        # Extract base class parameters
        base_params = {
            "element_id": kwargs.pop("id", None),
            "name": kwargs.pop("name", None),
            "description": kwargs.pop("description", None),
            "visibility": kwargs.pop("visibility", True),
        }
        super().__init__(**base_params)

        # Set any additional attributes
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return f"<SE {getattr(self, 'name', None)}>"

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the object's attributes to a dictionary.

        Returns:
            dict[str, Any]: A dictionary containing the object's attribute names
            as keys and their corresponding values.
        """
        # Simple dict representation used by QuerySet.values() in tests
        return dict(self.__dict__)


class TestKMLQuerySetLookups:
    """
    Test suite for KMLQuerySet lookup functionality.

    This class contains tests for various field lookups supported by KMLQuerySet,
    including exact, icontains, contains, regex, startswith, endswith, comparison
    lookups (gt, lte), 'in', 'range', 'isnull', and error handling for unsupported
    lookups.

    Tested lookups:
    - exact: Field value matches exactly.
    - icontains: Case-insensitive substring match.
    - contains: Substring match.
    - regex: Regular expression match.
    - startswith / istartswith: String starts with value (case-sensitive/insensitive).
    - endswith / iendswith: String ends with value (case-sensitive/insensitive).
    - gt / lte: Greater than / less than or equal comparisons.
    - in: Field value is in a given iterable.
    - range: Field value is within a given range.
    - isnull: Field value is (or is not) None.
    - Raises KMLQueryError for unsupported lookups.

    Fixtures:
    - Sets up a KMLQuerySet with three _SimpleElement instances for use in tests.
    """

    a: _SimpleElement
    b: _SimpleElement
    c: _SimpleElement
    qs: KMLQuerySet

    def setup_method(self) -> None:
        """
        Set up test fixtures for each test method.

        Initializes three _SimpleElement instances with varying attributes
        and assigns them to self.a, self.b, and self.c.
        Creates a KMLQuerySet containing these elements and assigns it to self.qs.
        """
        self.a = _SimpleElement(id=1, name="Alpha", rank=10, tags=["x", "y"], maybe=None)
        self.b = _SimpleElement(id=2, name="beta", rank=5, tags=["y"], maybe=0)
        self.c = _SimpleElement(id=3, name="AlphaBeta", rank=7, tags=[], maybe=None)
        self.qs = KMLQuerySet([self.a, self.b, self.c])

    def test_exact_and_icontains(self) -> None:
        """
        Tests the 'filter' method of the queryset for both exact and case-insensitive
        containment lookups on the 'name' field.

        - Verifies that filtering with 'name__exact' returns only the element with an exact match.
        - Verifies that filtering with 'name__icontains' returns all elements whose 'name'
            contains the substring, case-insensitively.
        """
        exact = self.qs.filter(name__exact="Alpha")
        assert len(exact.elements) == 1 and exact.elements[0] is self.a

        icontains = self.qs.filter(name__icontains="alpha")
        assert set(e for e in icontains.elements) == {self.a, self.c}

    def test_contains_and_regex(self) -> None:
        """
        Tests the queryset's ability to filter elements using 'contains' and 'regex' lookups
            on the 'name' field.

        - Verifies that filtering with 'name__contains="Beta"' returns only elements
            whose name contains the substring 'Beta'.
        - Verifies that filtering with 'name__regex=r"^A.*a$"' returns all elements
            whose name starts with 'A' and ends with 'a'.
        """
        contains = self.qs.filter(name__contains="Beta")
        assert contains.elements == [self.c]

        # The regex '^A.*a$' matches any string that starts with 'A' and ends
        # with 'a' — both 'Alpha' and 'AlphaBeta' meet that condition here.
        regex = self.qs.filter(name__regex=r"^A.*a$")
        assert set(regex.elements) == {self.a, self.c}

    def test_startswith_and_endswith(self) -> None:
        """
        Tests the queryset filtering functionality for string field lookups:
        - Checks that filtering with 'startswith' returns elements whose 'name'
            starts with the given prefix.
        - Checks that filtering with 'istartswith' (case-insensitive) returns elements
            whose 'name' starts with the given prefix, ignoring case.
        - Checks that filtering with 'iendswith' (case-insensitive) returns elements
            whose 'name' ends with the given suffix, ignoring case.
        """
        # Both 'Alpha' and 'AlphaBeta' start with 'Al'
        starts = self.qs.filter(name__startswith="Al")
        assert set(starts.elements) == {self.a, self.c}

        istarts = self.qs.filter(name__istartswith="be")
        assert istarts.elements == [self.b]

        iends = self.qs.filter(name__iendswith="ta")

        assert set(iends.elements) == {self.b, self.c}

    def test_comparison_lookups(self) -> None:
        """
        Tests the queryset's ability to filter elements using comparison lookups.

        This test verifies that:
        - Filtering with 'rank__gt=6' returns only elements with rank greater than 6.
        - Filtering with 'rank__lte=7' returns only elements with rank less than or equal to 7.
        """
        gt = self.qs.filter(rank__gt=6)
        assert set(gt.elements) == {self.a, self.c}

        lte = self.qs.filter(rank__lte=7)
        assert set(lte.elements) == {self.b, self.c}

    def test_in_and_range_and_isnull(self) -> None:
        """
        Tests the queryset filtering methods for 'in', 'range', and 'isnull' lookups.

        - Verifies that filtering with 'in' returns elements whose 'name' is in the provided list.
        - Checks that filtering with 'range' returns elements whose 'rank' falls within
            the specified range.
        - Ensures that filtering with 'isnull' returns elements where the 'maybe' field is null.
        """
        # 'in' expects iterable filter value where field_value in filter_value
        in_q = self.qs.filter(name__in=["Alpha", "Gamma"])
        assert in_q.elements == [self.a]

        range_q = self.qs.filter(rank__range=(6, 11))
        assert set(range_q.elements) == {self.a, self.c}

        isnull_q = self.qs.filter(maybe__isnull=True)
        assert set(isnull_q.elements) == {self.a, self.c}

    def test_unsupported_lookup_raises(self) -> None:
        """
        Test that using an unsupported lookup in the filter method raises a KMLQueryError.

        This test verifies that when an invalid or unknown lookup (e.g., 'name__unknown') is used
        with the queryset's filter method, the appropriate exception (KMLQueryError) is raised,
        ensuring that unsupported query operations are properly handled.
        """
        with pytest.raises(KMLQueryError):
            self.qs.filter(name__unknown=123)


class TestKMLQuerySetAPI:
    """
    Test suite for the KMLQuerySet API, verifying core query and utility behaviors.

    Tested features include:
    - Retrieval of elements with `get`, including error handling for not found and multiple results.
    - Ordering of elements with `order_by` and `reverse`, including error handling for
        invalid fields.
    - Extraction of values and value lists with `values` and `values_list`, including flat
        argument validation.
    - Distinct element selection, creation of empty querysets, slicing, and boolean
        evaluation of querysets.

    Each test ensures correct exceptions are raised and expected results are returned for
    various queryset operations.
    """

    a: _SimpleElement
    b: _SimpleElement
    c: _SimpleElement
    qs: KMLQuerySet

    def setup_method(self) -> None:
        """
        Set up test fixtures for each test method.

        Creates three instances of _SimpleElement with different ids, names, and ranks,
        and initializes a KMLQuerySet containing these elements for use in tests.
        """
        self.a = _SimpleElement(id=1, name="A", rank=3)
        self.b = _SimpleElement(id=2, name="B", rank=1)
        self.c = _SimpleElement(id=3, name="C", rank=2)
        self.qs = KMLQuerySet([self.a, self.b, self.c])

    def test_get_not_found_and_multiple(self) -> None:
        """
        Tests the behavior of the 'get' method in the queryset for three scenarios:
        1. Raises KMLElementNotFound when no element matches the query.
        2. Raises KMLMultipleElementsReturned when multiple elements match the query.
        3. Returns the correct element when exactly one element matches the query.
        """
        with pytest.raises(KMLElementNotFound):
            self.qs.get(name__exact="X")

        # multiple
        with pytest.raises(KMLMultipleElementsReturned):
            self.qs.get(rank__gt=0)  # all three

        # single
        assert self.qs.get(name__exact="B") is self.b

    def test_order_by_and_reverse_and_invalid(self) -> None:
        """
        Tests the ordering and reversing functionality of the queryset.

        This test verifies that:
        - Ordering by a valid attribute in ascending order returns elements sorted in
            ascending order.
        - Ordering by a valid attribute in descending order (using a '-' prefix) returns
            elements sorted in descending order.
        - Reversing an ascendingly ordered queryset returns elements in descending order.
        - Attempting to order by a non-existent attribute raises a KMLQueryError.
        """
        asc = self.qs.order_by("rank")
        assert [getattr(e, "rank", None) for e in asc.elements] == [1, 2, 3]

        desc = self.qs.order_by("-rank")
        assert [getattr(e, "rank", None) for e in desc.elements] == [3, 2, 1]

        rev = asc.reverse()
        assert [getattr(e, "rank", None) for e in rev.elements] == [3, 2, 1]

        # ordering by missing attribute should raise KMLQueryError
        with pytest.raises(KMLQueryError):
            self.qs.order_by("missing")

    def test_values_and_values_list_and_flat_error(self) -> None:
        """
        Tests the behavior of the 'values' and 'values_list' queryset methods.

        - Verifies that 'values()' returns a list of dictionaries.
        - Checks that 'values("name", "rank")' returns dictionaries containing the specified keys.
        - Ensures 'values_list("name", "rank")' returns a list of tuples.
        - Asserts that using 'flat=True' with multiple fields in 'values_list' raises a ValueError.
        """
        vals_all = self.qs.values()
        assert isinstance(vals_all, list) and all(isinstance(d, dict) for d in vals_all)

        vals = self.qs.values("name", "rank")
        assert all("name" in d and "rank" in d for d in vals)

        vlist = self.qs.values_list("name", "rank")
        assert isinstance(vlist[0], tuple)

        with pytest.raises(ValueError):
            self.qs.values_list("a", "b", flat=True)

    def test_distinct_and_none_and_slice_and_bool(self) -> None:
        """
        Tests the behavior of the KMLQuerySet for distinct, none, slicing, and boolean evaluation.

        - Verifies that calling `distinct()` returns a queryset marked as distinct.
        - Checks that `none()` returns an empty queryset of the correct type.
        - Ensures slicing the queryset returns a new queryset with the expected length.
        - Asserts that a non-empty queryset evaluates to True in a boolean context.
        """
        dup = self.a
        self.qs._elements.append(dup)  # duplicate  # pylint: disable=protected-access
        distinct = self.qs.distinct()
        assert distinct.is_distinct is True

        empty = self.qs.none()
        assert isinstance(empty, KMLQuerySet) and len(empty) == 0

        sliced = self.qs[0:2]
        assert isinstance(sliced, KMLQuerySet) and len(sliced) == 2

        assert bool(self.qs) is True


class TestQuerySet:
    """
    Test suite for the KMLQuerySet class, verifying its core query and ordering functionalities.

    This class contains tests for:
    - Filtering elements using exact and case-insensitive containment lookups.
    - Retrieving single elements with `get`, including error handling for not found and
        multiple results.
    - Returning an empty queryset with `none`.
    - Ordering elements in ascending and descending order by a specified field.

    Attributes:
        a (_SimpleElement): Test element with id=1, name="Alpha", rank=3, visibility=True.
        b (_SimpleElement): Test element with id=2, name="Beta", rank=1, visibility=False.
        c (_SimpleElement): Test element with id=3, name="alpha-beta", rank=2, visibility=True.
        qs (KMLQuerySet): QuerySet containing the above elements.

    Test Methods:
        test_filter_exact_and_icontains: Tests filtering by exact match and
            case-insensitive containment.
        test_get_not_found_and_multiple: Tests get method for not found, multiple,
            and single result cases.
        test_none_returns_empty_queryset: Tests that none() returns an empty queryset.
        test_order_by_ascending_and_descending: Tests ordering by a field in ascending
            and descending order.
    """

    a: _SimpleElement
    b: _SimpleElement
    c: _SimpleElement
    qs: KMLQuerySet

    def setup_method(self) -> None:
        """
        Set up test fixtures for each test method.

        Initializes three _SimpleElement instances with different attributes and
        creates a KMLQuerySet containing these elements for use in tests.
        """
        self.a = _SimpleElement(id=1, name="Alpha", rank=3, visibility=True)
        self.b = _SimpleElement(id=2, name="Beta", rank=1, visibility=False)
        self.c = _SimpleElement(id=3, name="alpha-beta", rank=2, visibility=True)
        self.qs = KMLQuerySet([self.a, self.b, self.c])

    def test_filter_exact_and_icontains(self) -> None:
        """
        Tests the 'filter' method of the queryset for both 'exact' and 'icontains' lookups
        on the 'name' field.

        - Verifies that filtering with 'name__exact' returns a queryset containing only
            the exact match.
        - Verifies that filtering with 'name__icontains' returns a queryset containing
            all case-insensitive matches.
        - Asserts the correct type and contents of the returned querysets.
        """
        exact = self.qs.filter(name__exact="Alpha")
        assert isinstance(exact, KMLQuerySet)
        assert len(exact.elements) == 1
        assert exact.elements[0] is self.a

        icontains = self.qs.filter(name__icontains="alp")
        assert len(icontains.elements) == 2
        assert set(e.name for e in icontains.elements) == {"Alpha", "alpha-beta"}

    def test_get_not_found_and_multiple(self) -> None:
        """
        Tests the behavior of the `get` method in the queryset for three scenarios:
        1. Raises `KMLElementNotFound` when no element matches the query.
        2. Raises `KMLMultipleElementsReturned` when multiple elements match the query.
        3. Returns the correct element when exactly one match is found.
        """
        # not found
        with pytest.raises(KMLElementNotFound):
            self.qs.get(name__exact="Nope")

        # multiple returned
        with pytest.raises(KMLMultipleElementsReturned):
            self.qs.get(name__icontains="alp")  # matches a and c

        # single hit returns the element
        single = self.qs.get(name__exact="Beta")
        assert single is self.b

    def test_none_returns_empty_queryset(self) -> None:
        """
        Tests that calling the `none()` method on the queryset returns an empty
            `KMLQuerySet` instance.
        Ensures that the returned object is of type `KMLQuerySet` and contains no elements.
        """
        empty = self.qs.none()
        assert isinstance(empty, KMLQuerySet)
        assert empty.elements == []

    def test_order_by_ascending_and_descending(self) -> None:
        """
        Tests the `order_by` method of the queryset for both ascending and descending order.
        Verifies that ordering by "rank" returns elements in ascending order, and
            ordering by "-rank"
        returns elements in descending order.
        """
        asc = self.qs.order_by("rank")
        assert [getattr(e, "rank", None) for e in asc.elements] == [1, 2, 3]

        desc = self.qs.order_by("-rank")
        assert [getattr(e, "rank", None) for e in desc.elements] == [3, 2, 1]
