"""
Django-style Manager classes for KML elements.

This module provides the KMLManager and RelatedManager classes that
implement the .objects interface and relationship management similar
to Django's ORM managers.
"""

# pylint: disable=too-many-public-methods, too-many-lines
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
        # Set by KMLFile for geometry managers to access root placemarks
        self._placemarks_manager: Optional["KMLManager[Any]"] = None

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

    def all(self) -> "KMLQuerySet[T]":
        """
        Return all elements as a QuerySet, including those in nested folders.

        Returns:
            QuerySet containing all elements including those in nested folders

        Example:
            >>> # Get all placemarks including those in nested folders
            >>> all_placemarks = kml.placemarks.all()
            >>>
            >>> # For direct children only, use .children()
            >>> root_placemarks = kml.placemarks.children()
        """
        # Start with direct children
        all_elements = list(self.elements)

        # If we have a folders manager (KML root case), use the existing logic
        if self._folders_manager:
            all_elements.extend(self._collect_nested_elements())
        # If we have a parent (folder case), collect from nested containers
        elif (
            hasattr(self, "_parent")
            and getattr(self, "_parent", None)
            and hasattr(getattr(self, "_parent"), "folders")
        ):
            all_elements.extend(self._collect_from_parent_containers())

        # Deduplicate elements
        return self._deduplicate_elements(all_elements)

    def _collect_from_parent_containers(self) -> List[T]:
        """
        Collect elements from parent's nested containers (folders, etc.).

        Returns:
            List of elements from nested containers
        """
        elements: List[T] = []
        attribute_name = self._get_manager_attribute_name()
        if not attribute_name:
            return elements

        parent = getattr(self, "_parent")
        parent_folders = getattr(parent, "folders", None)
        if not parent_folders:
            return elements

        if attribute_name == "folders":
            # For folders, get all nested folders
            for folder in parent_folders.children():
                elements.append(cast(T, folder))
                # Recursively get nested folders
                subfolder_manager = getattr(folder, "folders", None)
                if subfolder_manager:
                    elements.extend(subfolder_manager.all())
        else:
            # For other element types, collect from all nested folders
            for folder in parent_folders.children():
                # Get elements from this folder
                folder_manager = getattr(folder, attribute_name, None)
                if folder_manager:
                    elements.extend(list(folder_manager.children()))
                # Recursively collect from nested folders
                subfolder_manager = getattr(folder, "folders", None)
                if subfolder_manager:
                    all_nested_folders = subfolder_manager.all()
                    for nested_folder in all_nested_folders:
                        nested_manager = getattr(nested_folder, attribute_name, None)
                        if nested_manager:
                            elements.extend(list(nested_manager.children()))

        return elements

    def _deduplicate_elements(self, elements: List[T]) -> "KMLQuerySet[T]":
        """
        Remove duplicate elements from list.

        Args:
            elements: List of elements that may contain duplicates

        Returns:
            QuerySet with unique elements
        """
        seen_ids = set()
        deduped = []
        for el in elements:
            el_id = id(el)
            if el_id not in seen_ids:
                seen_ids.add(el_id)
                deduped.append(el)
        return KMLQuerySet(deduped)

    def children(self) -> "KMLQuerySet[T]":
        """
        Return only direct child elements as a QuerySet.

        This method returns elements that are direct children of the current
        container, without traversing into nested folders. This provides the
        same behavior as the current .all() method without the flatten parameter.

        Returns:
            QuerySet containing only direct child elements

        Example:
            >>> # Get only placemarks directly in the KML file root
            >>> root_placemarks = kml_file.placemarks.children()
            >>>
            >>> # Get only folders directly in the current folder
            >>> direct_subfolders = folder.folders.children()
            >>>
            >>> # Chain with other QuerySet methods
            >>> visible_root_placemarks = kml_file.placemarks.children().filter(visibility=True)
        """
        return self.get_queryset()

    def _collect_nested_elements(self) -> List[T]:
        """
        Recursively collect elements of this manager's type from nested containers.

        This method collects elements from folders and other containers in the
        hierarchy. Subclasses can override this to customize collection behavior
        (e.g., PointManager collecting Points from both folders and Placemarks).

        Returns:
            List of elements found in nested containers
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
            # For folders, use recursive .all() on the folders manager itself
            # This will properly collect all nested folders
            for folder in self._folders_manager.children():
                # Add the folder itself
                elements.append(cast(T, folder))
                # Recursively collect all nested folders
                subfolder_manager = getattr(folder, "folders", None)
                if subfolder_manager:
                    # Use .all() recursively to get all nested folders
                    elements.extend(subfolder_manager.all())
        else:
            # For other element types, we need to:
            # 1. Get elements from direct child folders
            # 2. Recursively get elements from ALL nested folders

            # First, collect from direct child folders
            for folder in self._folders_manager.children():
                folder_manager = getattr(folder, attribute_name, None)
                if folder_manager:
                    elements.extend(list(folder_manager.children()))

                # Then recursively collect from all nested subfolders
                subfolder_manager = getattr(folder, "folders", None)
                if subfolder_manager:
                    # Get ALL nested folders (not just direct children)
                    all_nested_folders = subfolder_manager.all()
                    for nested_folder in all_nested_folders:
                        nested_manager = getattr(nested_folder, attribute_name, None)
                        if nested_manager:
                            elements.extend(list(nested_manager.children()))

        return elements

    def _collect_from_placemarks_and_multigeometries(
        self, placemarks: "KMLQuerySet[Any]", geometry_type: str
    ) -> List[T]:
        """
        Helper method to collect geometries from Placemarks and their MultiGeometries.

        This method extracts geometries of a specific type from:
        1. Direct geometry properties on Placemarks (e.g., placemark.point)
        2. MultiGeometry containers within Placemarks

        Args:
            placemarks: QuerySet of Placemark objects to search
            geometry_type: Type of geometry to collect ('points', 'paths', 'polygons')

        Returns:
            List of geometry objects of the specified type
        """
        geometries: List[T] = []

        # Map geometry types to Placemark attributes and MultiGeometry methods
        geometry_mappings = {
            "points": ("point", "get_points"),
            "paths": ("path", "get_paths"),
            "polygons": ("polygon", "get_polygons"),
        }

        if geometry_type not in geometry_mappings:
            return geometries

        attr_name, multigeom_method = geometry_mappings[geometry_type]

        for placemark in placemarks:
            # Check for direct geometry property
            if hasattr(placemark, attr_name):
                geometry = getattr(placemark, attr_name, None)
                if geometry:
                    geometries.append(geometry)

            # Check for MultiGeometry containing this geometry type
            if hasattr(placemark, "multigeometry") and placemark.multigeometry:
                getter = getattr(placemark.multigeometry, multigeom_method, None)
                if getter and callable(getter):
                    result = getter()
                    if isinstance(result, list):
                        geometries.extend(result)

        return geometries

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

    def _collect_nested_elements(self) -> List["Path"]:
        """
        Override to collect Paths from ALL sources at root level.

        Paths can exist as:
        1. Direct children of folders (standalone LineStrings)
        2. Inside Placemarks (as LineString elements that become Paths)
        3. Inside MultiGeometry (both standalone and in Placemarks)

        Returns:
            List of all Paths found in nested containers
        """
        # First get Paths using the base implementation (standalone Paths in folders)
        paths = super()._collect_nested_elements()

        # Collect from root-level placemarks if available
        if hasattr(self, "_placemarks_manager") and self._placemarks_manager:
            paths.extend(
                self._collect_from_placemarks_and_multigeometries(
                    self._placemarks_manager.all(), "paths"
                )
            )

        # For PathManager at root level, collect from all folders' placemarks
        if self._folders_manager:
            for folder in self._folders_manager.all():
                if hasattr(folder, "placemarks"):
                    paths.extend(
                        self._collect_from_placemarks_and_multigeometries(
                            folder.placemarks.all(), "paths"
                        )
                    )

        return paths


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

    def _collect_nested_elements(self) -> List["Polygon"]:
        """
        Override to collect Polygons from ALL sources at root level.

        Polygons can exist as:
        1. Direct children of folders (standalone Polygons)
        2. Inside Placemarks (as placemark.polygon property)
        3. Inside MultiGeometry (both standalone and in Placemarks)

        Returns:
            List of all Polygons found in nested containers
        """
        # First get Polygons using the base implementation (standalone Polygons in folders)
        polygons = super()._collect_nested_elements()

        # Collect from root-level placemarks if available
        if hasattr(self, "_placemarks_manager") and self._placemarks_manager:
            polygons.extend(
                self._collect_from_placemarks_and_multigeometries(
                    self._placemarks_manager.all(), "polygons"
                )
            )

        # For PolygonManager at root level, collect from all folders' placemarks
        if self._folders_manager:
            for folder in self._folders_manager.all():
                if hasattr(folder, "placemarks"):
                    polygons.extend(
                        self._collect_from_placemarks_and_multigeometries(
                            folder.placemarks.all(), "polygons"
                        )
                    )

        return polygons


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

    def _collect_nested_elements(self) -> List["Point"]:
        """
        Override to collect Points from ALL sources at root level.

        Points can exist as:
        1. Direct children of folders (standalone Points)
        2. Inside Placemarks (as placemark.point property)
        3. Inside MultiGeometry (both standalone and in Placemarks)

        Returns:
            List of all Points found in nested containers
        """
        # First get Points using the base implementation (standalone Points in folders)
        points = super()._collect_nested_elements()

        # Collect from root-level placemarks if available
        if hasattr(self, "_placemarks_manager") and self._placemarks_manager:
            points.extend(
                self._collect_from_placemarks_and_multigeometries(
                    self._placemarks_manager.all(), "points"
                )
            )

        # For PointManager at root level, collect from all folders' placemarks
        if self._folders_manager:
            for folder in self._folders_manager.all():
                if hasattr(folder, "placemarks"):
                    points.extend(
                        self._collect_from_placemarks_and_multigeometries(
                            folder.placemarks.all(), "points"
                        )
                    )

        return points


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

    def _collect_nested_elements(self) -> List["Path"]:
        """
        Override to collect Paths from ALL sources at folder level.

        Paths can exist as:
        1. Direct children of folders (standalone LineStrings)
        2. Inside Placemarks (as placemark.path property)
        3. Inside MultiGeometry (both standalone and in Placemarks)

        Returns:
            List of all Paths found in nested containers
        """
        # First get Paths using the base implementation (standalone Paths in folders)
        paths = super()._collect_nested_elements()

        # PathRelatedManager is used for folders, so _parent is the folder itself
        parent = getattr(self, "_parent", None)
        if parent:
            # Get Paths from placemarks in this folder (direct children)
            if hasattr(parent, "placemarks"):
                paths.extend(
                    self._collect_from_placemarks_and_multigeometries(
                        parent.placemarks.children(), "paths"
                    )
                )

            # Get Paths from placemarks in nested folders
            if hasattr(parent, "folders"):
                for folder in parent.folders.all():
                    if hasattr(folder, "placemarks"):
                        paths.extend(
                            self._collect_from_placemarks_and_multigeometries(
                                folder.placemarks.all(), "paths"
                            )
                        )

        return paths

    def _collect_from_parent_containers(self) -> List["Path"]:
        """
        Override to collect Paths from parent's Placemarks as well as folders.

        Returns:
            List of Paths from parent's nested containers
        """
        # Get Paths from folders using base implementation
        paths = super()._collect_from_parent_containers()

        # Also collect Paths from parent's placemarks
        parent = getattr(self, "_parent", None)
        if parent:
            # Get Paths from direct placemarks in parent
            if hasattr(parent, "placemarks"):
                paths.extend(
                    self._collect_from_placemarks_and_multigeometries(
                        parent.placemarks.children(), "paths"
                    )
                )

            # Get Paths from placemarks in nested folders
            if hasattr(parent, "folders"):
                for folder in parent.folders.all():
                    if hasattr(folder, "placemarks"):
                        paths.extend(
                            self._collect_from_placemarks_and_multigeometries(
                                folder.placemarks.all(), "paths"
                            )
                        )

        return paths


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

    def _collect_nested_elements(self) -> List["Polygon"]:
        """
        Override to collect Polygons from ALL sources at folder level.

        Polygons can exist as:
        1. Direct children of folders (standalone Polygons)
        2. Inside Placemarks (as placemark.polygon property)
        3. Inside MultiGeometry (both standalone and in Placemarks)

        Returns:
            List of all Polygons found in nested containers
        """
        # First get Polygons using the base implementation (standalone Polygons in folders)
        polygons = super()._collect_nested_elements()

        # PolygonRelatedManager is used for folders, so _parent is the folder itself
        parent = getattr(self, "_parent", None)
        if parent:
            # Get Polygons from placemarks in this folder (direct children)
            if hasattr(parent, "placemarks"):
                polygons.extend(
                    self._collect_from_placemarks_and_multigeometries(
                        parent.placemarks.children(), "polygons"
                    )
                )

            # Get Polygons from placemarks in nested folders
            if hasattr(parent, "folders"):
                for folder in parent.folders.all():
                    if hasattr(folder, "placemarks"):
                        polygons.extend(
                            self._collect_from_placemarks_and_multigeometries(
                                folder.placemarks.all(), "polygons"
                            )
                        )

        return polygons

    def _collect_from_parent_containers(self) -> List["Polygon"]:
        """
        Override to collect Polygons from parent's Placemarks as well as folders.

        Returns:
            List of Polygons from parent's nested containers
        """
        # Get Polygons from folders using base implementation
        polygons = super()._collect_from_parent_containers()

        # Also collect Polygons from parent's placemarks
        parent = getattr(self, "_parent", None)
        if parent:
            # Get Polygons from direct placemarks in parent
            if hasattr(parent, "placemarks"):
                polygons.extend(
                    self._collect_from_placemarks_and_multigeometries(
                        parent.placemarks.children(), "polygons"
                    )
                )

            # Get Polygons from placemarks in nested folders
            if hasattr(parent, "folders"):
                for folder in parent.folders.all():
                    if hasattr(folder, "placemarks"):
                        polygons.extend(
                            self._collect_from_placemarks_and_multigeometries(
                                folder.placemarks.all(), "polygons"
                            )
                        )

        return polygons


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

    def _collect_nested_elements(self) -> List["Point"]:
        """
        Override to collect Points from ALL sources at folder level.

        Points can exist as:
        1. Direct children of folders (standalone Points)
        2. Inside Placemarks (as placemark.point property)
        3. Inside MultiGeometry (both standalone and in Placemarks)

        Returns:
            List of all Points found in nested containers
        """
        # First get Points using the base implementation (standalone Points in folders)
        points = super()._collect_nested_elements()

        # PointRelatedManager is used for folders, so _parent is the folder itself
        parent = getattr(self, "_parent", None)
        if parent:
            # Get Points from placemarks in this folder (direct children)
            if hasattr(parent, "placemarks"):
                points.extend(
                    self._collect_from_placemarks_and_multigeometries(
                        parent.placemarks.children(), "points"
                    )
                )

            # Get Points from placemarks in nested folders
            if hasattr(parent, "folders"):
                for folder in parent.folders.all():
                    if hasattr(folder, "placemarks"):
                        points.extend(
                            self._collect_from_placemarks_and_multigeometries(
                                folder.placemarks.all(), "points"
                            )
                        )

        return points

    def _collect_from_parent_containers(self) -> List["Point"]:
        """
        Override to collect Points from parent's Placemarks as well as folders.

        Returns:
            List of Points from parent's nested containers
        """
        # Get Points from folders using base implementation
        points = super()._collect_from_parent_containers()

        # Also collect Points from parent's placemarks
        parent = getattr(self, "_parent", None)
        if parent:
            # Get Points from direct placemarks in parent
            if hasattr(parent, "placemarks"):
                points.extend(
                    self._collect_from_placemarks_and_multigeometries(
                        parent.placemarks.children(), "points"
                    )
                )

            # Get Points from placemarks in nested folders
            if hasattr(parent, "folders"):
                for folder in parent.folders.all():
                    if hasattr(folder, "placemarks"):
                        points.extend(
                            self._collect_from_placemarks_and_multigeometries(
                                folder.placemarks.all(), "points"
                            )
                        )

        return points


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
