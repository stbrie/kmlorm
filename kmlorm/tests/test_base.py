"""
Unit tests for the KMLElement base class functionality.
Classes:
    _TestElement: A test subclass of KMLElement, marked as abstract to avoid manager attachment.
Test Cases:
    TestBase:
        - test_str_and_repr_variants: Verifies __str__ and __repr__ output for elements with
            and without names/IDs.
        - test_parent_property_and_to_dict_and_copy: Tests parent property, to_dict serialization,
            and copy behavior.
        - test_update_success_and_missing_attribute_raises: Checks attribute update functionality
            and error handling for missing attributes.
        - test_validate_happy_and_error_cases: Validates correct and incorrect field types,
            ensuring KMLValidationError is raised as expected.
"""

from typing import Any

import pytest

from kmlorm.models.base import KMLElement
from kmlorm.core.exceptions import KMLValidationError


class _TestElement(KMLElement):
    """
    _TestElement is an abstract subclass of KMLElement intended for testing purposes.
    It sets the `_abstract` attribute to True to prevent the metaclass from attaching managers.
    The constructor accepts arbitrary keyword arguments and delegates handling of common
    fields to the base class.
    """

    # Make this class 'abstract' for the metaclass to avoid attaching managers
    _abstract = True

    def __init__(self, **kwargs: Any) -> None:
        # Accept arbitrary kwargs and let base class handle common fields
        super().__init__(**kwargs)


class TestBase:
    """
    Test suite for the _TestElement class, verifying its core behaviors:

    - test_str_and_repr_variants: Ensures correct string and repr representations
        based on element attributes.
    - test_parent_property_and_to_dict_and_copy: Tests parent assignment,
        dictionary conversion, and deep copying of elements.
    - test_update_success_and_missing_attribute_raises: Validates attribute
        updating and error handling for invalid attributes.
    - test_validate_happy_and_error_cases: Checks validation logic for correct
        and incorrect attribute types, raising appropriate exceptions.
    """

    def test_str_and_repr_variants(self) -> None:
        """
        Tests the string and representation variants of the _TestElement class.

        Verifies that:
        - When a name is provided, str returns the name and repr includes the name.
        - When only an element_id is provided, str returns the class name and id, and repr
            includes the id.
        - When neither name nor element_id is provided, str returns the class name with 'unnamed'.
        """
        e1 = _TestElement(element_id="1", name="MyName")
        assert str(e1) == "MyName"
        assert "name='MyName'" in repr(e1)

        e2 = _TestElement(element_id="2")
        assert str(e2) == f"{e2.__class__.__name__}(2)"
        assert "id='2'" in repr(e2)

        e3 = _TestElement()
        assert str(e3) == f"{e3.__class__.__name__}(unnamed)"

    def test_parent_property_and_to_dict_and_copy(self) -> None:
        """
        Tests the behavior of the parent property, to_dict method, and copy method
            of the _TestElement class.

        - Verifies that the parent property can be set and retrieved correctly.
        - Checks that the to_dict method returns a dictionary with the expected attributes
            and values.
        - Ensures that the copy method creates a new instance with duplicated attributes
            (excluding parent and private attributes), and that custom attributes are also copied.
        """
        parent = _TestElement(element_id="p", name="Parent")
        child = _TestElement(
            element_id="c", name="Child", description="d", visibility=False, extra=123
        )

        # parent default
        assert child.parent is None
        child.parent = parent
        assert child.parent is parent

        d = child.to_dict()
        assert d["id"] == "c"
        assert d["name"] == "Child"
        assert d["description"] == "d"
        assert d["visibility"] is False
        assert d["element_type"] == child.__class__.__name__

        # copy should duplicate attributes (except parent and private attrs)
        copy = child.copy()
        assert isinstance(copy, _TestElement)
        assert copy is not child
        assert copy.parent is None
        # copied attributes preserved
        assert copy.id == child.id
        assert copy.name == child.name
        assert copy.description == child.description
        assert copy.visibility == child.visibility
        # extra attribute should be copied
        assert getattr(copy, "extra") == 123

    def test_update_success_and_missing_attribute_raises(self) -> None:
        """
        Tests the `update` method of `_TestElement` for correct attribute updating and error
        handling.

        - Verifies that existing attributes (`name`, `description`) are updated successfully.
        - Asserts that attempting to update a non-existent attribute (`not_an_attr`) raises
            an `AttributeError`.
        """
        e = _TestElement(element_id="x", name="Old", description="old")
        e.update(name="New", description="new")
        assert e.name == "New"
        assert e.description == "new"

        with pytest.raises(AttributeError):
            e.update(not_an_attr=1)

    def test_validate_happy_and_error_cases(self) -> None:
        """
        Tests the `validate` method of the `_TestElement` class for both valid and invalid cases.

        - Verifies that a correctly initialized element passes validation.
        - Checks that setting `name` to a non-string value raises `KMLValidationError`.
        - Checks that setting `description` to a non-string value raises `KMLValidationError`.
        - Checks that setting `visibility` to a non-boolean value raises `KMLValidationError`.
        """
        # valid element
        e = _TestElement(name="n", description="d", visibility=True)
        assert e.validate() is True

        # invalid name
        e.name = 123  # type: ignore[assignment]
        with pytest.raises(KMLValidationError):
            e.validate()

        e.name = "n"
        # invalid description
        e.description = 456  # type: ignore[assignment]
        with pytest.raises(KMLValidationError):
            e.validate()

        e.description = "d"
        # invalid visibility
        e.visibility = "yes"  # type: ignore[assignment]
        with pytest.raises(KMLValidationError):
            e.validate()
