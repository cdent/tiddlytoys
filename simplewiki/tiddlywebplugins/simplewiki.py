"""
A simplewiki using markdown syntax, hosted at a /route
of your choosing.

Old school wiki and web in action.
"""

import urllib


from tiddlywebplugins.utils import do_html, map_to_tiddler
from tiddlyweb.web.http import HTTP302, HTTP303, HTTP404
from tiddlyweb.web.util import server_base_url
from tiddlyweb.model.recipe import Recipe
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import NoBagError
from tiddlyweb import control
from tiddlyweb.wikitext import render_wikitext


def init(config):
    route_base = _route_base(config)
    config['markdown.wiki_link_base'] = '%s%s/' % (
            config['server_prefix'], route_base)

    config['selector'].add('%s[/]' % route_base, GET=home)
    config['selector'].add('%s/{tiddler_name}' % route_base, GET=page, POST=edit)
    config['selector'].add('%s/{tiddler_name};editor' % route_base, GET=editor, POST=edit)

    config['wikitext.type_render_map'].update({
        'text/x-markdown': 'markdown', # replace with plugin when it exists
        })


def home(environ, start_response):
    config = environ['tiddlyweb.config']
    location = '%s%s/%s' % (server_base_url(environ),
            _route_base(config),
            _front_page(config))
    raise HTTP302(location)
    

@do_html()
def page(environ, start_response):
    config = environ['tiddlyweb.config']
    store = environ['tiddlyweb.store']
    recipe = Recipe(_get_recipe(config))
    recipe = store.get(recipe)

    tiddler_name = environ['wsgiorg.routing_args'][1]['tiddler_name']
    tiddler_name = urllib.unquote(tiddler_name)
    tiddler_name = unicode(tiddler_name, 'utf-8')
    tiddler = Tiddler(tiddler_name)

    try:
        bag = control.determine_tiddler_bag_from_recipe(recipe, tiddler, environ)
        tiddler.bag = bag.name
        tiddler = store.get(tiddler)
    except NoBagError, exc:
        # Apparently the tiddler doesn't exist, let's fill in an empty one
        # then.
        tiddler.text = 'That Page does not yet exist.'
        tiddler.type = 'text/x-markdown'

    html = '<div class="tiddler">' + render_wikitext(tiddler, environ) + '</div>'
    environ['tiddlyweb.title'] = tiddler.title
    return [html]


def edit(environ, start_response):
    pass


@do_html()
def editor(environ, start_response):
    pass


def _front_page(config):
    return config.get('simplewiki.frontpage', 'FrontPage')
    

def _route_base(config):
    return config.get('simplewiki.route_base', '/wiki')


def _get_recipe(config):
    return config.get('simplewiki.recipe', 'wiki')
