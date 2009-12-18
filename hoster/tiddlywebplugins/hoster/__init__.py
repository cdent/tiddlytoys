"""
Host customizable TiddlyWikis on TiddlyWeb.
"""

__version__ = '0.2'

import Cookie
import time

from hashlib import md5

from tiddlyweb import __version__ as VERSION
from tiddlyweb.model.policy import UserRequiredError, ForbiddenError
from tiddlyweb.model.user import User
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.recipe import Recipe
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import NoBagError, NoTiddlerError, NoUserError
from tiddlyweb.web.http import HTTP302, HTTP404
from tiddlyweb.web.util import server_base_url
from tiddlyweb.web.wsgi import HTMLPresenter
from tiddlywebplugins.utils import replace_handler, do_html, ensure_bag
from tiddlywebplugins.templates import get_template
from tiddlyweb.wikitext import render_wikitext
from tiddlywebplugins.hoster.instance import instance_tiddlers
from tiddlyweb.web.extractors.simple_cookie import Extractor as SimpleExtractor


def init(config):
    import tiddlywebwiki
    import tiddlywebplugins.register
    import tiddlywebplugins.wimporter
    tiddlywebwiki.init(config)
    tiddlywebplugins.register.init(config)
    tiddlywebplugins.wimporter.init(config)
    
    # XXX this clobbers?
    config['instance_tiddlers'] = instance_tiddlers

    if config['selector']:
        replace_handler(config['selector'], '/', dict(GET=front))
        config['selector'].add('/help', GET=help)
        config['selector'].add('/formeditor', GET=get_profiler, POST=post_profile)
        config['selector'].add('/addemail', POST=add_email)
        config['selector'].add('/follow', POST=add_friend)
        config['selector'].add('/logout', POST=logout)
        config['selector'].add('/members', GET=members)
        config['selector'].add('/{userpage:segment}', GET=userpage)
        presenter_index = config['server_response_filters'].index(HTMLPresenter)
        config['server_response_filters'][presenter_index] = PrettyPresenter
        simple_cookie_index = config['extractors'].index('simple_cookie')
        config['extractors'][simple_cookie_index] = 'tiddlywebplugins.hoster'


@do_html()
def members(environ, start_response):
    store = environ['tiddlyweb.store']
    member_names = sorted(_get_member_names(store))
    members = []
    for member in member_names:
        email = _get_email_tiddler(store, member)
        email_md5 = md5(email.lower()).hexdigest()
        members.append((member, email_md5))
    return _send_template(environ, 'members.html', {'members': members}) 


def _get_member_names(store):
    def _reify_user(username):
        return store.get(username)
    names = (user.usersign for user in store.list_users() if
            'MEMBER' in _reify_user(user).list_roles())
    return names

def logout(environ, start_response):
    cookie = Cookie.SimpleCookie()
    path = environ['tiddlyweb.config']['server_prefix']
    cookie['tiddlyweb_user'] = ''
    cookie['tiddlyweb_user']['path'] = '%s/' % path
    cookie['tiddlyweb_user']['expires'] = '%s' % (time.ctime(time.time()-6000))
    uri = server_base_url(environ)
    start_response('303 See Other', [
        ('Set-Cookie', cookie.output(header='')),
        ('Location', uri),
        ])
    return uri


def add_friend(environ, start_response):
    user = _get_user_object(environ)
    store = environ['tiddlyweb.store']
    _ensure_user_bag(store, user['name'])
    new_friend = environ['tiddlyweb.query'].get('name', None)[0]
    tiddler = Tiddler('friends', user['name'])
    try:
        store.get(tiddler)
        friends = tiddler.text.splitlines()
    except NoTiddlerError:
        friends = []
    if new_friend and new_friend not in friends:
        friends.append(new_friend)
    tiddler.text = '\n'.join(friends)
    store.put(tiddler)
    raise HTTP302('%s/%s' % (server_base_url(environ), user['name']))


def add_email(environ, start_response):
    user = _get_user_object(environ)
    store = environ['tiddlyweb.store']
    _ensure_user_bag(store, user['name'])
    tiddler = Tiddler('email', user['name'])
    email = environ['tiddlyweb.query'].get('email', [''])[0]
    tiddler.text = email
    store.put(tiddler)
    raise HTTP302('%s/%s' % (server_base_url(environ), user['name']))


@do_html()
def help(environ, start_response):
    return _send_template(environ, 'help.html') 

@do_html()
def front(environ, start_response):
    return _send_template(environ, 'home.html')


def first_time_check(environ, user):
    username = user['name']
    store = environ['tiddlyweb.store']
    try:
        bag = Bag(username)
        store.get(bag)
    except NoBagError:
        _ensure_public_bag(store, username)
        _ensure_private_bag(store, username)
        _ensure_public_recipe(store, username)
        _ensure_private_recipe(store, username)
        _ensure_user_bag(store, username)


@do_html()
def userpage(environ, start_response):
    userpage = environ['wsgiorg.routing_args'][1]['userpage']
    user = environ['tiddlyweb.usersign']

    first_time_check(environ, user)

    if userpage == 'home':
        userpage = user['name']

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

    user_friend_names = _get_friends(store, user['name'])
    friend_names = sorted(_get_friends(store, userpage))
    friends = []
    for name in friend_names:
        email = _get_email_tiddler(store, name)
        email_md5 = md5(email.lower()).hexdigest()
        friends.append((name, email_md5))

    profile_tiddler = _get_profile(store, user, userpage)
    profile_html = render_wikitext(profile_tiddler, environ)
    kept_recipes = _get_stuff(store, store.list_recipes(), user, userpage)
    kept_bags = _get_stuff(store, store.list_bags(), user, userpage)
    email = _get_email_tiddler(store, userpage)
    email_md5 = md5(email.lower()).hexdigest()
    data = {'bags': kept_bags,
            'user_friends': user_friend_names,
            'friends': friends,
            'recipes': kept_recipes,
            'home': userpage,
            'profile': profile_html,
            'email': email,
            'email_md5': email_md5,
            'user': _get_user_object(environ)}

    return _send_template(environ, 'profile.html', data)


