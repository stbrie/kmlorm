"""
KML model classes.

This package contains all the model classes that represent
different types of KML elements with Django-style interfaces.
"""

# pylint: disable=duplicate-code
from .base import KMLElement
from .folder import Folder
from .path import Path
from .placemark import Placemark
from .polygon import Polygon

__all__ = [
    "KMLElement",
    "Placemark",
    "Folder",
    "Path",
    "Polygon",
]
