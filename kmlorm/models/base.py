"""
Base classes for all KML elements.

This module provides the foundational KMLElement class that all other
KML element types inherit from, establishing the common interface and
Django-style ORM patterns.
"""

from abc import ABC, ABCMeta
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..core.exceptions import KMLValidationError

if TYPE_CHECKING:
    from ..core.managers import KMLManager


class KMLElementMeta(ABCMeta):
    """
    Metaclass for KML elements that sets up the manager.
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs: Any) -> type:
        new_class = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Set up manager for non-abstract classes
        if name != "KMLElement" and not getattr(new_class, "_abstract", False):
            # Import here to avoid circular imports
            from ..core.managers import KMLManager  # pylint: disable=import-outside-toplevel

            manager: "KMLManager" = KMLManager()
            manager.contribute_to_class(new_class, "objects")

        return new_class


class KMLElement(ABC, metaclass=KMLElementMeta):
    """
    Base class for all KML elements.

    Provides common attributes and methods shared by all KML element types
    including Placemark, Folder, Path, and Polygon. This class establishes
    the Django-style ORM interface pattern.
    """

    # Class-level manager (will be set by metaclass)
    objects: "KMLManager"

    def __init__(
        self,
        element_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        visibility: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a KML element with common attributes.

        Args:
            element_id: Unique identifier for the element
            name: Display name for the element
            description: Descriptive text for the element
            visibility: Whether the element is visible in Google Earth
            **kwargs: Additional element-specific attributes
        """
        self.id = element_id
        self.name = name
        self.description = description
        self.visibility = visibility

        # Store any additional attributes for subclasses
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Reference to parent container (folder, document, etc.)
        self._parent: Optional["KMLElement"] = None

        # Internal storage for the original KML element if parsed from file
        self._kml_element: Optional[Any] = None

    def __str__(self) -> str:
        """
        String representation of the KML element.

        Returns the name if available, otherwise the class name and id.
        """
        if self.name:
            return self.name
        if self.id:
            return f"{self.__class__.__name__}({self.id})"
        return f"{self.__class__.__name__}(unnamed)"

    def __repr__(self) -> str:
        """
        Developer-friendly representation of the KML element.
        """
        attrs = []
        if self.id:
            attrs.append(f"id='{self.id}'")
        if self.name:
            attrs.append(f"name='{self.name}'")

        attr_str = ", ".join(attrs)
        return f"{self.__class__.__name__}({attr_str})"

    @property
    def parent(self) -> Optional["KMLElement"]:
        """
        Get the parent container of this element.

        Returns:
            The parent KML element (usually a Folder) or None if root-level
        """
        return self._parent

    @parent.setter
    def parent(self, value: Optional["KMLElement"]) -> None:
        """
        Set the parent container of this element.

        Args:
            value: The parent KML element or None
        """
        self._parent = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the KML element to a dictionary representation.

        Returns:
            Dictionary with all element attributes
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "visibility": self.visibility,
            "element_type": self.__class__.__name__,
        }

    def update(self, **kwargs: Any) -> None:
        """
        Update multiple attributes at once.

        Args:
            **kwargs: Attribute names and values to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

    def copy(self) -> "KMLElement":
        """
        Create a copy of this KML element.

        Returns:
            A new instance with the same attributes but no parent reference
        """
        # Get all attributes except private ones and parent
        attrs = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                attrs[key] = value

        # Create new instance of the same class
        new_instance = self.__class__(**attrs)
        return new_instance

    def validate(self) -> bool:
        """
        Validate the KML element's data.

        This base implementation performs basic validation. Subclasses
        should override this method to add specific validation logic.

        Returns:
            True if validation passes

        Raises:
            KMLValidationError: If validation fails
        """
        # Basic validation - name should be a string if provided
        if self.name is not None and not isinstance(self.name, str):
            raise KMLValidationError("Name must be a string", field="name", value=self.name)

        # Description should be a string if provided
        if self.description is not None and not isinstance(self.description, str):
            raise KMLValidationError(
                "Description must be a string",
                field="description",
                value=self.description,
            )

        # Visibility should be a boolean
        if not isinstance(self.visibility, bool):
            raise KMLValidationError(
                "Visibility must be a boolean",
                field="visibility",
                value=self.visibility,
            )

        return True
