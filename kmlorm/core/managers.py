"""
Django-style Manager classes for KML elements.

This module provides the KMLManager and RelatedManager classes that
implement the .objects interface and relationship management similar
to Django's ORM managers.
"""

# pylint: disable=too-many-public-methods
from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Optional, TypeVar, Generic, cast


from .exceptions import KMLElementNotFound, KMLMultipleElementsReturned
from .querysets import KMLQuerySet

if TYPE_CHECKING:
    from ..models.base import KMLElement
    from ..models.folder import Folder
    from ..models.placemark import Placemark  # noqa: F401
    from ..models.path import Path  # noqa: F401
    from ..models.polygon import Polygon  # noqa: F401
    from ..models.point import Point  # noqa: F401
    from ..models.multigeometry import MultiGeometry  # noqa: F401

T = TypeVar("T", bound="KMLElement")


class KMLManager(Generic[T]):
    """
    Django-style manager for KML elements.

    Provides the .objects interface that returns QuerySets for chaining
    queries and filtering operations.
    """

    def __init__(self, folders_manager: Optional["KMLManager['Folder']"] = None) -> None:
        """Initialize the manager.

        Args:
            folders_manager: Reference to the folders manager for flattening operations
        """
        self._elements: List[T] = []
        self._model_class: Optional[type] = None
        self._folders_manager = folders_manager

    @property
    def elements(self) -> List[T]:
        """
        Returns a list of KMLElement objects managed by this instance.

        Returns:
            list[KMLElement]: The list of KMLElement objects.
        """
        return self._elements

    @elements.setter
    def elements(self, value: List[T]) -> None:
        """
        Sets the elements for the manager.

        Args:
            value (list[KMLElement]): A list of KMLElement instances to assign.

        Raises:
            TypeError: If any item in the list is not an instance of KMLElement.

        This method assigns a copy of the provided list to the manager's internal elements,
        ensuring all items are valid KMLElement instances.
        """
        # pylint: disable=import-outside-toplevel
        from ..models.base import KMLElement as _KMLElement

        for item in value:
            if not isinstance(item, _KMLElement):
                raise TypeError("Elements assignment must contain only KMLElement instances.")

        self._elements = value.copy()

    def contribute_to_class(self, model_class: type, name: str) -> None:
        """
        Called when manager is attached to a model class.

        Args:
            model_class: The model class this manager belongs to
            name: The attribute name of the manager
        """
        self._model_class = model_class
        setattr(model_class, name, self)

    def get_queryset(self) -> "KMLQuerySet[T]":
        """
        Return a QuerySet containing all elements.

        Returns:
            QuerySet with all managed elements
        """
        return KMLQuerySet(self.elements)

    def all(self, flatten: bool = False) -> "KMLQuerySet[T]":
        """
        Return all elements as a QuerySet.

        Args:
            flatten: If True, recursively include elements from nested folders

        Returns:
            QuerySet containing all elements (flattened if requested)
        """
        if not flatten or not self._folders_manager:
            return self.get_queryset()

        # Collect all elements including those in folders, deduplicated by object id
        all_elements = list(self.elements)
        all_elements.extend(self._collect_folder_elements())
        seen_ids = set()
        deduped = []
        for el in all_elements:
            el_id = id(el)
            if el_id not in seen_ids:
                seen_ids.add(el_id)
                deduped.append(el)
        return KMLQuerySet(deduped)

    def _collect_folder_elements(self) -> List[T]:
        """
        Recursively collect elements of this manager's type from all folders.

        Returns:
            List of elements found in folders
        """
        # Ensure model_class is set for specialized managers
        if hasattr(self, "_set_model_class") and callable(getattr(self, "_set_model_class")):
            getattr(self, "_set_model_class")()
        # Debug: folders_manager and model_class status can be logged here if needed
        elements: List[T] = []

        if not self._folders_manager or not self._model_class:
            return elements

        attribute_name = self._get_manager_attribute_name()
        if not attribute_name:
            return elements

        if attribute_name == "folders":
            # For folders, collect all root and nested folders recursively
            def collect_all_folders(folder: Any, depth: int = 0) -> list:
                # Debug: visiting folder at depth can be logged here if needed
                result = [folder]
                subfolders = getattr(folder, "folders", None)
                if subfolders:
                    for subfolder in subfolders.all():
                        result.extend(collect_all_folders(subfolder, depth + 1))
                return result

            for folder in self._folders_manager.all():
                # Debug: starting recursion from root folder can be logged here if needed
                elements.extend(collect_all_folders(folder))
        else:
            for folder in self._folders_manager.all():
                folder_manager = getattr(folder, attribute_name, None)
                if folder_manager:
                    elements.extend(list(folder_manager.all()))
                elements.extend(self._collect_elements_from_folder(folder, attribute_name))

        return elements

    def _collect_elements_from_folder(self, folder: "KMLElement", attribute_name: str) -> List[T]:
        """
        Recursively collect elements from a folder and its subfolders.

        Args:
            folder: Folder to collect elements from
            attribute_name: Name of the manager attribute (e.g., 'placemarks', 'paths')

        Returns:
            List of elements from folder and subfolders
        """
        elements: List[T] = []
        subfolders = getattr(cast("Folder", folder), "folders", None)
        if not subfolders:
            return elements

        for subfolder in subfolders.all():
            if attribute_name == "folders":
                # For folders, add the subfolder itself
                elements.append(subfolder)
                # And recurse to collect deeper nested folders
                elements.extend(self._collect_elements_from_folder(subfolder, attribute_name))
            else:
                subfolder_manager = getattr(subfolder, attribute_name, None)
                if subfolder_manager:
                    elements.extend(list(subfolder_manager.all()))
                elements.extend(self._collect_elements_from_folder(subfolder, attribute_name))
        return elements

    def _get_manager_attribute_name(self) -> Optional[str]:
        """
        Get the attribute name for this manager's element type.

        Returns:
            Attribute name or None if not found
        """
        # For specialized managers, set model class if not already set
        if hasattr(self, "_set_model_class") and callable(getattr(self, "_set_model_class")):
            getattr(self, "_set_model_class")()

        if not self._model_class:
            return None

        # Map model classes to their manager attribute names
        # pylint: disable=import-outside-toplevel
        from ..models.placemark import Placemark  # noqa: F811
        from ..models.folder import Folder
        from ..models.path import Path  # noqa: F811
        from ..models.polygon import Polygon  # noqa: F811
        from ..models.point import Point  # noqa: F811
        from ..models.multigeometry import MultiGeometry  # noqa: F811

        type_mapping: dict[type, str] = {
            Placemark: "placemarks",
            Folder: "folders",
            Path: "paths",
            Polygon: "polygons",
            Point: "points",
            MultiGeometry: "multigeometries",
        }

        return type_mapping.get(self._model_class)

    def filter(self, **kwargs: Any) -> "KMLQuerySet[T]":
        """
        Filter elements based on field lookups.

        Args:
            **kwargs: Field lookup expressions

        Returns:
            Filtered QuerySet
        """
        return self.get_queryset().filter(**kwargs)

    def exclude(self, **kwargs: Any) -> "KMLQuerySet[T]":
        """
        Exclude elements that match the given filters.

        Args:
            **kwargs: Field lookup expressions

        Returns:
            QuerySet with non-matching elements
        """
        return self.get_queryset().exclude(**kwargs)

    def get(self, **kwargs: Any) -> T:
        """
        Get a single element that matches the criteria.

        Args:
            **kwargs: Field lookup expressions

        Returns:
            Single matching element

        Raises:
            KMLElementNotFound: If no elements match
            KMLMultipleElementsReturned: If multiple elements match
        """
        return self.get_queryset().get(**kwargs)

    def first(self) -> "Optional[T]":
        """
        Get the first element.

        Returns:
            First element or None if empty
        """
        return self.get_queryset().first()

    def last(self) -> "Optional[T]":
        """
        Get the last element.

        Returns:
            Last element or None if empty
        """
        return self.get_queryset().last()

    def count(self) -> int:
        """
        Count the number of elements.

        Returns:
            Number of elements
        """
        return len(self.elements)

    def exists(self) -> bool:
        """
        Check if any elements exist.

        Returns:
            True if elements exist
        """
        return bool(self.elements)

    def none(self) -> "KMLQuerySet[T]":
        """
        Return an empty QuerySet.

        Returns:
            Empty QuerySet
        """
        return cast("KMLQuerySet[T]", KMLQuerySet([]))

    def order_by(self, *fields: str) -> "KMLQuerySet[T]":
        """
        Order elements by the given fields.

        Args:
            *fields: Field names to order by

        Returns:
            Ordered QuerySet
        """
        return self.get_queryset().order_by(*fields)

    # Geospatial query methods

    def near(
        self, longitude: float, latitude: float, radius_km: Optional[float] = None
    ) -> "KMLQuerySet[T]":
        """
        Find elements near given coordinates.

        Args:
            longitude: Center longitude
            latitude: Center latitude
            radius_km: Search radius in kilometers

        Returns:
            QuerySet with nearby elements
        """
        return self.get_queryset().near(longitude, latitude, radius_km)

    def within_bounds(
        self, north: float, south: float, east: float, west: float
    ) -> "KMLQuerySet[T]":
        """
        Find elements within a bounding box.

        Args:
            north: Northern boundary
            south: Southern boundary
            east: Eastern boundary
            west: Western boundary

        Returns:
            QuerySet with elements in bounds
        """
        return self.get_queryset().within_bounds(north, south, east, west)

    def has_coordinates(self) -> "KMLQuerySet[T]":
        """
        Find elements that have coordinate data.

        Returns:
            QuerySet with elements having coordinates
        """
        return self.get_queryset().has_coordinates()

    def valid_coordinates(self) -> "KMLQuerySet[T]":
        """
        Find elements with valid coordinate ranges.

        Returns:
            QuerySet with valid coordinates
        """
        return self.get_queryset().valid_coordinates()

    # Element management methods

    def add(self, *elements: T) -> None:
        """
        Add elements to this manager.

        Args:
            *elements: KML elements to add
        """
        for element in elements:
            if element not in self.elements:
                self._elements.append(element)

    def remove(self, *elements: T) -> None:
        """
        Remove elements from this manager.

        Args:
            *elements: KML elements to remove
        """
        for element in elements:
            if element in self._elements:
                self._elements.remove(element)

    def clear(self) -> None:
        """Remove all elements from this manager."""
        self._elements.clear()

    def create(self, **kwargs: Any) -> T:
        """
        Create a new element and add it to this manager.

        Args:
            **kwargs: Element attributes

        Returns:
            Newly created element

        Raises:
            TypeError: If no model class is set
        """
        if not self._model_class:
            raise TypeError("Cannot create element without model class")

        element = cast(T, self._model_class(**kwargs))
        self.add(element)
        return element

    def get_or_create(self, **kwargs: Any) -> tuple[T, bool]:
        """
        Get an existing element or create a new one.

        Args:
            **kwargs: Element attributes

        Returns:
            Tuple of (element, created) where created is True if element was created
        """
        try:
            element = self.get(**kwargs)
            return element, False
        except (KMLElementNotFound, KMLMultipleElementsReturned):
            element = self.create(**kwargs)
            return element, True

    def bulk_create(self, elements: List[T]) -> List[T]:
        """
        Add multiple elements efficiently.

        Args:
            elements: List of elements to add

        Returns:
            List of added elements
        """
        self._elements.extend(elements)
        return elements


