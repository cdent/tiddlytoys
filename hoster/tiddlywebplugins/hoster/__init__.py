"""
Host customizable TiddlyWikis on TiddlyWeb.
"""

__version__ = '0.2'

from tiddlyweb.model.policy import UserRequiredError, ForbiddenError
from tiddlyweb.model.user import User
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import NoBagError, NoTiddlerError, NoUserError
from tiddlyweb.web.http import HTTP302, HTTP404
from tiddlyweb.web.util import server_base_url
from tiddlywebplugins.utils import replace_handler, do_html, ensure_bag
from tiddlywebplugins.templates import get_template
from tiddlyweb.wikitext import render_wikitext


def init(config):
    import tiddlywebwiki
    import tiddlywebplugins.register
    import tiddlywebplugins.wimporter
    tiddlywebwiki.init(config)
    tiddlywebplugins.register.init(config)
    tiddlywebplugins.wimporter.init(config)

    if config['selector']:
        replace_handler(config['selector'], '/', dict(GET=front))
        config['selector'].add('/help', GET=help)
        config['selector'].add('/{userpage:segment}', GET=userpage)

@do_html()
def help(environ, start_response):
    user = _get_user_object(environ)
    data = {}
    data['user'] = user
    return _send_template(environ, 'help.html', data) 

@do_html()
def front(environ, start_response):
    user = _get_user_object(environ)
    data = {}
    data['user'] = user
    return _send_template(environ, 'home.html', data)


@do_html()
def userpage(environ, start_response):
    userpage = environ['wsgiorg.routing_args'][1]['userpage']
    user = environ['tiddlyweb.usersign']

    if userpage == 'home':
        userpage = user['name']
    if userpage == 'GUEST' or 'MEMBER' not in user['roles']:
        location = '%s/' % server_base_url(environ)
        raise HTTP302(location)

    store = environ['tiddlyweb.store']

    # If we try to go to a user page that doesn't exist,
    # just go to the home page. XXX maybe should 404 instead.
    try:
        userpage_user = User(userpage)
        userpage_user = store.get(userpage_user)
    except NoUserError:
        pass # roles will be empty
    if 'MEMBER' not in userpage_user.list_roles():
        raise HTTP404('%s has no page' % userpage)

    profile_tiddler = _get_profile(store, user, userpage)
    profile_html = render_wikitext(profile_tiddler, environ)
    kept_recipes = _get_stuff(store, store.list_recipes(), user, userpage)
    kept_bags = _get_stuff(store, store.list_bags(), user, userpage)
    data = {'bags': kept_bags,
            'recipes': kept_recipes,
            'home': userpage,
            'profile': profile_html,
            'user': _get_user_object(environ)}

    return _send_template(environ, 'profile.html', data)

def _get_profile(store, user, userpage):
    try:
        tiddler = Tiddler('profile', userpage)
        tiddler = store.get(tiddler)
    except NoTiddlerError:
        if user['name'] == userpage:
            _ensure_user_bag(store, userpage)
            tiddler.text = '!!!You can make a profile!\n'
        else:
            tiddler.text = '!!!No profile yet!\n'
    return tiddler


def _ensure_user_bag(store, userpage):
    policy = {}
    policy['read'] = ['R:MEMBER']

    for constraint in ['write', 'create', 'delete', 'manage']:
        policy[constraint] = [userpage]

    ensure_bag(userpage, store, policy, owner=userpage)


def _get_stuff(store, entities, user, owner):
    """
    Get a sub-list of recipes or bags from the provided
    list which is readable by the given user and owned
    by the user represented given owner.
    """
    kept_entities = []
    for entity in entities:
        if hasattr(entity, 'skinny'):
            entity.skinny = True
        entity = store.get(entity)
        if entity.policy.owner == owner:
            try:
                entity.policy.allows(user, 'read')
                kept_entities.append(entity)
            except (UserRequiredError, ForbiddenError):
                pass
    return kept_entities

def _get_user_object(environ):
    user = environ['tiddlyweb.usersign']
    if user['name'] == 'GUEST':
        user['pretty_name'] = 'GUEST'
    elif 'MEMBER' in user['roles']:
        store = environ['tiddlyweb.store']
        userobject = store.get(User(user['name']))
        if userobject.note:
            user['pretty_name'] = userobject.note
        else:
            user['pretty_name'] = user['name']
    else:
        user['pretty_name'] = user['name']
    return user


def _send_template(environ, template_name, template_data):
    template = get_template(environ, template_name)
    server_prefix = environ['tiddlyweb.config']['server_prefix']
    template_defaults = {
            #'message': 'test me you are a message',
            'member_role': 'MEMBER',
            'title': 'TiddlyHoster',
            'userpage': {
                'link': '%s/home' % server_prefix,
                'title': 'homepage',
                },
            'login': {
                'link': '%s/challenge' % server_prefix,
                'title': 'Login',
                },
            'help': {
                'link': '%s/help' % server_prefix,
                'title': 'Help',
                },
            'register': {
                'link': '%s/register' % server_prefix,
                'title': 'Register',
                },
            'server_prefix': server_prefix,
            'main_css': environ['tiddlyweb.config'].get(
                'hoster.main_css', 'main.css'),
            }
    template_defaults.update(template_data)
    return template.generate(template_defaults)
