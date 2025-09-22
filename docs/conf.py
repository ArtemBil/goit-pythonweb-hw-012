# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# <https://www.sphinx-doc.org/en/master/usage/configuration.html>

# -- Project information -----------------------------------------------------
# <https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information>
import os
import sys
from datetime import datetime

# Add project root to sys.path for autodoc imports
sys.path.insert(0, os.path.abspath('..'))

project = 'Contacts API'
copyright = f'{datetime.now().year}, Artem Bilko'
author = 'Artem Bilko'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# <https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration>

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

autodoc_mock_imports = [
    'fastapi', 'starlette', 'slowapi',
    'sqlalchemy',
    'redis', 'redis.asyncio',
    'fastapi_mail',
    'cloudinary',
    'passlib',
    'jose',
    'pydantic', 'pydantic_settings',
]

templates_path = ['_templates']
exclude_patterns = ['_build']

# -- Options for HTML output -------------------------------------------------
# <https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output>

html_theme = 'alabaster'
html_static_path = ['_static']