def _get_friends(store, username):
    tiddler = Tiddler('friends', username)
    try:
        store.get(tiddler)
        friends = tiddler.text.splitlines()
    except NoTiddlerError:
        friends = []
    return friends

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


def _get_email_tiddler(store, userpage):
    try:
        tiddler = Tiddler('email', userpage)
        tiddler = store.get(tiddler)
    except NoTiddlerError:
        tiddler.text = ''
    return tiddler.text


def _ensure_user_bag(store, userpage):
    policy = {}
    policy['manage'] = ['R:ADMIN']

    for constraint in ['read', 'write', 'create', 'delete']:
        policy[constraint] = [userpage]

    policy['owner'] = userpage

    ensure_bag(userpage, store, policy)


def _ensure_public_bag(store, username):
    policy = {}
    policy['read'] = []
    for constraint in ['write', 'create', 'delete', 'manage']:
        policy[constraint] = [username]
    policy['owner'] = username
    ensure_bag('%s-public' % username, store, policy)


def _ensure_private_bag(store, username):
    policy = {}
    for constraint in ['read', 'write', 'create', 'delete', 'manage']:
        policy[constraint] = [username]
    policy['owner'] = username
    ensure_bag('%s-private' % username, store, policy)


def _ensure_public_recipe(store, username):
    name = '%s-public' % username
    recipe = Recipe(name)
    recipe.policy.read = []
    recipe.policy.manage = [username]
    recipe.policy.owner = username
    recipe.set_recipe([
        ('system', ''),
        (name, ''),
        ])
    store.put(recipe)


def _ensure_private_recipe(store, username):
    name = '%s-private' % username
    pname = '%s-public' % username
    recipe = Recipe(name)
    recipe.policy.read = [username]
    recipe.policy.manage = [username]
    recipe.policy.owner = username
    recipe.set_recipe([
        ('system', ''),
        (pname, ''),
        (name, ''),
        ])
    store.put(recipe)


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


def _send_template(environ, template_name, template_data=None):
    if template_data == None:
        template_data = {}
    template = get_template(environ, template_name)
    server_prefix = environ['tiddlyweb.config']['server_prefix']
    user = _get_user_object(environ)
    template_defaults = {
            #'message': 'test me you are a message',
            'version': VERSION,
            'user': user,
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


@do_html()
def get_profiler(environ, start_response):
    usersign = environ['tiddlyweb.usersign']
    store = environ['tiddlyweb.store']
    username = usersign['name']

    if not 'MEMBER' in usersign['roles']:
        raise HTTP404('bad edit')

    tiddler = _get_profile(store, usersign, username)
    bag = Bag(tiddler.bag)
    bag = store.get(bag)
    bag.policy.allows(usersign, 'write')

    return_url = '%s/home' % server_base_url(environ)

    data = {}
    data['tiddler'] = tiddler
    data['return_url'] = return_url
    return _send_template(environ, 'profile_edit.html', data)


def post_profile(environ, start_response):
    usersign = environ['tiddlyweb.usersign']
    text = environ['tiddlyweb.query'].get('text', [''])[0]
    title = environ['tiddlyweb.query'].get('title', [''])[0]
    bag = environ['tiddlyweb.query'].get('bag', [''])[0]
    return_url = environ['tiddlyweb.query'].get('return_url', ['/home'])[0]

    store = environ['tiddlyweb.store']

    tiddler = Tiddler(title, bag)
    tiddler.text = text
    tiddler.modifier = usersign['name']
    bag = Bag(bag)
    try:
        bag = store.get(bag)
    except NoBagError, exc:
        raise HTTP404('tiddler %s not found: %s' % (tiddler.title, exc))

    bag.policy.allows(usersign, 'write')

    store.put(tiddler)

    raise HTTP302(return_url)


class PrettyPresenter(HTMLPresenter):

    def __call__(self, environ, start_response):
        output = self.application(environ, start_response)
        if self._needs_title(environ):
            output = ''.join(output)
            data = {
                    'output': output,
                    'title': environ['tiddlyweb.title'],
                    }
            return _send_template(environ, 'pretty.html', data)
        return output

class Extractor(SimpleExtractor):

    def extract(self, environ, start_response):
        results = SimpleExtractor.extract(self, environ, start_response)
        if results:
            store = environ['tiddlyweb.store']
            user_dict = results
            username = user_dict['name']
            users_friends = _get_friends(store, username)
            friended_user = _get_followers(store, username)

            for friend in users_friends:
                user_dict['roles'].append('%s-is-friend' % friend)
            for friend in friended_user:
                user_dict['roles'].append('friend-of-%s' % friend)

            return user_dict
        return results

def _get_followers(store, username):
    """
    Get all the users who have username as a friend.
    """
    member_names = _get_member_names(store)
    followers = []
    for member_name in member_names:
        if member_name == username:
            continue
        if username in _get_friends(store, member_name):
            followers.append(member_name)
    return followers
