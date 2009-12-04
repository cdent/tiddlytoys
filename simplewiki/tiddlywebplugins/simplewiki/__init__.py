"""
A simplewiki using markdown syntax, hosted at a /route
of your choosing.

Old school wiki and web in action.
"""

import urllib


from tiddlywebplugins.utils import do_html, map_to_tiddler
from tiddlyweb.web.http import HTTP302, HTTP303, HTTP404
from tiddlyweb.web.util import server_base_url
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.recipe import Recipe
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.policy import ForbiddenError, UserRequiredError
from tiddlyweb.store import NoBagError
from tiddlyweb import control
from tiddlyweb.wikitext import render_wikitext
from tiddlywebplugins.templates import get_template
from tiddlyweb.web.wsgi import _challenge_url

def init(config):
    route_base = _route_base(config)
    config['markdown.wiki_link_base'] = ''

    config['selector'].add('%s[/]' % route_base, GET=home)
    config['selector'].add('%s/{tiddler_name:alpha}' % route_base, GET=page, POST=edit)
    config['selector'].add('%s/{tiddler_name:alpha};editor' % route_base, GET=editor, POST=edit)

    config['wikitext.type_render_map'].update({
        'text/x-markdown': 'tiddlywebplugins.markdown', # replace with plugin when it exists
        })


def recent_changes(tiddler, environ):
    store = environ['tiddlyweb.store']
    recipe = _get_recipe(environ)
    recipe = store.get(Recipe(recipe))
    tmpbag = Bag('tmpbag', tmpbag=True)
    tmpbag.add_tiddlers(control.get_tiddlers_from_recipe(recipe, environ))
    tiddlers = control.filter_tiddlers_from_bag(tmpbag, 'sort=-modified;limit=30')
    template = get_template(environ, 'changes.html')
    environ['tiddlyweb.title'] = 'Recent Changes'
    return template.generate(tiddlers=tiddlers)


def home(environ, start_response):
    config = environ['tiddlyweb.config']
    location = '%s%s/%s' % (server_base_url(environ),
            _route_base(config),
            _front_page(config))
    raise HTTP302(location)


@do_html()
def page(environ, start_response):
    tiddler = _determine_tiddler(environ)

    if tiddler.title in SPECIAL_PAGES:
        return SPECIAL_PAGES[tiddler.title](tiddler, environ)

    template = get_template(environ, 'page.html')
    environ['tiddlyweb.title'] = tiddler.title
    return template.generate(html=render_wikitext(tiddler, environ),
            tiddler=tiddler)


@do_html()
def edit(environ, start_response):
    user = environ['tiddlyweb.usersign']
    tiddler = _determine_tiddler(environ)
    tiddler.text = environ['tiddlyweb.query']['text'][0]
    store = environ['tiddlyweb.store']
    config = environ['tiddlyweb.config']

    # if _determine_tiddler loaded the tiddler from the store
    # then bag will be set and we know that the tiddler is not new
    tiddler_new = True
    if tiddler.bag:
        print 'bag ', tiddler.bag
        tiddler_new = False

    try:
        recipe = _get_recipe(config)
        recipe = store.get(Recipe(recipe))
        bag = control.determine_bag_for_tiddler(recipe, tiddler, environ)
        tiddler.bag = bag.name
    except NoBagError, exc:
        raise HTTP404('No suitable bag to store tiddler %s found, %s' % (tiddler.title, exc))

    bag = store.get(bag)
    try:
        if tiddler_new:
            bag.policy.allows(user, 'create')
        else:
            bag.policy.allows(user, 'write')
    except (UserRequiredError, ForbiddenError):
        challenge_url = _challenge_url(environ)
        message = """
You do not have permission. Copy your edits, <a href="%s">login</a>, then try again.
""" % challenge_url
        return _editor_display(environ, tiddler, message=message)

    store.put(tiddler)
    location = '%s%s/%s' % (server_base_url(environ),
            _route_base(config), tiddler.title)
    raise HTTP303(location)


@do_html()
def editor(environ, start_response):
    tiddler = _determine_tiddler(environ)
    return _editor_display(environ, tiddler)


def _editor_display(environ, tiddler, message=''):
    template = get_template(environ, 'editor.html')
    environ['tiddlyweb.title'] = 'Edit ' + tiddler.title
    return template.generate(tiddler=tiddler, message=message)


def _front_page(config):
    return config.get('simplewiki.frontpage', 'FrontPage')
    

def _route_base(config):
    return config.get('simplewiki.route_base', '/wiki')


def _get_recipe(config):
    return config.get('simplewiki.recipe', 'wiki')


def _determine_tiddler(environ):
    user = environ['tiddlyweb.usersign']
    config = environ['tiddlyweb.config']
    store = environ['tiddlyweb.store']
    recipe = Recipe(_get_recipe(config))
    recipe = store.get(recipe)
    recipe.policy.allows(user, 'read')

    tiddler_name = environ['wsgiorg.routing_args'][1]['tiddler_name']
    tiddler_name = urllib.unquote(tiddler_name)
    tiddler_name = unicode(tiddler_name, 'utf-8')
    tiddler = Tiddler(tiddler_name)

    try:
        bag = control.determine_tiddler_bag_from_recipe(recipe, tiddler, environ)
        bag.policy.allows(user, 'read')
        tiddler.bag = bag.name
        tiddler = store.get(tiddler)
    except NoBagError, exc:
        # Apparently the tiddler doesn't exist, let's fill in an empty one
        # then.
        tiddler.text = 'That Page does not yet exist.'
        tiddler.type = 'text/x-markdown'

    return tiddler

SPECIAL_PAGES = {
        'RecentChanges': recent_changes,
        }
