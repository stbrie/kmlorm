"""
Compatibility tests for API transition from flatten=True to .children() method.

This test module ensures that the transition from the old API to the new API
maintains backward compatibility and doesn't break existing functionality.
"""

# pylint: disable=duplicate-code, too-many-public-methods

import time
import warnings
from typing import List, TYPE_CHECKING, Union

import pytest

from kmlorm import KMLFile

if TYPE_CHECKING:
    from kmlorm.models.folder import Folder
    from kmlorm.models.placemark import Placemark


# Test data for compatibility testing
COMPLEX_KML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Transition Test Document</name>

        <!-- Root level elements -->
        <Placemark>
            <name>Root Placemark 1</name>
            <Point>
                <coordinates>-122.0856545755255,37.42243077405461,0</coordinates>
            </Point>
        </Placemark>
        <Placemark>
            <name>Root Placemark 2</name>
            <Point>
                <coordinates>-122.084075,37.4220033612141,0</coordinates>
            </Point>
        </Placemark>

        <!-- Nested structure -->
        <Folder>
            <name>Level 1 Folder A</name>
            <Placemark>
                <name>L1A Placemark 1</name>
                <Point>
                    <coordinates>-122.085075,37.4230033612141,0</coordinates>
                </Point>
            </Placemark>
            <Placemark>
                <name>L1A Placemark 2</name>
                <Point>
                    <coordinates>-122.086075,37.4240033612141,0</coordinates>
                </Point>
            </Placemark>

            <Folder>
                <name>Level 2 Folder AA</name>
                <Placemark>
                    <name>L2AA Placemark 1</name>
                    <Point>
                        <coordinates>-122.087075,37.4250033612141,0</coordinates>
                    </Point>
                </Placemark>
            </Folder>
        </Folder>

        <Folder>
            <name>Level 1 Folder B</name>
            <Placemark>
                <name>L1B Placemark 1</name>
                <Point>
                    <coordinates>-122.088075,37.4260033612141,0</coordinates>
                </Point>
            </Placemark>
        </Folder>
    </Document>
</kml>"""

# Empty KML for edge case testing
EMPTY_KML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Empty Document</name>
    </Document>
</kml>"""


