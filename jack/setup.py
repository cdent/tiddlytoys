"""
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from jack import __version__ as VERSION

setup(name = 'jack',
        version = VERSION,
        description = 'A TiddlyWeb jack of all trades',
        author = 'Chris Dent',
        author_email = 'cdent@peermore.com',
        packages = ['jack'],
        py_modules = ['sql', 'formreader', 'static', 'whoosher'],
        platforms = 'Posix; MacOS X; Windows',
        install_requires = ['tiddlywebwiki'],
        include_package_data = True,
        )
