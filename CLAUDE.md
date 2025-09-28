# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in the kml_orm repository.

## Quick Reference

### Essential Commands
- **Virtual environment**: `source venv/bin/activate` (local venv in project root)
- **Run tests**: `python -m pytest kmlorm/tests/ -v`
- **Type check**: `mypy kmlorm`
- **Lint**: `pylint kmlorm/`
- **Format**: `black kmlorm/`
- **Sort imports**: `isort kmlorm/`
- **Check style**: `flake8 kmlorm/`
- **Coverage**: `pytest --cov=kmlorm --cov-report=term-missing`

### Test Commands
- **All tests**: `python -m pytest kmlorm/tests/ -v`
- **Specific test file**: `python -m pytest kmlorm/tests/test_basic.py -v`
- **Specific test method**: `python -m pytest kmlorm/tests/test_basic.py::TestPlacemark::test_placemark_creation -v`
- **Integration tests**: `python -m pytest kmlorm/tests/test_url_integration.py -v`
- **Documentation tests**: `python -m pytest kmlorm/tests/test_*_docs.py -v`
- **Coverage with short output**: `python -m pytest kmlorm/tests/ -v --tb=short`

### Project Structure
```
kml_orm/
├── kmlorm/                 # Main package
│   ├── core/              # Core functionality and exceptions
│   ├── models/            # KML model classes (Point, Placemark, Folder, etc.)
│   ├── parsers/           # XML/KML parsing utilities
│   ├── spatial/           # Geospatial operations and utilities
│   ├── utils/             # General utilities
│   ├── exports/           # Reserved for future functionality
│   └── tests/             # Test suite
├── docs/                  # Sphinx documentation
├── pyproject.toml         # Project configuration
├── .pylintrc             # Pylint configuration
└── .flake8              # Flake8 configuration
```

## Architecture Overview

### Core Application Structure
KML ORM is a Django-style ORM for KML (Keyhole Markup Language) files that provides:

**Main Models (kmlorm/models/):**
- **KMLFile**: Root container for KML documents
- **Placemark**: Geographic features with coordinates and metadata
- **Folder**: Hierarchical organization of KML elements
- **Point**: Geographic point coordinates with latitude, longitude, altitude
- **Path**: Linear geographic features (LineString)
- **Polygon**: Area-based geographic features
- **MultiGeometry**: Collections of multiple geometric types

**Core Components (kmlorm/core/):**
- **Managers**: Django-style object managers for querying
- **QuerySets**: Chainable query interfaces
- **Exceptions**: Custom exception classes for validation and errors
- **Base classes**: Foundation classes for models and functionality

**Parser Architecture (kmlorm/parsers/):**
- **XML Parser**: lxml-based KML parsing with validation
- **URL Integration**: HTTP/HTTPS KML file loading
- **Error handling**: Comprehensive parsing error management

### Query System Architecture
- **Django-style API**: `.objects.all()`, `.filter()`, `.get()` methods
- **Chainable queries**: Build complex queries step by step
- **Geospatial operations**: `.near()`, `.within_bounds()`, coordinate filtering
- **Field lookups**: `name__icontains`, `address__contains`, `visibility=True`
- **Type safety**: Full type annotations throughout

## Development Workflow

### Code Quality Standards
- Follow PEP 8 with 100-character line length (configured in pyproject.toml)
- Use type hints for all function parameters and returns
- Maintain comprehensive test coverage (current target: 80%+)
- Write self-documenting code with descriptive names
- Keep functions focused and under 20 lines when possible
- Use early returns to reduce nesting complexity

### Python Development Conventions
- Use Python 3.11+ features and type annotations
- Follow dataclass patterns for model definitions
- Implement proper error handling with custom exceptions
- Use lxml for XML parsing with proper namespace handling
- Maintain compatibility with optional dependencies

### Development Commands

#### Environment & Setup
- **Virtual environment**: `source venv/bin/activate` (local project venv)
- **Install dev dependencies**: `pip install -e .[dev]`
- **Install documentation dependencies**: `pip install -e .[docs]`
- **Install all optional dependencies**: `pip install -e .[all]`

#### Testing Commands
- **Full test suite**: `python -m pytest kmlorm/tests/ -v`
- **Fast feedback**: `python -m pytest kmlorm/tests/ --tb=short`
- **Specific test pattern**: `python -m pytest -k "test_placemark" -v`
- **Integration tests**: `python -m pytest kmlorm/tests/test_url_integration.py -v`
- **Documentation tests**: `python -m pytest kmlorm/tests/test_*_docs.py --tb=short`

#### Code Quality Commands
- **Type checking**: `mypy kmlorm` (configured for strict mode)
- **Linting**: `pylint kmlorm/` (Django-aware configuration)
- **Fast linting**: `pylint kmlorm/ --disable=all --enable=E,F`
- **Code formatting**: `black kmlorm/` (line length 100)
- **Import sorting**: `isort kmlorm/`
- **Style checking**: `flake8 kmlorm/`

#### Coverage & Quality Gates
- **Coverage**: `pytest --cov=kmlorm --cov-report=term-missing`
- **Coverage with HTML**: `pytest --cov=kmlorm --cov-report=html`
- **Coverage threshold**: 80% minimum (configured in pyproject.toml)

#### Documentation
- **Install doc dependencies**: `pip install -e .[docs]`
- **Build docs**: `cd docs && make html`
- **Clean docs**: `cd docs && make clean`
- **Check doc links**: `cd docs && make linkcheck`
- **View docs**: Open `docs/build/html/index.html` in browser
- **Documentation tests validate**: All examples in docs are tested in `test_*_docs.py` files