class FolderManager(KMLManager["Folder"]):
    """
    Manager class for handling Folder model instances within the KML ORM framework.

    This class extends KMLManager to provide specialized management for Folder objects,
    including creation and model class resolution.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.

        If the internal `_model_class` attribute is `None`, this method imports the `Folder` model
        and assigns it to `_model_class`. This ensures that the manager is associated with the
        correct model.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.folder import Folder

            self._model_class = Folder

    def create(self, **kwargs: Any) -> "Folder":
        """
        Creates and returns a new instance of the Folder model using the provided keyword arguments.

        This method ensures the model class is set before delegating the creation process
        to the parent class.

        Args:
            **kwargs (Any): Arbitrary keyword arguments representing the fields and values for
            the new Folder instance.

        Returns:
            Folder: The newly created Folder instance.
        """

        self._set_model_class()
        return super().create(**kwargs)


class PlacemarkManager(KMLManager["Placemark"]):
    """
    Manager class for handling Placemark objects within a KML structure.

    This class provides methods to create and manage Placemark instances,
    optionally associating them with a Folders manager. It ensures the correct
    model class is set before performing operations.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.

        This method checks if the internal `_model_class` attribute is `None`. If so, it imports
        the `Placemark` model from the appropriate module and assigns it to `_model_class`.
        This ensures that the manager is associated with the correct model class before
        performing any operations that require it.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.placemark import Placemark

            self._model_class = Placemark

    def create(self, **kwargs: Any) -> "Placemark":
        """
        Creates a new Placemark instance with the given keyword arguments and adds it to
        the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the Placemark instance.

        Returns:
            Placemark: The newly created Placemark object.
        """
        self._set_model_class()
        return super().create(**kwargs)


