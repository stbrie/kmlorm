"""
Core functionality for KML ORM.

This package contains the fundamental classes and functionality
that power the Django-style ORM interface for KML data.
"""

# pylint: disable=duplicate-code
from .exceptions import (
    KMLElementNotFound,
    KMLInvalidCoordinates,
    KMLMultipleElementsReturned,
    KMLOrmException,
    KMLParseError,
    KMLQueryError,
    KMLValidationError,
)
from .managers import KMLManager, RelatedManager
from .querysets import KMLQuerySet

__all__ = [
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