## Testing Standards

### Core Testing Strategy
- Comprehensive test coverage across models, parsers, and queries
- Documentation tests ensure all examples work as shown
- Integration tests for URL loading and complex workflows
- Performance tests for large KML files
- Type checking integration with mypy in CI

### Test Organization
- **test_basic.py**: Core model functionality and basic operations
- **test_*_docs.py**: Tests that validate documentation examples
- **test_querysets_*.py**: Query system and filtering tests
- **test_*_integration.py**: End-to-end and integration tests
- **test_xml_parser.py**: Parser functionality and error handling

### Testing Requirements
- Write tests for all new functionality using pytest
- Include edge cases and error conditions
- Test both success and failure scenarios
- Use fixtures for complex test data setup
- Maintain test independence (no test should depend on another)

### Test Data and Fixtures
- **fixtures/**: Directory containing sample KML files for testing
- **Test data creation**: Use factory methods for generating test objects
- **URL integration**: Tests include HTTP server simulation for remote KML files
- **Error scenarios**: Comprehensive testing of malformed KML and edge cases

### Documentation Testing Strategy
Documentation tests ensure all code examples in the docs actually work:

```python
# Pattern from test_*_docs.py files
def test_quickstart_example(self) -> None:
    """Test that the quickstart example in README works."""
    # Example code from documentation
    kml = KMLFile.from_string(SAMPLE_KML)
    all_places = kml.placemarks.all()
    # Verify results match documentation claims
    self.assertGreater(len(all_places), 0)
```

### Testing Best Practices
- Use descriptive test method names that explain the scenario
- Test one thing per test method
- Use setUp/tearDown appropriately for test isolation
- Mock external dependencies (HTTP requests, file system)
- Include both positive and negative test cases
- Test error messages and exception types

## Common Development Issues & Solutions

### KML Parsing and XML Namespaces
**Problem**: KML files use XML namespaces that can cause parsing issues.

**Solution**: Always use namespace-aware parsing with lxml:
```python
# Correct namespace handling
from lxml import etree
parser = etree.XMLParser(ns_clean=True, recover=True)
root = etree.fromstring(kml_content, parser)
```

### Coordinate System Handling
**Critical**: KML uses longitude, latitude, altitude order (WGS84).

**Coordinate Order**:
- KML format: `longitude,latitude,altitude`
- Common expectation: `latitude,longitude`
- Always validate coordinate order in tests and documentation

### Type Safety with Optional Dependencies
**Pattern**: Handle optional dependencies gracefully:
```python
try:
    import optional_library
    HAS_OPTIONAL = True
except ImportError:
    HAS_OPTIONAL = False

def optional_feature(self):
    if not HAS_OPTIONAL:
        raise ImportError("optional_library is required for this feature")
    # Implementation here
```

### Large File Handling
**Memory Management**: For large KML files:
- Use streaming parsers when possible
- Implement lazy loading for large datasets
- Consider memory usage in query operations
- Test with realistic file sizes

### URL Loading and HTTP Integration
**Best Practices**:
- Always handle network timeouts and errors
- Support both HTTP and HTTPS URLs
- Validate URL formats before attempting requests
- Use appropriate User-Agent headers

## Security & Production

### Security Considerations
- Validate all XML input to prevent XXE attacks
- Sanitize user-provided coordinates and strings
- Handle malformed KML files gracefully
- Don't expose internal paths in error messages

### Performance Considerations
- Use lxml for efficient XML parsing
- Implement query optimization for large datasets
- Consider memory usage with large KML files
- Profile critical paths for performance bottlenecks

## Code Review Standards
When suggesting or reviewing code, ensure it meets these criteria:
- [ ] Is the code easily testable with pytest?
- [ ] Are edge cases and error conditions handled?
- [ ] Is the naming clear and follows project conventions?
- [ ] Are type hints comprehensive and accurate?
- [ ] Does it handle optional dependencies properly?
- [ ] Are coordinate systems handled correctly (lon/lat order)?
- [ ] Is XML/KML parsing secure and robust?
- [ ] Are there corresponding tests for new functionality?
- [ ] Do documentation examples work as shown?

### AI Development Workflow

#### Context Management for Claude Code
- Always include model relationships when discussing changes
- Reference spatial operations and coordinate systems
- Include testing patterns when adding new functionality
- Consider optional dependencies and graceful degradation
- Use specific file patterns: `kmlorm/models/point.py:45`

#### Development Best Practices with Claude
- Reference models by exact path and line numbers
- Provide context about geospatial operations and KML structure
- Use incremental changes rather than large refactors
- Always run tests after modifications
- Consider both basic and integration test coverage

## Important Notes

### File Exclusions
- `kmlorm/_version.py` is auto-generated by setuptools_scm (excluded from linting)
- Virtual environment (`venv/`) should not be committed to git
- Generated documentation (`docs/build/`) is excluded from version control

### Dependencies
- **Required**: `lxml` for XML parsing
- **Optional**: None currently (reserved for future optional features)
- **Development**: `pytest`, `mypy`, `pylint`, `black`, `flake8`, `isort`

### Version Management
- Version is automatically managed by setuptools_scm based on git tags
- No manual version updates needed in code
- Use semantic versioning for git tags (v1.0.0, v1.1.0, etc.)
- do not write disposable or "one-off" tests.  any information that is required during development that a "one-off" would provide will be useful in the future when debugging.  any code that exposes information or workflow for development purposes needs to go in an appropriately named file in the tests/ folder for future reference.