class TestAPITransitionCompatibility:
    """
    Test suite for verifying API transition compatibility in kmlorm.

    This class contains comprehensive tests to ensure the transition from the deprecated
    `.all(flatten=True/False)` API to the new `.all()` and `.children()` methods is smooth,
    backward compatible, and well-documented. It covers baseline behavior, deprecation warnings,
    migration guidance, performance, memory usage, edge cases, and documentation patterns.

    Key areas tested:
    - New `.all()` behavior vs. deprecated `.all(flatten=True/False)`
    - Deprecation warnings and migration guidance for all manager types
    - Chaining, filtering, ordering, and type consistency of `.children()` and `.all()`
    - Performance and memory usage for large and deeply nested KML datasets
    - Edge cases, empty managers, and managers without folder attributes
    - Correct warning stacklevel and multiple warning issuance
    - Patterns shown in documentation and internal implementation usage

    Ensures users are guided to new API patterns, and that the transition does not introduce
    regressions or break existing usage.
    """

    def test_new_all_behavior_baseline(self) -> None:
        """
        Test new .all() behavior to establish baseline.

        This test documents the new behavior where .all() includes
        all elements including those in nested folders.
        """
        # New .all() should return all elements including nested ones
        complex_kml: KMLFile = KMLFile.from_string(COMPLEX_KML_DATA)
        all_placemarks = complex_kml.placemarks.all()
        all_folders = complex_kml.folders.all()

        # Verify new expectations (should include nested elements)
        assert len(all_placemarks) == 6, "Should have 6 total placemarks"
        assert len(all_folders) == 3, "Should have 3 total folders"

        # Verify all placemark names are included
        placemark_names = {p.name for p in all_placemarks if p.name is not None}
        expected_all_names = {
            "Root Placemark 1",
            "Root Placemark 2",
            "L1A Placemark 1",
            "L1A Placemark 2",
            "L2AA Placemark 1",
            "L1B Placemark 1",
        }
        assert placemark_names == expected_all_names

    def test_deprecated_flatten_true_behavior_baseline(self) -> None:
        """
        Test deprecated .all(flatten=True) behavior to ensure compatibility.

        This test verifies that the deprecated flatten=True parameter
        still works but shows a deprecation warning.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # Test that flatten=True still works but shows warning
        with pytest.warns(DeprecationWarning, match="flatten=True parameter is deprecated"):
            all_placemarks = complex_kml.placemarks.all(flatten=True)

        with pytest.warns(DeprecationWarning, match="flatten=True parameter is deprecated"):
            all_folders = complex_kml.folders.all(flatten=True)

        # Verify behavior still works (should match new .all() behavior)
        assert len(all_placemarks) == 6, "Should have 6 total placemarks"
        assert len(all_folders) == 3, "Should have 3 total folders"

        # Verify all placemark names are included
        placemark_names = {p.name for p in all_placemarks}
        expected_names = {
            "Root Placemark 1",
            "Root Placemark 2",
            "L1A Placemark 1",
            "L1A Placemark 2",
            "L2AA Placemark 1",
            "L1B Placemark 1",
        }
        assert placemark_names == expected_names

    def test_deprecated_flatten_false_behavior_baseline(self) -> None:
        """
        Test that .children() matches deprecated .all(flatten=False) behavior.

        This ensures backward compatibility during the transition period.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # Test .children() behavior
        children_placemarks = complex_kml.placemarks.children()
        children_folders = complex_kml.folders.children()

        # Test deprecated flatten=False behavior with warning
        with pytest.warns(DeprecationWarning, match="flatten=False parameter is deprecated"):
            flatten_false_placemarks = complex_kml.placemarks.all(flatten=False)

        with pytest.warns(DeprecationWarning, match="flatten=False parameter is deprecated"):
            flatten_false_folders = complex_kml.folders.all(flatten=False)

        # Should return identical results
        assert len(children_placemarks) == len(flatten_false_placemarks)
        assert len(children_folders) == len(flatten_false_folders)

        # Should contain same elements by name
        children_placemark_names = {p.name for p in children_placemarks}
        flatten_false_placemark_names = {p.name for p in flatten_false_placemarks}
        assert children_placemark_names == flatten_false_placemark_names

        children_folder_names = {f.name for f in children_folders}
        flatten_false_folder_names = {f.name for f in flatten_false_folders}
        assert children_folder_names == flatten_false_folder_names

    def test_new_all_matches_old_flatten_true(self) -> None:
        """
        Test that new .all() behavior matches old .all(flatten=True) behavior.

        This ensures the new default behavior provides the same comprehensive
        access that users previously needed flatten=True for.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # Test new .all() default behavior
        new_all_placemarks = complex_kml.placemarks.all()
        new_all_folders = complex_kml.folders.all()

        # Test old flatten=True behavior (with deprecation warning)
        with pytest.warns(DeprecationWarning, match="flatten=True parameter is deprecated"):
            old_flatten_placemarks = complex_kml.placemarks.all(flatten=True)

        with pytest.warns(DeprecationWarning, match="flatten=True parameter is deprecated"):
            old_flatten_folders = complex_kml.folders.all(flatten=True)

        # Results should be identical
        assert len(new_all_placemarks) == len(old_flatten_placemarks)
        assert len(new_all_folders) == len(old_flatten_folders)

        # Should contain same elements
        new_all_names = {p.name for p in new_all_placemarks}
        old_flatten_names = {p.name for p in old_flatten_placemarks}
        assert new_all_names == old_flatten_names

    def test_no_warnings_for_default_behavior(self) -> None:
        """Test that default .all() call produces no warnings."""
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors
            result = complex_kml.placemarks.all()  # Should not raise
            assert len(result) > 0

    def test_children_chaining_compatibility(self) -> None:
        """
        Test that .children() works with QuerySet chaining operations.

        This ensures .children() and .all() both support chaining but return
        appropriately different results based on their scope.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # Test .children() chaining (should work on direct children only)
        filtered_children = complex_kml.placemarks.children().filter(name__icontains="Root")
        assert len(filtered_children) == 2  # Only root placemarks match

        children_names = {p.name for p in filtered_children}
        expected_children_names = {"Root Placemark 1", "Root Placemark 2"}
        assert children_names == expected_children_names

        # Test .all() chaining (should work on all placemarks including nested)
        filtered_all = complex_kml.placemarks.all().filter(name__icontains="Root")
        assert len(filtered_all) == 2  # Same filter, but from larger set

        all_names = {p.name for p in filtered_all}
        expected_all_names = {"Root Placemark 1", "Root Placemark 2"}
        assert all_names == expected_all_names

        # Test ordering works for both
        ordered_children = complex_kml.placemarks.children().order_by("name")
        ordered_all = complex_kml.placemarks.all().order_by("name")

        # Children should be 2 elements, all should be 6 elements
        assert len(ordered_children) == 2
        assert len(ordered_all) == 6

        # Both should be properly ordered
        children_ordered_names = [p.name or "" for p in ordered_children]
        all_ordered_names = [p.name or "" for p in ordered_all]

        # Verify ordering works
        assert children_ordered_names is not None
        assert children_ordered_names == sorted(children_ordered_names)
        assert all_ordered_names == sorted(all_ordered_names)

    def test_nested_folder_children_behavior(self) -> None:
        """
        Test .children() behavior on nested folder managers.

        This verifies that .children() works correctly at any folder level.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # Get a nested folder
        level1_folder = complex_kml.folders.children().filter(name="Level 1 Folder A").first()
        assert level1_folder is not None

        # Test .children() on nested folder
        folder_children = level1_folder.placemarks.children()
        assert len(folder_children) == 2

        children_names = {p.name for p in folder_children}
        expected_names = {"L1A Placemark 1", "L1A Placemark 2"}
        assert children_names == expected_names

        # Test nested folders
        nested_folders = level1_folder.folders.children()
        assert len(nested_folders) == 1
        assert nested_folders[0].name == "Level 2 Folder AA"

    def test_internal_implementation_usage_patterns(self) -> None:
        """
        Test patterns that internal implementation code uses.

        This simulates how internal code uses .all() and ensures
        .children() provides the same functionality.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # Pattern: Collecting all direct children of different types
        # (This is what folder.get_all_elements() does)
        all_elements: "List[Union[Folder, Placemark]]" = []
        all_elements.extend(complex_kml.placemarks.children())
        all_elements.extend(complex_kml.folders.children())

        # Should get exactly the root-level elements
        assert len(all_elements) == 4  # 2 placemarks + 2 folders

        # Pattern: Iterating through direct children
        # (This is what managers do for recursive operations)
        folder_count = 0
        for folder in complex_kml.folders.children():
            folder_count += 1
            # Each folder has its own children
            assert folder.placemarks.children().count() > 0

        assert folder_count == 2

    def test_type_consistency(self) -> None:
        """
        Test that .children() returns the same types as .all().

        This ensures type compatibility during the transition.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # pylint: disable=import-outside-toplevel
        from kmlorm.core.querysets import KMLQuerySet

        # Both should return KMLQuerySet
        children_result = complex_kml.placemarks.children()
        all_result = complex_kml.placemarks.all()

        assert isinstance(children_result, KMLQuerySet)
        assert isinstance(all_result, KMLQuerySet)

        # Both should contain the same element types
        for placemark in children_result:
            assert type(placemark).__name__ == "Placemark"

        for placemark in all_result:
            assert type(placemark).__name__ == "Placemark"

    def test_performance_compatibility(self) -> None:
        """
        Test that .children() has similar performance characteristics to .all().

        This ensures the transition doesn't introduce performance regressions.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # Time .all() operation
        start_time = time.time()
        for _ in range(100):
            result_all = complex_kml.placemarks.all()
            _ = len(result_all)
        all_time = time.time() - start_time

        # Time .children() operation
        start_time = time.time()
        for _ in range(100):
            result_children = complex_kml.placemarks.children()
            _ = len(result_children)
        children_time = time.time() - start_time

        # .children() should not be significantly slower
        # Allow up to 50% slower (very generous tolerance)
        assert (
            children_time < all_time * 1.5
        ), f"children() took {children_time:.4f}s vs all() {all_time:.4f}s"

    def test_edge_cases_compatibility(self) -> None:
        """
        Test edge cases to ensure .children() handles them like .all().
        """
        # Both should return empty results
        empty_kml: "KMLFile" = KMLFile.from_string(EMPTY_KML_DATA)
        empty_children = empty_kml.placemarks.children()
        empty_all = empty_kml.placemarks.all()

        assert len(empty_children) == 0
        assert len(empty_all) == 0
        assert len(empty_children) == len(empty_all)

    def test_documentation_example_patterns(self) -> None:
        """
        Test common patterns shown in documentation.

        This ensures examples in docs will work during transition.
        """
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        # pylint: disable=import-outside-toplevel
        from kmlorm.core.querysets import KMLQuerySet as _KMLQuerySet

        # Pattern: Get all of a type at root level
        root_items = complex_kml.placemarks.children()
        assert isinstance(root_items, _KMLQuerySet)  # QuerySet-like

        # Pattern: Filter root items
        root_named_items = complex_kml.placemarks.children().filter(name__icontains="Root")
        assert len(root_named_items) == 2

        # Pattern: Count root items
        root_count = complex_kml.placemarks.children().count()
        assert root_count == 2

        # Pattern: Check if root items exist
        has_root_items = complex_kml.placemarks.children().exists()
        assert has_root_items

    # NEW TESTS FOR COMPREHENSIVE DEPRECATION WARNING COVERAGE

    def test_all_manager_types_deprecation_warnings(self) -> None:
        """Test deprecation warnings work for all manager types."""
        complex_kml: "KMLFile" = KMLFile.from_string(COMPLEX_KML_DATA)
        manager_names = ["placemarks", "folders", "paths", "polygons", "points", "multigeometries"]

        for manager_name in manager_names:
            manager = getattr(complex_kml, manager_name)

            # Test flatten=True warning
            with pytest.warns(DeprecationWarning, match="flatten=True parameter is deprecated"):
                manager.all(flatten=True)

            # Test flatten=False warning
            with pytest.warns(DeprecationWarning, match="flatten=False parameter is deprecated"):
                manager.all(flatten=False)

    def test_warning_messages_provide_migration_guidance(self) -> None:
        """Test that deprecation warning messages guide users to new API patterns."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        # Test flatten=True warning message
        with pytest.warns(DeprecationWarning) as warning_info:
            kml.placemarks.all(flatten=True)

        warning_message = str(warning_info[0].message)
        assert "flatten=True parameter is deprecated" in warning_message
        assert "Use .all() instead" in warning_message
        assert "new default behavior includes nested elements" in warning_message

        # Test flatten=False warning message
        with pytest.warns(DeprecationWarning) as warning_info:
            kml.placemarks.all(flatten=False)

        warning_message = str(warning_info[0].message)
        assert "flatten=False parameter is deprecated" in warning_message
        assert "Use .children() instead" in warning_message
        assert "direct children only" in warning_message

    def test_multiple_warnings_in_single_session(self) -> None:
        """Test that multiple deprecation warnings are properly issued."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Multiple calls should each produce warnings
            kml.placemarks.all(flatten=True)
            kml.folders.all(flatten=True)
            kml.placemarks.all(flatten=False)
            kml.folders.all(flatten=False)

            # Should have 4 warnings
            assert len(w) == 4
            assert all(issubclass(warning.category, DeprecationWarning) for warning in w)

    def test_warning_stacklevel_points_to_user_code(self) -> None:
        """Test that warnings point to the correct location in user code."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            kml.placemarks.all(flatten=True)  # This line should be in the warning

            assert len(w) == 1
            # Warning should point to this test file, not internal implementation
            assert "test_api_transition_compatibility.py" in w[0].filename
            # Line number should be around this call
            assert w[0].lineno > 470  # Should be around line where we call .all(flatten=True)

    def create_large_test_kml(self, num_elements: int) -> KMLFile:
        """Create a KML file with many elements for performance testing."""
        kml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<kml xmlns="http://www.opengis.net/kml/2.2">',
            "<Document>",
            "<name>Large Test Document</name>",
        ]

        # Add root-level placemarks
        for i in range(num_elements // 2):
            kml_parts.extend(
                [
                    "<Placemark>",
                    f"<name>Root Placemark {i}</name>",
                    "<Point>",
                    f"<coordinates>-122.{i:06d},37.{i:06d},0</coordinates>",
                    "</Point>",
                    "</Placemark>",
                ]
            )

        # Add nested structure
        kml_parts.extend(["<Folder>", "<name>Nested Folder</name>"])

        for i in range(num_elements // 2):
            kml_parts.extend(
                [
                    "<Placemark>",
                    f"<name>Nested Placemark {i}</name>",
                    "<Point>",
                    f"<coordinates>-121.{i:06d},38.{i:06d},0</coordinates>",
                    "</Point>",
                    "</Placemark>",
                ]
            )

        kml_parts.extend(["</Folder>", "</Document>", "</kml>"])

        return KMLFile.from_string("\n".join(kml_parts))

    def test_performance_benchmarks(self) -> None:
        """Test performance requirements are met."""
        # Create large test KML with 1000+ elements
        large_kml = self.create_large_test_kml(1000)

        # Benchmark old behavior (with warning suppression)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            start = time.perf_counter()
            for _ in range(100):
                result = large_kml.placemarks.all(flatten=True)
                _ = len(result)
            old_time = time.perf_counter() - start

        # Benchmark new behavior
        start = time.perf_counter()
        for _ in range(100):
            result = large_kml.placemarks.all()
            _ = len(result)
        new_time = time.perf_counter() - start

        # Performance requirement: <10% degradation
        assert new_time < old_time * 1.1, f"Performance degraded: {new_time/old_time:.2f}x"

    def test_memory_usage_reasonable(self) -> None:
        """Test that memory usage is reasonable for large datasets."""
        # pylint: disable=import-outside-toplevel
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available - skipping memory usage test")

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create and process large KML
        large_kml = self.create_large_test_kml(1000)
        result = large_kml.placemarks.all()
        _ = len(result)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB for 1000 elements)
        assert (
            memory_increase < 50 * 1024 * 1024
        ), f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB"

    def test_empty_managers_no_warnings(self) -> None:
        """Test that empty managers work correctly without warnings."""
        kml = KMLFile.from_string(EMPTY_KML_DATA)

        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            # These should not raise (no warnings for default behavior)
            empty_placemarks = kml.placemarks.all()
            empty_folders = kml.folders.all()

            assert len(empty_placemarks) == 0
            assert len(empty_folders) == 0

    def test_managers_without_folders_manager(self) -> None:
        """Test managers that don't have _folders_manager attribute."""
        kml = KMLFile.from_string(COMPLEX_KML_DATA)

        # Get a placemark and check if its point manager works
        placemark = kml.placemarks.children().first()
        if placemark and placemark.point:
            # Point managers typically don't have _folders_manager
            point_manager = getattr(placemark.point, "coordinates", None)
            if hasattr(point_manager, "all"):
                # Should work without warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    assert point_manager is not None
                    point_manager.all()

    def test_deep_nesting_performance(self) -> None:
        """Test performance with deeply nested folder structures."""
        # Create KML with 5 levels of nesting
        kml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <name>Deep Nesting Test</name>
                <Folder>
                    <name>Level 1</name>
                    <Folder>
                        <name>Level 2</name>
                        <Folder>
                            <name>Level 3</name>
                            <Folder>
                                <name>Level 4</name>
                                <Folder>
                                    <name>Level 5</name>
                                    <Placemark>
                                        <name>Deep Placemark</name>
                                        <Point>
                                            <coordinates>-122.0,37.0,0</coordinates>
                                        </Point>
                                    </Placemark>
                                </Folder>
                            </Folder>
                        </Folder>
                    </Folder>
                </Folder>
            </Document>
        </kml>"""

        deep_kml = KMLFile.from_string(kml_content)

        # Should be able to find the deeply nested placemark
        all_placemarks = deep_kml.placemarks.all()
        assert len(all_placemarks) == 1
        assert all_placemarks[0].name == "Deep Placemark"

        # Performance should still be reasonable
        start = time.perf_counter()
        for _ in range(100):
            result = deep_kml.placemarks.all()
            _ = len(result)
        elapsed = time.perf_counter() - start

        # Should complete 100 iterations in reasonable time (less than 1 second)
        assert elapsed < 1.0, f"Deep nesting took too long: {elapsed:.2f}s"

    if __name__ == "__main__":
        pytest.main([__file__])