class PathManager(KMLManager["Path"]):
    """
    Manager class for handling operations related to the 'Path' model.

    This class extends KMLManager to provide specialized management for 'Path' objects,
    including creation and model class setup.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.

        This method checks if the internal `_model_class` attribute is `None`.
        If so, it imports the `Path` model from the parent module's `models.path`
        and assigns it to `_model_class`. This ensures that the manager is
        associated with the correct model class before performing any operations.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.path import Path

            self._model_class = Path

    def create(self, **kwargs: Any) -> "Path":
        """
        Creates a new instance of the Path model with the provided keyword arguments and adds
        it to the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments corresponding to the fields of the
                Path model.

        Returns:
            Path: The newly created Path instance.
        """
        self._set_model_class()
        return super().create(**kwargs)


class PolygonManager(KMLManager["Polygon"]):
    """
    Manager class for handling Polygon model instances within the KML ORM framework.

    This class extends KMLManager to provide specialized management for Polygon objects,
    including creation and association with optional Folder managers.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.

        This method checks if the internal `_model_class` attribute is `None`.
        If so, it imports the `Polygon` model from the appropriate module and assigns
        it to `_model_class`.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.polygon import Polygon

            self._model_class = Polygon

    def create(self, **kwargs: Any) -> "Polygon":
        """
        Creates and returns a new instance of the Polygon model using the provided keyword
        arguments.

        This method ensures the model class is set before delegating the creation process
        to the superclass.

        Args:
            **kwargs (Any): Arbitrary keyword arguments corresponding to the Polygon model fields.

        Returns:
            Polygon: The newly created Polygon instance.
        """
        self._set_model_class()
        return super().create(**kwargs)


