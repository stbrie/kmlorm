"""
KML ORM - A Django-style ORM for KML (Keyhole Markup Language) files.

This package provides an intuitive, Django-inspired interface for querying
and manipulating KML data without requiring Django as a dependency.
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from .core.exceptions import (
    KMLElementNotFound,
    KMLInvalidCoordinates,
    KMLMultipleElementsReturned,
    KMLOrmException,
    KMLParseError,
    KMLValidationError,
)
from .models.base import KMLElement
from .models.folder import Folder
from .models.multigeometry import MultiGeometry
from .models.path import Path
from .models.placemark import Placemark
from .models.point import Point, Coordinate
from .models.polygon import Polygon
from .parsers.kml_file import KMLFile

__all__ = [
    "__version__",
    "KMLOrmException",
    "KMLParseError",
    "KMLElementNotFound",
    "KMLMultipleElementsReturned",
    "KMLInvalidCoordinates",
    "KMLValidationError",
    "KMLElement",
    "Placemark",
    "Folder",
    "Path",
    "Polygon",
    "Point",
    "Coordinate",
    "MultiGeometry",
    "KMLFile",
]
