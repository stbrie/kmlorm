"""
Test that proves the Field Lookups examples in tutorial.rst work exactly as shown.

This test loads the same KML data structure that the tutorial examples reference
and runs the exact code shown in the tutorial documentation to ensure users
can copy-paste examples and they will work.
"""

import os
from ..parsers.kml_file import KMLFile


class TestTutorialFieldLookupsExact:
    """Test that tutorial field lookups examples work exactly as documented."""

    fixtures_dir: str
    tutorial_kml_file: str

    def setup_method(self) -> None:
        """Set up test data for each test."""
        # Path to the actual KML file used in tutorial examples
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        self.tutorial_kml_file = os.path.join(self.fixtures_dir, "tutorial_stores.kml")

    def test_tutorial_field_lookups_exact_copy(self) -> None:
        """Test that tutorial field lookups examples work exactly as documented."""
        # From tutorial.rst: Field Lookups section - EXACT COPY
        # Load the KML data (matches the tutorial's kml = KMLFile.from_file('stores.kml'))
        kml = KMLFile.from_file(self.tutorial_kml_file)

        # ===== EXACT COPY OF CODE FROM TUTORIAL.RST =====

        # Exact match (default) - use flatten=True to include folder contents
        exact = kml.placemarks.all(flatten=True).filter(name="Capital Electric Supply")

        # Case-insensitive contains
        contains = kml.placemarks.all(flatten=True).filter(name__icontains="electric")

        # Starts with / ends with
        starts = kml.placemarks.all(flatten=True).filter(name__startswith="Capital")
        ends = kml.placemarks.all(flatten=True).filter(name__endswith="Store")

        # In a list of values
        multiple = kml.placemarks.all(flatten=True).filter(
            name__in=["Hardware Store", "Electric Depot"]
        )

        # Null checks
        with_description = kml.placemarks.all(flatten=True).filter(description__isnull=False)
        without_description = kml.placemarks.all(flatten=True).filter(description__isnull=True)

        # Regular expressions
        regex_match = kml.placemarks.all(flatten=True).filter(name__regex=r"^Capital.*Electric.*$")

        # ===== VERIFY THE EXACT RESULTS USERS SHOULD EXPECT =====

        # Verify the exact results that users should expect
        assert len(exact) == 1, f"Expected 1 exact match, got {len(exact)}"

        # Capital Electric Supply and Electric Depot
        assert len(contains) == 2, f"Expected 2 contains matches, got {len(contains)}"

        # Capital Electric Supply
        assert len(starts) == 1, f"Expected 1 starts match, got {len(starts)}"

        # Hardware Store and Independent Store
        assert len(ends) == 2, f"Expected 2 ends matches, got {len(ends)}"

        # Hardware Store and Electric Depot
        assert len(multiple) == 2, f"Expected 2 multiple matches, got {len(multiple)}"
        assert (
            len(with_description) >= 1
        ), f"Expected >=1 with_description matches, got {len(with_description)}"
        assert (
            len(without_description) >= 1
        ), f"Expected >=1 without_description matches, got {len(without_description)}"

        # Capital Electric Supply
        assert len(regex_match) == 1, f"Expected 1 regex match, got {len(regex_match)}"

        # Verify specific content
        assert exact[0].name == "Capital Electric Supply"
        assert "Capital Electric Supply" in [p.name for p in contains]
        assert "Electric Depot" in [p.name for p in contains]
        assert starts[0].name == "Capital Electric Supply"
        assert "Hardware Store" in [p.name for p in ends]
        assert "Independent Store" in [p.name for p in ends]

    def test_tutorial_examples_work_with_real_file(self) -> None:
        """Test that examples work exactly as shown in tutorial using real KML file."""
        # Verify the fixture file exists
        assert os.path.exists(
            self.tutorial_kml_file
        ), f"Tutorial KML fixture not found: {self.tutorial_kml_file}"

        # Use the exact pattern shown in tutorial: kml = KMLFile.from_file('stores.kml')
        # (but using our test fixture path)
        kml = KMLFile.from_file(self.tutorial_kml_file)

        # Run one of the tutorial examples to prove it works with real file loading
        exact = kml.placemarks.all(flatten=True).filter(name="Capital Electric Supply")
        assert len(exact) == 1
        assert exact[0].name == "Capital Electric Supply"

        # Test additional examples to prove the file contains the right data
        contains = kml.placemarks.all(flatten=True).filter(name__icontains="electric")
        assert len(contains) == 2  # Capital Electric Supply and Electric Depot
