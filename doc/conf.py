# pylint: disable=invalid-name
"""Sphinx configuration."""
from datetime import datetime


project = u"Accretion"

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.spelling",
]
napoleon_include_special_with_doc = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

source_suffix = ".rst"  # The suffix of source filenames.
master_doc = "index"  # The master toctree document.

copyright = u"%s, Amazon" % datetime.now().year  # pylint: disable=redefined-builtin

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ["_build"]

pygments_style = "sphinx"

autoclass_content = "both"
autodoc_default_flags = ["show-inheritance", "members"]
autodoc_member_order = "bysource"

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
htmlhelp_basename = "%sdoc" % project

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {"python": ("http://docs.python.org/", None)}

# autosummary
autosummary_generate = True

# Spellchecker
spelling_word_list_filename = "spelling_wordlist.txt"
spelling_lang = "en_US"
spelling_ignore_python_builtins = True
spelling_ignore_importable_modules = True
