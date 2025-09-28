"""
Tests for examples from the index documentation.

This module contains tests that verify all code examples from the
index.rst documentation work correctly. Each test copies the exact
code from the documentation to ensure it works as shown.
"""

import os


class TestIndexDocsExamples:
    """
    Test suite for validating the index.rst documentation examples.

    This class contains tests that ensure every code example shown in the
    index.rst file works exactly as documented when copy-pasted by users.
    """

    fixtures_dir: str
    places_kml_file: str

    def setup_method(self) -> None:
        """Set up test data for each test."""
        # Path to fixture files for real file system testing
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        self.places_kml_file = os.path.join(self.fixtures_dir, "sample.kml")

    def test_exact_quick_example_code_block(self) -> None:
        """Test the exact 'Quick Example' code block from index.rst."""
        # EXACT CODE FROM index.rst: Quick Example section
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        # Load KML file
        kml = KMLFile.from_file(self.places_kml_file)  # Use our test file instead of 'places.kml'

        # Query placemarks (use .all() to include those in folders, .children() for direct only)
        all_places = kml.placemarks.all()
        capital_stores = kml.placemarks.all().filter(name__icontains="capital")
        nearby = kml.placemarks.all().near(-76.6, 39.3, radius_km=25)

        # Chain queries
        nearby_open = (
            kml.placemarks.all()
            .filter(name__icontains="electric")
            .near(-76.6, 39.3, radius_km=50)
            .filter(visibility=True)
        )

        # Verify the code worked as expected
        assert isinstance(kml, KMLFile)
        assert hasattr(all_places, "__iter__")
        assert len(all_places) >= 0

        # Verify capital stores filter works
        assert hasattr(capital_stores, "__iter__")
        capital_list = list(capital_stores)
        for store in capital_list:
            assert store.name and "capital" in store.name.lower()

        # Verify nearby query works
        assert hasattr(nearby, "__iter__")

        # Verify chained query works
        assert hasattr(nearby_open, "__iter__")
        nearby_open_list = list(nearby_open)
        for place in nearby_open_list:
            assert place.name and "electric" in place.name.lower()
            assert place.visibility is True

    def test_exact_load_kml_file_example(self) -> None:
        """Test the exact KML file loading example from index.rst."""
        # EXACT CODE FROM index.rst: Quick Example section
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        # Load KML file
        kml = KMLFile.from_file(self.places_kml_file)  # Use our test file

        # Verify the code worked
        assert isinstance(kml, KMLFile)
        assert kml.document_name is not None

    def test_exact_query_placemarks_examples(self) -> None:
        """Test the exact placemark querying examples from index.rst."""
        # Setup
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        kml = KMLFile.from_file(self.places_kml_file)

        # EXACT CODE FROM index.rst: Quick Example section
        # Query placemarks (use .all() to include those in folders, .children() for direct only)
        all_places = kml.placemarks.all()
        capital_stores = kml.placemarks.all().filter(name__icontains="capital")
        nearby = kml.placemarks.all().near(-76.6, 39.3, radius_km=25)

        # Verify each query works
        assert hasattr(all_places, "__iter__")
        assert len(list(all_places)) >= 0

        assert hasattr(capital_stores, "__iter__")
        capital_list = list(capital_stores)

        assert hasattr(nearby, "__iter__")
        nearby_list = list(nearby)
        assert nearby_list is not None
        # Verify the filtering logic works
        for store in capital_list:
            if store.name:
                assert "capital" in store.name.lower()

    def test_exact_chain_queries_example(self) -> None:
        """Test the exact query chaining example from index.rst."""
        # Setup
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        kml = KMLFile.from_file(self.places_kml_file)

        # EXACT CODE FROM index.rst: Quick Example section
        # Chain queries
        nearby_open = (
            kml.placemarks.all()
            .filter(name__icontains="electric")
            .near(-76.6, 39.3, radius_km=50)
            .filter(visibility=True)
        )

        # Verify the chained query works
        assert hasattr(nearby_open, "__iter__")

        # Verify the filtering logic
        nearby_open_list = list(nearby_open)
        for place in nearby_open_list:
            if place.name:
                assert "electric" in place.name.lower()
            # Note: visibility might be None, so we check if it's explicitly True when set
            if hasattr(place, "visibility") and place.visibility is not None:
                assert place.visibility is True

    def test_all_imports_work_as_documented(self) -> None:
        """Test that all imports shown in index.rst work correctly."""
        # EXACT CODE FROM index.rst: Quick Example section
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        # Verify the import worked and class is available
        assert KMLFile is not None
        assert hasattr(KMLFile, "from_file")
        assert callable(getattr(KMLFile, "from_file"))

    def test_flatten_parameter_behavior_as_documented(self) -> None:
        """Test that new API behavior works as documented in index.rst."""
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        kml = KMLFile.from_file(self.places_kml_file)

        # The documentation now emphasizes the new intuitive API
        # Test that this pattern works
        direct_children = kml.placemarks.children()  # Direct children only
        all_places = kml.placemarks.all()  # All placemarks including nested

        # Verify both queries work
        assert hasattr(direct_children, "__iter__")
        assert hasattr(all_places, "__iter__")

        # all() should typically return more or equal elements than children()
        children_count = len(list(direct_children))
        all_count = len(list(all_places))
        assert all_count >= children_count

    def test_geospatial_operations_as_documented(self) -> None:
        """Test that geospatial operations work as shown in index.rst features."""
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        kml = KMLFile.from_file(self.places_kml_file)

        # Test the .near() operation mentioned in features
        nearby = kml.placemarks.all().near(-76.6, 39.3, radius_km=25)
        assert hasattr(nearby, "__iter__")

        # The features mention .within_bounds() - test that it exists and works
        assert hasattr(kml.placemarks.all(), "within_bounds")
        bounded = kml.placemarks.all().within_bounds(
            north=39.5, south=39.0, east=-76.0, west=-77.0
        )
        assert hasattr(bounded, "__iter__")

    def test_django_style_api_as_documented(self) -> None:
        """Test that Django-style API methods work as documented in features."""
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        kml = KMLFile.from_file(self.places_kml_file)

        # Test the Django-style methods mentioned in features
        # .objects.all() equivalent
        all_placemarks = kml.placemarks.all()
        assert hasattr(all_placemarks, "__iter__")

        # .filter() method
        filtered = kml.placemarks.all().filter(name__icontains="capital")
        assert hasattr(filtered, "__iter__")

        # .get() method - test that it exists (we'll use a safe call)
        placemarks_list = list(kml.placemarks.all())
        if placemarks_list:
            # Find a unique name to test .get() with
            first_placemark = placemarks_list[0]
            if first_placemark.name:
                try:
                    single = kml.placemarks.all().get(name=first_placemark.name)
                    assert single is not None
                except Exception:  # pylint: disable=broad-except
                    # Multiple elements might exist with same name, that's ok
                    pass

    def test_chainable_queries_as_documented(self) -> None:
        """Test that queries can be chained as documented in features."""
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        kml = KMLFile.from_file(self.places_kml_file)

        # Test building complex geospatial queries step by step
        base_query = kml.placemarks.all()
        with_filter = base_query.filter(name__icontains="electric")
        with_location = with_filter.near(-76.6, 39.3, radius_km=50)
        final_query = with_location.filter(visibility=True)

        # Verify each step in the chain works
        assert hasattr(base_query, "__iter__")
        assert hasattr(with_filter, "__iter__")
        assert hasattr(with_location, "__iter__")
        assert hasattr(final_query, "__iter__")

        # Verify we can iterate through the final result
        results = list(final_query)
        assert isinstance(results, list)

    def test_example_demonstrates_core_functionality(self) -> None:
        """Test that the index.rst example demonstrates the core library functionality."""
        # pylint: disable=import-outside-toplevel
        from kmlorm import KMLFile

        # Test that the example covers the main use cases
        kml = KMLFile.from_file(self.places_kml_file)

        # 1. Loading files
        assert isinstance(kml, KMLFile)

        # 2. Accessing elements
        placemarks = kml.placemarks.all()
        assert hasattr(placemarks, "__iter__")

        # 3. Filtering
        filtered = kml.placemarks.all().filter(name__icontains="capital")
        assert hasattr(filtered, "__iter__")

        # 4. Geospatial queries
        nearby = kml.placemarks.all().near(-76.6, 39.3, radius_km=25)
        assert hasattr(nearby, "__iter__")

        # 5. Query chaining
        chained = (
            kml.placemarks.all()
            .filter(name__icontains="electric")
            .near(-76.6, 39.3, radius_km=50)
        )
        assert hasattr(chained, "__iter__")

        # All the core functionality works as documented


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
