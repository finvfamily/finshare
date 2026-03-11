# Configuration file for the Sphinx documentation builder.

project = 'finshare'
copyright = '2024, finshare'
author = 'finshare'

release = '1.0.3'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_baseurl = 'https://finvfamily.github.io/finshare/'

html_theme_options = {
    'canonical_url': 'https://finvfamily.github.io/finshare/',
    'analytics_id': '',
    'display_version': True,
    'prev_next_buttons_location': 'both',
    'style_external_links': False,
    'style_nav_header_background': '#2980b9',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    'expand_navigation': True,
}

html_js_files = [
    'navigation.js',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
}

myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'task_lists',
]

html_context = {
    'display_github': True,
    'github_user': 'finvfamily',
    'github_repo': 'finshare',
    'github_version': 'main',
}
