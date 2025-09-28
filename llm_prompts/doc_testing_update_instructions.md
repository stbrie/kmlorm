# Documentation Testing Update Instructions

## Overview
Ensure every Python code example in .rst documentation files has a corresponding pytest test that validates the documented behavior exactly as shown.

## Project-Specific Conventions

### Test File Organization
- **Naming Convention**: `tests/test_[docname]_docs.py` (note: plural `_docs` not singular `_doc`)
  - Example: `examples.rst` → `test_examples_docs.py`
  - Example: `api/spatial.rst` → `test_spatial_docs.py`

**Note**: Some existing test_*_docs.py files may still use `unittest.TestCase` (legacy pattern).
When updating or creating new documentation tests, use pure pytest patterns as shown below.

### Test Structure Requirements
```python
"""
Tests that validate every example in docs/source/[path]/[docname].rst works as documented.

This test suite ensures that all code examples in the [DocName] documentation
are functional and produce the expected results.
"""

import pytest
from typing import Generator
# Additional imports as needed

class Test[DocName]DocsExamples:
    """Test cases that validate [docname].rst documentation examples."""

    @pytest.fixture
    def sample_kml(self) -> str:
        """Provide sample KML content for tests."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <!-- KML content matching documentation examples -->
        </kml>"""

    @pytest.fixture
    def kml_file(self, sample_kml: str) -> 'KMLFile':
        """Create KMLFile instance for tests."""
        from kmlorm import KMLFile
        return KMLFile.from_string(sample_kml)
```

### Testing Standards (from CLAUDE.md)
- **No disposable tests**: All tests must provide long-term debugging value
- **Comprehensive coverage**: Test edge cases and error conditions
- **Type safety**: Include type hints for test methods
- **Coordinate ordering**: Always verify longitude, latitude order (KML standard)
- **XML safety**: Validate against malformed KML and XXE attacks
- **Memory efficiency**: Test with realistic file sizes (hundreds of placemarks)

### Code Example Extraction Guidelines

1. **Identify testable code blocks**:
   - Look for `.. code-block:: python` sections
   - Include setup code from preceding paragraphs if needed
   - Consider context from section headers

2. **Handle imports properly**:
   ```python
   # Documentation often shows:
   from kmlorm import KMLFile

   # Test should include all necessary imports:
   from kmlorm import KMLFile
   from kmlorm.spatial import DistanceUnit, SpatialCalculations
   from kmlorm.core.exceptions import KMLElementNotFound
   ```

3. **Create realistic test data**:
   - Use comprehensive KML fixtures that match documentation scenarios
   - Include nested folders, multiple element types
   - Test with coordinates in Baltimore area (-76.6, 39.3) for consistency

4. **Validate spatial calculations**:
   - Use known distances for validation (NYC-London: ~5567km)
   - Test with tolerance for floating-point calculations
   - Verify unit conversions (km, miles, meters)

### Test Implementation Patterns

#### Pattern 1: Basic functionality test
```python
def test_basic_usage_from_docs(self, kml_file) -> None:
    """Test basic usage example from documentation."""
    # Execute documented code
    placemarks = kml_file.placemarks.all()

    # Verify documented behavior with pytest assertions
    assert len(placemarks) > 0
    assert placemarks[0].name == "Expected Name"
```

#### Pattern 2: Spatial operations test
```python
def test_spatial_calculations_example(self, kml_file) -> None:
    """Test spatial calculation example from documentation."""
    from kmlorm.spatial import DistanceUnit

    store1 = kml_file.placemarks.get(name="Store A")
    store2 = kml_file.placemarks.get(name="Store B")

    # Test documented spatial operations
    distance_km = store1.distance_to(store2)
    distance_miles = store1.distance_to(store2, unit=DistanceUnit.MILES)

    # Verify with reasonable tolerance using pytest.approx
    assert distance_km == pytest.approx(expected_km, abs=0.1)
    assert distance_miles == pytest.approx(expected_miles, abs=0.1)
```

