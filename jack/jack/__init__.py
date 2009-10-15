__version__ = '0.1'

from tiddlywebplugins import replace_handler
from tiddlyweb.web.http import HTTP302


def index(environ, start_response):
    raise HTTP302('/static/search.html')


def init(config):
    replace_handler(config['selector'], '/', dict(GET=index))
