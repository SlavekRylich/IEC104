# -*- coding: utf-8 -*-
#
# Configuration file for Sphinx documentation
#
# This file is used to configure the Sphinx documentation system.
# For more information, see the Sphinx documentation:
# https://www.sphinx-doc.org/en/latest/

# General information about the project.
project = 'Název Vašeho Projektu'
copyright = '2024 Autor Vašeho Jména'
author = 'Vaše Jméno'

# The version info for the project you're documenting.
# Releases are numbered by using the semver versioning scheme,
# e.g. 1.0.0, 1.0.1, 1.1.0, etc.
version = '0.1.0'
release = '0.1.0'

# The language for the generated documentation.
language = 'en'

# List of available extensions. See https://www.sphinx-doc.org/en/latest/usage/extensions.html
# for more information.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.imgmath',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.githubpages',
]

# Add any paths that contain docstrings.
autodoc_mock_imports = ['tensorflow', 'numpy']
autodoc_member_order = 'bysource'

# Set the intersphinx links for your project.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

# The HTML theme for the generated documentation.
html_theme = 'sphinx_rtd_theme'

# The name of the PyPI project package to use as the base theme.
html_theme_path = ['.themes']

# Additional settings for the HTML theme.
html_sidebars = {
    'default': ['sidebar/toctree.html', 'sidebar/search.html'],
}

# Other options for the HTML output.
html_static_path = ['_static']
html_css_files = ['custom.css']
html_js_files = ['custom.js']

# The name of the EPUB file to generate.
epub_title = 'Název Vašeho Projektu'
epub_author = 'Vaše Jméno'
epub_publisher = 'Vaše Jméno'
epub_copyright = '2024 Autor Vašeho Jména'

# The name of the MOBI file to generate.
kindle_title = 'Název Vašeho Projektu'
kindle_author = 'Vaše Jméno'
kindle_publisher = 'Vaše Jméno'
kindle_copyright = '2024 Autor Vašeho Jména'

# The name of the PDF file to generate.
pdf_title = 'Název Vašeho Projektu'
pdf_author = 'Vaše Jméno'
pdf_publisher = 'Vaše Jméno'
pdf_copyright = '2024 Autor Vašeho Jména'

# If true, Sphinx will create a .rst file for each .py file it parses.
# This can be useful for debugging.
create_ngdocs = False

# If true, Sphinx will create a .json file containing all of the documentation
# information. This can be useful for external tools.
json_use_underscores = True
json_use_toc = True
json_use_index = True
json_use_private = True
json_use_symbols = True
