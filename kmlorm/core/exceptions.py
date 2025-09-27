"""
Exception classes for KML ORM operations.

This module defines all custom exceptions used throughout the KML ORM package,
following Django's exception patterns for consistency.
"""

from typing import Any, Optional


class KMLOrmException(Exception):
    """
    Base exception class for all KML ORM operations.

    All other KML ORM exceptions inherit from this class, making it easy
    to catch any KML ORM-related error.
    """


class KMLParseError(KMLOrmException):
    """
    Raised when KML content cannot be parsed.

    This exception is raised when:
    - KML file is malformed or invalid
    - Required KML elements are missing
    - KML content doesn't conform to expected structure
    """

    def __init__(self, message: str, source: Optional[str] = None) -> None:
        """
        Initialize KMLParseError.

        Args:
            message: Description of the parsing error
            source: Optional source file or URL that caused the error
        """
        super().__init__(message)
        self.source = source


class KMLElementNotFound(KMLOrmException):
    """
    Raised when a get() query finds no matching elements.

    Similar to Django's DoesNotExist exception, this is raised when
    a get() call expects exactly one element but finds none.
    """

    def __init__(self, element_type: str, query_kwargs: Optional[dict] = None) -> None:
        """
        Initialize KMLElementNotFound.

        Args:
            element_type: The type of element that was not found
            query_kwargs: The query parameters that yielded no results
        """
        if query_kwargs:
            query_str = ", ".join(f"{k}={v}" for k, v in query_kwargs.items())
            message = f"{element_type} matching query({query_str}) does not exist."
        else:
            message = f"{element_type} does not exist."

        super().__init__(message)
        self.element_type = element_type
        self.query_kwargs = query_kwargs or {}


class KMLMultipleElementsReturned(KMLOrmException):
    """
    Raised when a get() query finds multiple matching elements.

    Similar to Django's MultipleObjectsReturned exception, this is raised
    when a get() call expects exactly one element but finds multiple.
    """

    def __init__(self, element_type: str, count: int, query_kwargs: Optional[dict] = None) -> None:
        """
        Initialize KMLMultipleElementsReturned.

        Args:
            element_type: The type of element that had multiple matches
            count: Number of elements found
            query_kwargs: The query parameters that yielded multiple results
        """
        if query_kwargs:
            query_str = ", ".join(f"{k}={v}" for k, v in query_kwargs.items())
            message = (
                f"get() returned more than one {element_type} -- "
                f"it returned {count}! Lookup was: {query_str}"
            )
        else:
            message = f"get() returned more than one {element_type} -- it returned {count}!"

        super().__init__(message)
        self.element_type = element_type
        self.count = count
        self.query_kwargs = query_kwargs or {}


class KMLInvalidCoordinates(KMLOrmException):
    """
    Raised when coordinates are invalid or out of range.

    This exception is raised when:
    - Latitude is not between -90 and 90
    - Longitude is not between -180 and 180
    - Coordinate format is invalid
    - Required coordinate data is missing
    """

    def __init__(self, message: str, coordinates: Optional[Any] = None) -> None:
        """
        Initialize KMLInvalidCoordinates.

        Args:
            message: Description of what makes the coordinates invalid
            coordinates: The invalid coordinate data
        """
        super().__init__(message)
        self.coordinates = coordinates


class KMLValidationError(KMLOrmException):
    """
    Raised when KML element validation fails.

    This exception is raised when:
    - Required fields are missing
    - Field values don't meet validation criteria
    - Cross-field validation fails
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> None:
        """
        Initialize KMLValidationError.

        Args:
            message: Description of the validation error
            field: Name of the field that failed validation
            value: The invalid value
        """
        super().__init__(message)
        self.field = field
        self.value = value


class KMLQueryError(KMLOrmException):
    """
    Raised when a query cannot be executed.

    This exception is raised when:
    - Invalid field names are used in queries
    - Invalid lookup types are specified
    - Query operations are not supported
    """

    def __init__(self, message: str, query_field: Optional[str] = None) -> None:
        """
        Initialize KMLQueryError.

        Args:
            message: Description of the query error
            query_field: The field that caused the query error
        """
        super().__init__(message)
        self.query_field = query_field