#### Pattern 3: Error handling test
```python
def test_error_handling_example(self, kml_file) -> None:
    """Test error handling example from documentation."""
    from kmlorm.core.exceptions import KMLElementNotFound

    # Test documented exception with pytest.raises
    with pytest.raises(KMLElementNotFound):
        kml_file.placemarks.get(name="Non-existent Store")
```

#### Pattern 4: Parametrized test for multiple examples
```python
@pytest.mark.parametrize("coord1,coord2,expected_km,tolerance", [
    ((-74.006, 40.7128), (-0.1276, 51.5074), 5567, 10),  # NYC to London
    ((139.6917, 35.6895), (-122.4194, 37.7749), 8280, 10),  # Tokyo to SF
    ((0, 0), (0, 0), 0, 0),  # Same point
])
def test_distance_examples_from_docs(self, coord1, coord2, expected_km, tolerance) -> None:
    """Test distance calculation examples from documentation."""
    from kmlorm.models.point import Coordinate

    c1 = Coordinate(longitude=coord1[0], latitude=coord1[1])
    c2 = Coordinate(longitude=coord2[0], latitude=coord2[1])

    distance = c1.distance_to(c2)
    assert abs(distance - expected_km) <= tolerance
```

### Update Checklist

- [ ] Extract all Python code examples from .rst file
- [ ] Check for existing test in `tests/test_[docname]_docs.py`
- [ ] Verify test class follows naming pattern `Test[DocName]DocsExamples`
- [ ] Ensure setUp() creates appropriate test fixtures
- [ ] Match imports exactly as shown in documentation
- [ ] Test produces same output/behavior as documented
- [ ] Handle all documented exceptions properly
- [ ] Use realistic test data (KML with folders, coordinates, etc.)
- [ ] Verify spatial calculations with known values
- [ ] Add docstrings explaining what documentation section is tested
- [ ] Run full test suite: `python -m pytest kmlorm/tests/test_*_docs.py -v`

### Special Considerations

1. **Quickstart/Tutorial examples**: May require more comprehensive fixtures
2. **API reference examples**: Focus on exact method behavior
3. **Examples.rst**: Test complete functions, not just snippets
4. **Spatial operations**: Use known city coordinates and distances
5. **QuerySet operations**: Test with both `all()` and `children()` patterns

### Documentation Synchronization

When updating tests or documentation:
1. **If API changed**: Update both documentation and test
2. **If example fails**: Determine if API or documentation is correct
3. **If example is incomplete**: Add necessary context in test setUp()
4. **If example uses external data**: Create appropriate fixtures

### Running Documentation Tests

```bash
# Run all documentation tests
python -m pytest kmlorm/tests/test_*_docs.py -v

# Run specific documentation test
python -m pytest kmlorm/tests/test_examples_docs.py -v

# Run with coverage
pytest --cov=kmlorm --cov-report=term-missing kmlorm/tests/test_*_docs.py

# Quick validation (short traceback)
python -m pytest kmlorm/tests/test_*_docs.py --tb=short
```

### Common Issues and Solutions

1. **Import errors**: Ensure all necessary imports are included
2. **Missing fixtures**: Create comprehensive test KML using pytest fixtures
3. **Coordinate order**: KML uses lon,lat but display might show lat,lon
4. **Float comparisons**: Use `pytest.approx()` with appropriate tolerance
5. **Nested elements**: Use `all()` for nested, `children()` for direct only
6. **Test isolation**: Use fixtures instead of class-level state
7. **Parametrized tests**: Use `@pytest.mark.parametrize` for multiple test cases

## Your Task

1. **Identify documentation file**: Note the path (e.g., `docs/source/examples.rst`)
2. **Check for existing test**: Look for `tests/test_examples_docs.py`
3. **Extract code examples**: Find all `.. code-block:: python` sections
4. **Create/update tests**: Ensure each example has a corresponding test
5. **Verify behavior**: Run tests to confirm documentation accuracy
6. **Update as needed**: Fix documentation or implementation to match
7. **Document coverage**: Add comment noting which doc section is tested

Remember: Tests should validate that documentation examples work exactly as shown, providing confidence that users can rely on the documentation.