class PointManager(KMLManager["Point"]):
    """
    Manager class for handling Point model instances within the KML ORM framework.

    This class extends KMLManager to provide specialized management for Point objects,
    including creation and model class resolution.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.

        This method checks if the internal `_model_class` attribute is `None`.
        If so, it imports the `Point` model from the appropriate module and assigns
        it to `_model_class`. This ensures that the manager is associated with the
        correct model class before performing any operations.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.point import Point

            self._model_class = Point

    def create(self, **kwargs: Any) -> "Point":
        """
        Creates a new Point instance with the given keyword arguments and adds it to the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the Point instance.

        Returns:
            Point: The newly created Point object.
        """
        self._set_model_class()
        return super().create(**kwargs)


class MultiGeometryManager(KMLManager["MultiGeometry"]):
    """
    Manager class for handling MultiGeometry objects within the KML ORM framework.

    This class extends KMLManager to provide specialized management for MultiGeometry instances,
    including creation and model class resolution.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.

        This method checks if the internal `_model_class` attribute is `None`. If so,
        it imports the `MultiGeometry` class from the models module and assigns it to
        `_model_class`. This ensures that the manager is associated with the correct
        model class before performing further operations.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.multigeometry import MultiGeometry

            self._model_class = MultiGeometry

    def create(self, **kwargs: Any) -> "MultiGeometry":
        """
        Creates a new MultiGeometry instance with the given keyword arguments and
            adds it to the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the
                MultiGeometry instance.

        Returns:
            MultiGeometry: The newly created MultiGeometry object.
        """
        self._set_model_class()
        return super().create(**kwargs)


class RelatedManager(KMLManager[T]):
    """
    Manager for related objects (e.g., folder.placemarks).

    Extends KMLManager with relationship-specific functionality
    for managing collections of related KML elements.
    """

    def __init__(self, parent: Optional["KMLElement"] = None, related_name: str = "") -> None:
        """
        Initialize a RelatedManager.

        Args:
            parent: The optional parent instance (set at runtime for per-instance managers)
            related_name: Name of the relationship field
        """
        super().__init__()
        self._parent: Optional["KMLElement"] = parent
        self._related_name = related_name

    def add(self, *elements: T) -> None:
        """
        Add elements to this relationship.

        Args:
            *elements: KML elements to add
        """
        super().add(*elements)
        # Set parent reference on added elements
        if self._parent is not None:
            for element in elements:
                element.parent = self._parent

    def remove(self, *elements: T) -> None:
        """
        Remove elements from this relationship.

        Args:
            *elements: KML elements to remove
        """
        super().remove(*elements)
        # Clear parent reference on removed elements
        if self._parent is not None:
            for element in elements:
                if element.parent == self._parent:
                    element.parent = None

    def create(self, **kwargs: Any) -> T:
        """
        Create a new related element.

        Args:
            **kwargs: Element attributes

        Returns:
            Newly created element with parent set
        """

        element = super().create(**kwargs)
        if self._parent is not None:
            element.parent = self._parent
        return element


