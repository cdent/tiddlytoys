"""
A simplewiki using markdown syntax, hosted at a /route 
of your choosing, defaulting to /wiki

Old school wiki and web in action.
"""

import urllib

from tiddlywebplugins.utils import do_html, map_to_tiddler
from tiddlywebplugins.templates import get_template

from tiddlyweb import control

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.recipe import Recipe
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.policy import ForbiddenError, UserRequiredError

from tiddlyweb.store import NoBagError

from tiddlyweb.web.http import HTTP302, HTTP303, HTTP404
from tiddlyweb.web.util import server_base_url
from tiddlyweb.web.wsgi import _challenge_url

from tiddlyweb.wikitext import render_wikitext

def init(config):
    """
    Set up the plugin, establishing necessary configuration settings,
    and associating selector dispatch routes with handler code.
    """
    route_base = _route_base(config)
    config['markdown.wiki_link_base'] = ''

    config['selector'].add('%s[/]' % route_base, GET=home)
    config['selector'].add('%s/{tiddler_name:alpha}' % route_base, GET=page, POST=edit)
    config['selector'].add('%s/{tiddler_name:alpha};editor' % route_base, GET=editor, POST=edit)

    config['wikitext.type_render_map'].update({
        'text/x-markdown': 'tiddlywebplugins.markdown', # replace with plugin when it exists
        })


def recent_changes(tiddler, environ):
    """
    Display recent changes for the wiki. RecentChanges is handled
    as a SPECIAL_PAGES, described below.

    Recent changes are simply the 30 most recently modified tiddlers
    from the recipe. We make a list of those tiddlers and provide 
    them to the changes.html template.
    """
    # XXX to be strict we should do permissions checking
    # on the bags of all the tiddlers returned.
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
    """
    If we go to the base of the wiki route, redirect to the FrontPage.
    """
    config = environ['tiddlyweb.config']
    location = '%s%s/%s' % (server_base_url(environ),
            _route_base(config),
            _front_page(config))
    raise HTTP302(location)


@do_html()
def page(environ, start_response):
    """
    Display a page created from the tiddler named in the URL.
    If the tiddler title is in SPECIAL_PAGES, run the special
    page handling code. Otherwise, render the tiddler to html
    and provide it to the page.html template.
    """
    tiddler = _determine_tiddler(environ)

    if tiddler.title in SPECIAL_PAGES:
        return SPECIAL_PAGES[tiddler.title](tiddler, environ)

    template = get_template(environ, 'page.html')
    environ['tiddlyweb.title'] = tiddler.title
    return template.generate(html=render_wikitext(tiddler, environ),
            tiddler=tiddler)


@do_html()
def edit(environ, start_response):
    """
    Save POSTed text to the named page/tiddler. If there
    are insufficient permissions to write to the destination,
    send the edit form with a warning message. Otherwise redirect
    to the display page of the named page.
    """
    user = environ['tiddlyweb.usersign']
    tiddler = _determine_tiddler(environ)
    tiddler.text = environ['tiddlyweb.query']['text'][0]
    store = environ['tiddlyweb.store']
    config = environ['tiddlyweb.config']

    # if _determine_tiddler loaded the tiddler from the store
    # then bag will be set and we know that the tiddler is not new
    tiddler_new = True
    if tiddler.bag:
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
    """
    Display an editing interface for the tiddler named in the URL.
    """
    tiddler = _determine_tiddler(environ)
    return _editor_display(environ, tiddler)


def _editor_display(environ, tiddler, message=''):
    """
    Serve up the editing interface via the editor.html template.
    """
    template = get_template(environ, 'editor.html')
    environ['tiddlyweb.title'] = 'Edit ' + tiddler.title
    return template.generate(tiddler=tiddler, message=message)


def _front_page(config):
    """
    Query configuration to determine the name of the front or
    home page of the wiki. Defaults to FrontPage. Set
    'simplewiki.frontpage' in configuration to change.
    """
    return config.get('simplewiki.frontpage', 'FrontPage')
    

def _route_base(config):
    """
    The route on which to find the wiki. Defaults to '/wiki'.
    Set 'simplewiki.route_base' in configuration to change.
    """
    return config.get('simplewiki.route_base', '/wiki')


def _get_recipe(config):
    """
    The recipe from which to generate the wiki contents.
    Defaults to 'wiki'. Set 'simplewiki.recipe' to change.
    """
    return config.get('simplewiki.recipe', 'wiki')


def _determine_tiddler(environ):
    """
    Inspect the environment to determine which tiddler from which
    bag will provide content for the page named in the URL. If
    the page exists, and we have permission to read the bag in 
    which it is stored, the return the tiddler.

    If we do not have permission, a login interface will be shown.

    If the tiddler does not exist, an empty tiddler with stub
    text will be returned.
    """
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

"""
SPECIAL_PAGES provides a straightforward mechanism for providing
aggregation pages or other pages of interest in the same URL-space
as the wiki pages. If the name of the page shows up in this dict
it maps to code that will provide HTML to display. What that HTML
is, is up to the code. Besides the built in RecentChanges, another
option could be AllPages.
"""
SPECIAL_PAGES = {
        'RecentChanges': recent_changes,
        }
