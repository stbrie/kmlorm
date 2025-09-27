# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# pylint: disable=redefined-builtin,fixme
# mypy: ignore-errors
# flake8: noqa

import os
import sys

# -- Path setup --------------------------------------------------------------
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("../../"))

# -- Project information -----------------------------------------------------
project = "KML ORM"
copyright = "2025, Jack Nerad with Claude AI and ChatGPT GPT-4.1"
author = "Jack Nerad with Claude AI and ChatGPT GPT-4.1"
release = "1.0.0"
version = "1.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_autodoc_typehints",
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# Todo extension settings
todo_include_todos = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = []

language = "en"

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# RTD theme options
html_theme_options = {
    "canonical_url": "",
    "analytics_id": "",
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "#2980B9",
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# HTML context
html_context = {
    "display_github": True,
    "github_user": "stbrie",
    "github_repo": "kmlorm",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

html_title = f"{project} v{version}"
html_short_title = project
