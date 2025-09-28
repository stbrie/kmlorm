"""
Django-style QuerySet implementation for KML elements.

This module provides the KMLQuerySet class that implements all the query
methods like filter(), exclude(), get(), etc. in a Django-compatible way.
"""

# pylint: disable=too-many-public-methods
import logging
import re
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
    Generic,
    TypeVar,
    overload,
)
from .exceptions import (
    KMLElementNotFound,
    KMLInvalidCoordinates,
    KMLMultipleElementsReturned,
    KMLQueryError,
    KMLValidationError,
)

if TYPE_CHECKING:
    from ..models.point import Coordinate
    from ..models.base import KMLElement


T = TypeVar("T", bound="KMLElement")


class KMLQuerySet(Generic[T]):
    """Typed QuerySet for KML elements.

    This class wraps a list of elements and implements the common query/filter
    operations. It is generic in the element type so callers receive precise
    T / Optional[T] / List[T] return types.

    Similar to Django's QuerySet.
    """

    def __init__(self, elements: Optional[List[T]] = None) -> None:
        """
        Initialize a QuerySet with a list of elements.

        Args:
            elements: List of KML elements to query. If None, starts empty.
        """
        self._elements: List[T] = list(elements or [])
        self._ordered = False
        self._order_by_fields: List[str] = []
        self._distinct = False

    def __iter__(self) -> Iterator[T]:
        """Make QuerySet iterable."""
        return iter(self._elements)

    def __len__(self) -> int:
        """Return the number of elements in the QuerySet."""
        return len(self._elements)

    @overload
    def __getitem__(self, key: int) -> T: ...

    @overload
    def __getitem__(self, key: slice) -> "KMLQuerySet[T]": ...

    def __getitem__(self, key: Union[int, slice]) -> Union[T, "KMLQuerySet[T]"]:
        """
        Support indexing and slicing of QuerySet.

        Args:
            key: Index or slice object

        Returns:
            Single element for index, new QuerySet for slice
        """
        if isinstance(key, int):
            return self._elements[key]
        if isinstance(key, slice):
            return self.__class__(self._elements[key])
        raise TypeError("QuerySet indices must be integers or slices")

    def __bool__(self) -> bool:
        """Return True if QuerySet has any elements."""
        return bool(self._elements) or False

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<KMLQuerySet [{len(self._elements)} elements]>"

    @property
    def elements(self) -> List[T]:
        """
        Returns the list of KMLElement objects associated with this queryset.

        Returns:
            Optional[List["KMLElement"]]: A list of KMLElement instances if available, otherwise
                None.
        """
        return self._elements

    @elements.setter
    def elements(self, value: Optional[List[T]]) -> None:
        """
        Sets the elements of the queryset, ensuring all items are instances of KMLElement.
        Args:
            value: An iterable containing KMLElement instances to assign, or None to do nothing.
        Raises:
            TypeError: If any item in `value` is not an instance of KMLElement.
        Returns:
            None
        """
        # Setting None should do nothing (preserves existing elements)
        if value is None:
            return

        # pylint: disable=import-outside-toplevel
        from ..models.base import KMLElement as _KMLElement

        for item in value:
            if not isinstance(item, _KMLElement):
                raise TypeError("Elements assignment must contain only KMLElement instances.")

        self._elements = value.copy()

    def all(self) -> "KMLQuerySet[T]":
        """
        Return a copy of this QuerySet.

        This method exists for Django compatibility and returns a new
        QuerySet with the same elements.
        """
        return self.__class__(self._elements.copy())

    def filter(self, **kwargs: Any) -> "KMLQuerySet[T]":
        """
        Filter elements based on field lookups.

        Supports Django-style field lookups like:
        - name__icontains='capital'
        - coordinates__latitude__gte=39.0
        - visibility=True

        Args:
            **kwargs: Field lookup expressions

        Returns:
            New QuerySet with filtered elements
        """
        filtered_elements = []

        for element in self._elements:
            if self._matches_filters(element, kwargs):
                filtered_elements.append(element)

        new_qs = self.__class__(filtered_elements)
        new_qs.is_ordered = self.is_ordered
        new_qs.order_by_fields = self.order_by_fields
        return new_qs

    @property
    def is_ordered(self) -> bool:
        """
        Returns whether the queryset is ordered.

        Returns:
            bool: True if the queryset has an ordering applied, False otherwise.
        """
        return self._ordered

    @is_ordered.setter
    def is_ordered(self, value: bool) -> None:
        """
        Sets whether the queryset should be ordered.

        Args:
            value (bool): If True, the queryset will be ordered; if False, it will not be ordered.
        """
        self._ordered = value

    @property
    def order_by_fields(self) -> List[str]:
        """
        Returns the list of field names used to determine the ordering of query results.

        Returns:
            List[str]: A list of strings representing the field names by which the results are
                ordered.
        """
        return self._order_by_fields

    @order_by_fields.setter
    def order_by_fields(self, value: List[str]) -> None:
        """
        Sets the fields by which query results should be ordered.

        Args:
            value (List[str]): A list of field names to order the query results by.
        """
        self._order_by_fields = value.copy()

    @property
    def is_distinct(self) -> bool:
        """
        Returns whether the queryset is marked to return distinct results.

        Returns:
            bool: True if the queryset is set to return distinct results, False otherwise.
        """
        return bool(self._distinct)

    @is_distinct.setter
    def is_distinct(self, value: bool) -> None:
        """
        Sets whether the query should return distinct results.

        Args:
            value (bool): If True, the query will return only distinct results; otherwise,
                duplicates may be included.

        Returns:
            None
        """
        self._distinct = bool(value)

    def exclude(self, **kwargs: Any) -> "KMLQuerySet[T]":
        """
        Exclude elements that match the given filters.

        This is the inverse of filter() - returns elements that do NOT
        match the criteria.

        Args:
            **kwargs: Field lookup expressions

        Returns:
            New QuerySet with non-matching elements
        """
        filtered_elements = []

        for element in self._elements:
            if not self._matches_filters(element, kwargs):
                filtered_elements.append(element)

        new_qs = self.__class__(filtered_elements)
        new_qs.is_ordered = self.is_ordered
        new_qs.order_by_fields = self.order_by_fields
        return new_qs

    def get(self, **kwargs: Any) -> "T":
        """
        Get a single element that matches the given criteria.

        Args:
            **kwargs: Field lookup expressions

        Returns:
            Single matching KML element

        Raises:
            KMLElementNotFound: If no elements match
            KMLMultipleElementsReturned: If multiple elements match
        """
        filtered = self.filter(**kwargs)

        if len(filtered) == 0:
            element_type = self._elements[0].__class__.__name__ if self._elements else "KMLElement"
            raise KMLElementNotFound(element_type, kwargs)
        if len(filtered) > 1:
            element_type = filtered.elements[0].__class__.__name__
            raise KMLMultipleElementsReturned(element_type, len(filtered), kwargs)

        return filtered.elements[0]

    def first(self) -> Optional[T]:
        """
        Get the first element in the QuerySet.

        Returns:
            First element or None if QuerySet is empty
        """
        return self._elements[0] if self._elements else None

    def last(self) -> Optional[T]:
        """
        Get the last element in the QuerySet.

        Returns:
            Last element or None if QuerySet is empty
        """
        return self._elements[-1] if self._elements else None

    def count(self) -> int:
        """
        Return the number of elements in the QuerySet.

        Returns:
            Number of elements
        """
        return len(self._elements)

    def exists(self) -> bool:
        """
        Check if the QuerySet contains any elements.

        Returns:
            True if QuerySet has elements, False otherwise
        """
        return bool(self._elements)

    def none(self) -> "KMLQuerySet[T]":
        """
        Return an empty QuerySet.

        Returns:
            Empty QuerySet of the same type
        """
        return self.__class__([])

    def order_by(self, *fields: str) -> "KMLQuerySet[T]":
        """
        Order elements by the given fields.

        Supports field names with optional '-' prefix for descending order.

        Args:
            *fields: Field names to order by (e.g., 'name', '-visibility')

        Returns:
            New ordered QuerySet
        """
        if not fields:
            return self.all()

        new_qs = self.all()
        new_qs.is_ordered = True
        new_qs.order_by_fields = list(fields)

        # Sort elements by each field (in reverse order for stable sorting)
        for field in reversed(fields):

            reverse = field.startswith("-")
            clean_field = field.lstrip("-")

            try:

                def _key_fn(elem: T, cf: str = clean_field) -> Any:
                    return self._get_field_value(elem, cf)

                new_qs.elements.sort(key=_key_fn, reverse=reverse)
            except AttributeError as ae:
                raise KMLQueryError(f"Cannot order by field '{clean_field}'", clean_field) from ae

        return new_qs

    def reverse(self) -> "KMLQuerySet[T]":
        """
        Reverse the order of elements.

        Returns:
            New QuerySet with reversed element order
        """
        new_qs = self.all()
        new_qs.elements.reverse()
        return new_qs

    def distinct(self) -> "KMLQuerySet[T]":
        """
        Remove duplicate elements.

        Returns:
            New QuerySet with unique elements only
        """
        seen = set()
        unique_elements = []

        for element in self._elements:
            # Use id if available, otherwise use object id
            key = element.id if element.id else id(element)
            if key not in seen:
                seen.add(key)
                unique_elements.append(element)

        new_qs = self.__class__(unique_elements)
        new_qs.is_distinct = True
        new_qs.is_ordered = self.is_ordered
        new_qs.order_by_fields = self._order_by_fields.copy()
        return new_qs

    def values(self, *fields: str) -> List[Dict[str, Any]]:
        """
        Return a list of dictionaries with specified field values.

        Args:
            *fields: Field names to include in dictionaries

        Returns:
            List of dictionaries with field values
        """
        if not fields:
            # Return all fields
            return [element.to_dict() for element in self._elements]

        result = []
        for element in self._elements:
            item = {}
            for field in fields:
                try:
                    item[field] = self._get_field_value(element, field)
                except AttributeError:
                    item[field] = None
            result.append(item)

        return result

    def values_list(self, *fields: str, flat: bool = False) -> List[Any]:
        """
        Return a list of tuples with specified field values.

        Args:
            *fields: Field names to include in tuples
            flat: If True and only one field, return flat list of values

        Returns:
            List of tuples (or flat list if flat=True and one field)
        """
        if flat and len(fields) != 1:
            raise ValueError("values_list() with flat=True requires exactly one field")

        result = []
        for element in self._elements:
            values = []
            for field in fields:
                try:
                    values.append(self._get_field_value(element, field))
                except AttributeError:
                    values.append(None)

            if flat:
                result.append(values[0])
            else:
                result.append(tuple(values))

        return result

    # Geospatial-specific methods

    def near(
        self, longitude: float, latitude: float, radius_km: Optional[float] = None
    ) -> "KMLQuerySet[T]":
        """
        Filter elements within a radius of given coordinates.

        Args:
            longitude: Center longitude (-180 to 180)
            latitude: Center latitude (-90 to 90)
            radius_km: Radius in kilometers (if None, no distance filtering)

        Returns:
            New QuerySet with nearby elements
        """
        # pylint: disable=import-outside-toplevel
        from ..models.point import Coordinate
        from ..spatial.calculations import (
            SpatialCalculations,
        )

        center = Coordinate(longitude=longitude, latitude=latitude, altitude=0.0)

        if radius_km is None:
            return self.all()

        filtered_elements = []
        for element in self._elements:
            try:
                coords = self._point_coords(element)
                if coords:
                    distance = SpatialCalculations.distance_between(center, coords)
                    if distance is not None and distance <= radius_km:
                        filtered_elements.append(element)
            except (ValueError, TypeError):
                continue

        return self.__class__(filtered_elements)

    def within_bounds(
        self, north: float, south: float, east: float, west: float
    ) -> "KMLQuerySet[T]":
        """
        Filter elements within a bounding box.

        Args:
            north: Northern boundary (max latitude)
            south: Southern boundary (min latitude)
            east: Eastern boundary (max longitude)
            west: Western boundary (min longitude)

        Returns:
            New QuerySet with elements in bounds
        """
        # Validate bounds
        if not -90 <= south <= north <= 90:
            raise KMLInvalidCoordinates("Invalid latitude bounds")
        if not -180 <= west <= 180 and -180 <= east <= 180:
            raise KMLInvalidCoordinates("Invalid longitude bounds")

        filtered_elements = []
        for element in self._elements:

            try:
                coords = self._point_coords(element)
                if coords:
                    elem_lon, elem_lat = coords.longitude, coords.latitude
                    # Handle longitude wraparound
                    if west <= east:  # Normal case
                        lon_in_bounds = west <= elem_lon <= east
                    else:  # Crosses 180° meridian
                        lon_in_bounds = elem_lon >= west or elem_lon <= east

                    if south <= elem_lat <= north and lon_in_bounds:
                        filtered_elements.append(element)
            except (ValueError, TypeError):
                continue

        return self.__class__(filtered_elements)

    def has_coordinates(self) -> "KMLQuerySet[T]":
        """
        Filter elements that have coordinate data.

        Returns:
            New QuerySet with elements that have coordinates
        """
        filtered_elements = []
        for element in self._elements:

            try:
                coords = self._point_coords(element)
                if coords:
                    filtered_elements.append(element)
            except (ValueError, TypeError):
                continue

        return self.__class__(filtered_elements)

    def valid_coordinates(self) -> "KMLQuerySet[T]":
        """
        Filter elements with valid coordinate ranges.

        Uses the Coordinate class validation to ensure consistency with
        the authoritative coordinate validation logic.

        Returns:
            New QuerySet with elements having valid coordinates
        """
        filtered_elements = []
        for element in self._elements:
            try:
                coords = self._point_coords(element)
                if coords and coords.longitude is not None and coords.latitude is not None:
                    # Import here to avoid circular imports
                    from ..models.point import Coordinate  # pylint: disable=import-outside-toplevel

                    # Create a new Coordinate to validate ranges using the authoritative logic
                    # This replaces manual range checks with the same validation used elsewhere
                    try:
                        altitude = getattr(coords, "altitude", 0.0)
                        Coordinate(
                            longitude=coords.longitude, latitude=coords.latitude, altitude=altitude
                        )
                        filtered_elements.append(element)
                    except KMLValidationError:
                        # Invalid coordinate ranges - skip this element
                        continue
            except (ValueError, TypeError, AttributeError):
                # Problems extracting coordinates - skip this element
                continue

        return self.__class__(filtered_elements)

    # Helper methods

    def _matches_filters(self, element: T, filters: Dict[str, Any]) -> bool:
        """
        Check if an element matches all the given filters.

        Args:
            element: KML element to check
            filters: Dictionary of field lookups

        Returns:
            True if element matches all filters
        """
        for lookup, value in filters.items():
            if not self._matches_single_filter(element, lookup, value):
                return False
        return True

    def _matches_single_filter(self, element: T, lookup: str, value: Any) -> bool:
        """
        Check if an element matches a single filter.

        Args:
            element: KML element to check
            lookup: Field lookup string (e.g., 'name__icontains')
            value: Value to match against

        Returns:
            True if element matches the filter
        """
        # Parse field lookup
        parts = lookup.split("__")
        field_name = parts[0]
        lookup_type = parts[1] if len(parts) > 1 else "exact"

        # Get field value
        try:
            field_value = self._get_field_value(element, field_name)
        except AttributeError:
            return False

        # Apply lookup type
        return self._apply_lookup(field_value, lookup_type, value)

    def _get_field_value(self, element: T, field_path: str) -> Any:
        """
        Get a field value from an element, supporting nested field access.

        Args:
            element: KML element
            field_path: Field name or path (e.g., 'name' or 'coordinates.latitude')

        Returns:
            Field value

        Raises:
            AttributeError: If field doesn't exist
        """
        parts = field_path.split(".")
        current = element

        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                raise AttributeError(f"'{element.__class__.__name__}' has no attribute '{part}'")

        return current

    def _apply_lookup(self, field_value: Any, lookup_type: str, filter_value: Any) -> bool:
        """
        Apply a lookup type to compare field value with filter value.

        Args:
            field_value: Value from the element field
            lookup_type: Lookup type (e.g., 'exact', 'icontains', 'gte')
            filter_value: Value to compare against

        Returns:
            True if lookup matches
        """
        # pylint: disable=too-many-return-statements, too-many-branches, too-many-public-methods
        if field_value is None:
            return lookup_type == "isnull" and filter_value

        # String lookups
        if lookup_type == "exact":
            return bool(field_value == filter_value)
        if lookup_type == "iexact":
            return str(field_value).lower() == str(filter_value).lower()
        if lookup_type == "contains":
            return str(filter_value) in str(field_value)
        if lookup_type == "icontains":
            return str(filter_value).lower() in str(field_value).lower()
        if lookup_type == "startswith":
            return str(field_value).startswith(str(filter_value))
        if lookup_type == "istartswith":
            return str(field_value).lower().startswith(str(filter_value).lower())
        if lookup_type == "endswith":
            return str(field_value).endswith(str(filter_value))
        if lookup_type == "iendswith":
            return str(field_value).lower().endswith(str(filter_value).lower())
        if lookup_type == "regex":
            return bool(re.search(str(filter_value), str(field_value)))
        if lookup_type == "iregex":
            return bool(re.search(str(filter_value), str(field_value), re.IGNORECASE))

        # Comparison lookups
        if lookup_type == "gt":
            return bool(field_value > filter_value)
        if lookup_type == "gte":
            return bool(field_value >= filter_value)
        if lookup_type == "lt":
            return bool(field_value < filter_value)
        if lookup_type == "lte":
            return bool(field_value <= filter_value)

        # Range and membership lookups
        if lookup_type == "in":
            return bool(field_value in filter_value)
        if lookup_type == "range":
            return bool(filter_value[0] <= field_value <= filter_value[1])
        if lookup_type == "isnull":
            return bool((field_value is None) == filter_value)

        raise KMLQueryError(f"Unsupported lookup type: {lookup_type}")

    def _point_coords(self, element: T) -> Optional["Coordinate"]:
        """
        Extract coordinates from a KML element.

        Args:
            element: KML element to extract coordinates from

        Returns:
            Coordinate instance or None if no valid coordinates found
        """
        from ..models.point import (  # pylint: disable=import-outside-toplevel
            Point as _Point,
            Coordinate,
        )

        # For Point objects, get coordinates directly
        if isinstance(element, _Point):
            return element.coordinates

        # For other elements, try to find standard coordinates attribute
        coords = getattr(element, "coordinates", None)

        if not coords:
            return None

        try:
            return Coordinate.from_any(coords)
        except (ValueError, TypeError) as e:
            # Log warning for invalid coordinates but don't raise
            logger = logging.getLogger(__name__)
            logger.warning(
                "Failed to parse coordinates from element %s: %s. Skipping coordinate extraction.",
                getattr(element, "id", "unknown"),
                str(e),
            )
            return None