class FolderRelatedManager(RelatedManager["Folder"]):
    """
    Manager for handling operations related to Folder model relationships.

    This class extends RelatedManager to provide additional functionality
    or customization for managing related Folder instances.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.folder import Folder

            self._model_class = Folder

    def create(self, **kwargs: Any) -> "Folder":
        """
        Creates a new Folder instance with the given keyword arguments and adds it to
        the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the Folder instance.

        Returns:
            Folder: The newly created Folder object.
        """
        self._set_model_class()
        return super().create(**kwargs)


class PlacemarkRelatedManager(RelatedManager["Placemark"]):
    """
    Manager for handling related Placemark objects.

    This class extends the RelatedManager specifically for Placemark instances,
    providing an interface to manage and query related Placemark objects within
    the ORM context.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.placemark import Placemark

            self._model_class = Placemark

    def create(self, **kwargs: Any) -> "Placemark":
        """
        Creates a new Placemark instance with the given keyword arguments and adds it to
        the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the Placemark instance.

        Returns:
            Placemark: The newly created Placemark object.
        """
        self._set_model_class()
        return super().create(**kwargs)


class PathRelatedManager(RelatedManager["Path"]):
    """
    A specialized RelatedManager for handling relationships involving the Path model.

    This manager provides custom query and management capabilities for related Path objects.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.path import Path

            self._model_class = Path

    def create(self, **kwargs: Any) -> "Path":
        """
        Creates a new Path instance with the given keyword arguments and adds it to
        the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the Path instance.

        Returns:
            Path: The newly created Path object.
        """
        self._set_model_class()
        return super().create(**kwargs)


class PolygonRelatedManager(RelatedManager["Polygon"]):
    """
    Manager for handling relationships and queries related to the Polygon model.

    This class extends RelatedManager specifically for Polygon instances,
    enabling custom query and relationship management for polygons within the ORM.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.polygon import Polygon

            self._model_class = Polygon

    def create(self, **kwargs: Any) -> "Polygon":
        """
        Creates a new Polygon instance with the given keyword arguments and adds it to
        the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the Polygon instance.

        Returns:
            Polygon: The newly created Polygon object.
        """
        self._set_model_class()
        return super().create(**kwargs)


class PointRelatedManager(RelatedManager["Point"]):
    """
    A specialized RelatedManager for handling relationships involving Point objects.

    This manager provides an interface for managing and querying related Point instances
    within the ORM.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.point import Point

            self._model_class = Point

    def create(self, **kwargs: Any) -> "Point":
        """
        Creates a new Point instance with the given keyword arguments and adds it to
        the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the Point instance.

        Returns:
            Point: The newly created Point object.
        """
        self._set_model_class()
        return super().create(**kwargs)


class MultiGeometryRelatedManager(RelatedManager["MultiGeometry"]):
    """
    Manager for handling related objects of the MultiGeometry model.

    This class extends the generic RelatedManager to provide relationship management
    functionality specifically for MultiGeometry instances.
    """

    def _set_model_class(self) -> None:
        """
        Sets the model class for the manager if it has not been set already.
        """
        # pylint: disable=import-outside-toplevel
        if self._model_class is None:
            from ..models.multigeometry import MultiGeometry

            self._model_class = MultiGeometry

    def create(self, **kwargs: Any) -> "MultiGeometry":
        """
        Creates a new MultiGeometry instance with the given keyword arguments and adds it to
        the manager.

        Args:
            **kwargs (Any): Arbitrary keyword arguments used to initialize the
                MultiGeometry instance.

        Returns:
            MultiGeometry: The newly created MultiGeometry object.
        """
        self._set_model_class()
        return super().create(**kwargs)
