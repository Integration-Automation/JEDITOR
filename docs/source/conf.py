# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath("source"))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# -- Project information -----------------------------------------------------

project = "JEditor"
project_copyright = "2021 ~ Present, JE-Chen"
author = "JE-Chen"
release = "1.0.10"

# -- General configuration ---------------------------------------------------

extensions = []

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Internationalization ----------------------------------------------------

locale_dirs = ["locale/"]
gettext_compact = False
