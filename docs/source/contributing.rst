Contributing
============

We welcome contributions to KML ORM! This guide will help you get started.

Development Setup
-----------------

1. **Fork and Clone**:

   .. code-block:: bash

      git clone https://github.com/yourusername/kmlorm.git
      cd kmlorm

2. **Create Virtual Environment**:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install Development Dependencies**:

   .. code-block:: bash

      pip install -e .[dev]

4. **Install Pre-commit Hooks**:

   .. code-block:: bash

      pre-commit install

Code Quality Standards
----------------------

We maintain high code quality standards:

* **Type Hints**: All functions must have type hints
* **Docstrings**: All public methods must have Google-style docstrings
* **Testing**: All new features must include tests
* **Code Style**: Follow PEP 8 with 100-character line length

Development Tools
-----------------

Run these commands before submitting:

.. code-block:: bash

   # Format code
   black .
   isort .

   # Lint code
   flake8
   pylint kmlorm/

   # Type checking
   mypy .

   # Run tests
   pytest

Testing Guidelines
------------------

* Write tests for all new functionality
* Include edge cases and error conditions
* Use pytest fixtures for test data
* Maintain test coverage above 80%

Test Structure:

.. code-block:: python

   class TestNewFeature:
       def test_basic_functionality(self):
           """Test basic feature operation."""
           # Arrange
           kml = KMLFile.from_string(test_kml_data)

           # Act
           result = kml.new_feature()

           # Assert
           assert result is not None

Documentation
-------------

* Update docstrings for any changed methods
* Add examples to docstrings where helpful
* Update this documentation if adding new features
* Build docs locally to test: ``cd docs && make html``

Submitting Changes
------------------

1. **Create Feature Branch**:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make Changes**: Implement your feature with tests

3. **Run Quality Checks**:

   .. code-block:: bash

      black . && isort . && flake8 && mypy . && pytest

4. **Commit Changes**:

   .. code-block:: bash

      git add .
      git commit -m "Add feature: your feature description"

5. **Push and Create PR**:

   .. code-block:: bash

      git push origin feature/your-feature-name

Then create a pull request on GitHub.

Release Process
---------------

For maintainers:

1. Update version in ``pyproject.toml``
2. Update ``CHANGELOG.md``
3. Create release tag
4. GitHub Actions will handle PyPI deployment

Getting Help
------------

* **Issues**: Report bugs or request features on GitHub Issues
* **Discussions**: Ask questions in GitHub Discussions
* **Code Review**: All PRs require review before merging

Thank you for contributing to KML ORM!