# KML ORM

A Django-style ORM for KML (Keyhole Markup Language) files that provides intuitive, chainable query interfaces for geospatial data without requiring Django as a dependency.

## Features

- **Django-style API**: Familiar `.objects.all()`, `.filter()`, `.get()` methods
- **Chainable queries**: Build complex geospatial queries step by step
- **Type hints**: Full type annotation support for modern Python development
- **No Django dependency**: Use the Django(-ish) patterns you know and love (now with less Django!)
- **Geospatial operations**: Built-in spatial queries like `.near()`, `.within_bounds()`
- **Python data structures**: Access KML data as native Python objects

## Quick Start

```python
from kmlorm import KMLFile

# Load KML file
kml = KMLFile.from_file('places.kml')

# Query placemarks
all_places = kml.placemarks.all()
capital_stores = kml.placemarks.filter(name__icontains='capital')
nearby = kml.placemarks.near(-76.6, 39.3, radius_km=25)

# Chain queries
nearby_open = (kml.placemarks
    .filter(name__icontains='electric')
    .near(-76.6, 39.3, radius_km=50)
    .filter(visibility=True)
)

# Get specific placemark
rosedale = kml.placemarks.get(address__contains='Rosedale')
```

### Hierarchical Querying

Work with nested folder structures using intuitive methods:

```python
# Get only direct children (placemarks at root level)
root_placemarks = kml.placemarks.children()

# Get ALL placemarks including nested ones
all_placemarks = kml.placemarks.all()

# Same pattern works for folders
root_folders = kml.folders.children()
all_folders = kml.folders.all()

# Chain with other methods
visible_root_places = kml.placemarks.children().filter(visibility=True)
```

## Installation

```bash
pip install kmlorm
```

## Requirements

- Python 3.11+
- lxml

Note: This repository includes a built-in XML parser at `kmlorm/parsers/xml_parser.py` that will use `lxml`.  The kmlorm package will not work without it.

## Version Compatibility

KML ORM follows a pragmatic approach to dependency versioning:

- **Latest stable versions**: Dependencies are unpinned to use the latest stable versions available at install time
- **Ubuntu LTS focus**: Testing is primarily done against Ubuntu LTS package versions and latest PyPI releases
- **Python 3.11+ only**: We focus on recent Python versions rather than maintaining compatibility with older versions
- **Fix-forward strategy**: If version conflicts arise, we'll fix them as they're reported rather than pre-emptively constraining versions

### Why this approach?

- **Simplified maintenance**: Testing all possible version combinations is impractical for a specialized library
- **Latest features**: Users automatically get security updates and latest functionality
- **Realistic usage**: Most users install latest versions anyway
- **Technical user base**: GIS developers can typically handle version management

### If you encounter issues:

1. Try upgrading all dependencies: `pip install --upgrade kmlorm`
2. Check if the issue exists with the latest versions
3. [File an issue](https://github.com/stbrie/kmlorm/issues) with your environment details

This approach keeps the library maintainable while providing a good experience for most users.

## Development

This project was developed with assistance from Claude AI and ChatGPT GPT-4.1 assistants.

## Documentation

### Building Documentation

The project uses Sphinx for documentation. To build the documentation locally:

```bash
# Install documentation dependencies (if not already installed)
pip install sphinx sphinx-rtd-theme

# Navigate to docs directory and build HTML documentation
cd docs

# Unix/Linux/macOS (requires make)
make html

# Windows (using batch file)
make.bat html

# Alternative: Direct sphinx-build command (all platforms)
sphinx-build -M html source build

# Open the built documentation
open build/html/index.html  # macOS
# or
xdg-open build/html/index.html  # Linux
# or navigate to docs/build/html/index.html in your browser
```

### Available Documentation Formats

```bash
cd docs

# HTML documentation (recommended)
make html                    # Unix/Linux/macOS
make.bat html               # Windows

# PDF documentation (requires LaTeX)
make latexpdf               # Unix/Linux/macOS
make.bat latexpdf          # Windows

# Clean and rebuild
make clean && make html     # Unix/Linux/macOS
make.bat clean & make.bat html  # Windows

# Check external links
make linkcheck              # Unix/Linux/macOS
make.bat linkcheck         # Windows

# See all available targets
make help                   # Unix/Linux/macOS
make.bat help              # Windows

# Direct sphinx-build alternatives (all platforms)
sphinx-build -M html source build
sphinx-build -M latexpdf source build
sphinx-build -M clean source build
```

The built HTML documentation will be available in `docs/build/html/index.html`.

### Documentation Structure

- **Quick Start Guide**: `docs/source/quickstart.rst`
- **Full Tutorial**: `docs/source/tutorial.rst`
- **API Reference**: `docs/source/api/`
- **Examples**: `docs/source/examples.rst`

## Namespaces & Google Earth gx extensions

The project parses KML 2.2 data and commonly-seen Google Earth attributes. Use these namespace URIs when querying or generating KML:

- kml (default): `http://www.opengis.net/kml/2.2`
- gx: `http://www.google.com/kml/ext/2.2`
- atom: `http://www.w3.org/2005/Atom`

Note: neither the `gx` extensions (the `gx` namespace) nor Atom metadata are currently supported by kmlorm in particular, though lxml can parse them.  You could write an extension and submit it as a PR.

Note: The `gx` namespace URI is a stable identifier used by Google but is not necessarily a browsable documentation page. For human-readable documentation about the `gx` extension elements see:

https://developers.google.com/kml/documentation/kmlreference#kmlextensions

## Tests & Fixtures

- Tests live under: `kmlorm/tests`
- Fixtures live under: `kmlorm/tests/fixtures` (e.g. `google_earth_kml.kml`, `comprehensive.kml`)

Run tests locally with:

```bash
pytest -q
```

 ## Limitations / Current Implementation Status

  This project implements a comprehensive KML parsing and ORM system with most core features fully functional:

  **Fully Implemented:**
  - All KML models (Placemark, Folder, Point, Path, Polygon, MultiGeometry)
  - Complete Django-style QuerySet/Manager API with filtering and geospatial operations
  - HTTP/HTTPS URL loading for remote KML files
  - Hierarchical folder navigation with `flatten=True` support
  - Type-safe `to_dict()` methods for external library integration
  - Comprehensive test suite (22 test files) with documentation validation

  **Planned/Limited:**
  - Google Earth Extensions (`gx:Track`, `gx:Tour`) - partial support
  - Advanced spatial indexing and operations
  - Built-in export formats (users can create their own using `to_dict()`)

  See `docs/GOOGLE_KML_EXTENSIONS.md` and `docs/KML_ORM_SPECIFICATION.md` for details.

  This project depends on `lxml`. You'll need to install it in your environment if you want to use `kmlorm`.

## License

MIT License. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## Credits
 
- Developed by Jack Nerad with assistance from Claude (Anthropic) and ChatGPT GPT-4.1 (OpenAI) AI Assistants
- Built with a custom XML parser that uses `lxml`.  All credit really belongs to the `lxml` folks.  `kmlorm` is just a django'ish face on their superb work.
- Inspired by Django's ORM design patterns