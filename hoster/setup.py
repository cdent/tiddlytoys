
AUTHOR = 'Chris Dent'
AUTHOR_EMAIL = 'cdent@peermore.com'
NAME = 'tiddlywebplugins.hoster'
DESCRIPTION = 'A hoster for TiddlyWikis'

import os
from setuptools import setup, find_packages

VERSION = '0.7'


# You should review the below so that it seems correct. install_requires
# especially.
setup(
        namespace_packages = ['tiddlywebplugins'],
        name = NAME,
        version = VERSION,
        description = DESCRIPTION,
        long_description=file(
            os.path.join(os.path.dirname(__file__), 'README')).read(),
        author = AUTHOR,
        scripts = ['betsy'],
        url = 'http://pypi.python.org/pypi/%s' % NAME,
        packages = find_packages(exclude='test'),
        author_email = AUTHOR_EMAIL,
        platforms = 'Posix; MacOS X; Windows',
        install_requires = ['setuptools',
            'tiddlyweb>=0.9.79',
            'tiddlywebplugins.utils',
            'tiddlywebplugins.templates',
            'tiddlywebwiki',
            'tiddlywebplugins.wimporter',
            'tiddlywebplugins.register',
            'tiddlywebplugins.instancer>=0.3.2',
            ],
        include_package_data = True,
        zip_safe = False,
        )
