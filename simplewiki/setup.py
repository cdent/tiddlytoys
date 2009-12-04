
AUTHOR = 'Chris Dent'
AUTHOR_EMAIL = 'cdent@peermore.com'
NAME = 'tiddlywebplugins.simplewiki'
DESCRIPTION = 'A simple markdown based wiki in TiddlyWeb'
VERSION = '0.5'

import os
from setuptools import setup, find_packages

setup(
        namespace_packages = ['tiddlywebplugins'],
        name = NAME,
        version = VERSION,
        description = DESCRIPTION,
        long_description=file(os.path.join(os.path.dirname(__file__), 'README')).read(),
        author = AUTHOR,
        scripts = ['simplewiki'],
        url = 'http://pypi.python.org/pypi/%s' % NAME,
        packages = find_packages(exclude=['test']),
        author_email = AUTHOR_EMAIL,
        platforms = 'Posix; MacOS X; Windows',
        install_requires = ['tiddlyweb>=0.9.79',
            'tiddlywebplugins.templates',
            'tiddlywebplugins.instancer',
            'tiddlywebplugins.utils',
            'tiddlywebplugins.markdown'],
        include_package_data = True,
        zip_safe = False,
        )
