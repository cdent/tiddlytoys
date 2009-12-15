"""
Host customizable TiddlyWikis on TiddlyWeb.
"""

__version__ = '0.1'

from tiddlyweb.model.policy import UserRequiredError, ForbiddenError
from tiddlyweb.model.user import User
from tiddlyweb.web.http import HTTP302
from tiddlyweb.web.util import server_base_url
from tiddlywebplugins.utils import replace_handler, do_html
from tiddlywebplugins.templates import get_template


def init(config):
    import tiddlywebwiki
    import tiddlywebplugins.register
    import tiddlywebplugins.wimporter
    tiddlywebwiki.init(config)
    tiddlywebplugins.register.init(config)
    tiddlywebplugins.wimporter.init(config)

    if config['selector']:
        replace_handler(config['selector'], '/', dict(GET=front))
        config['selector'].add('/{userpage:segment}', GET=userpage)

# XXX this stuff with usernames points out the critical problem
# with any user system: someday the user might change either their
# name or their openid. Then what do we do? The TiddlyWeb user
# system doesn't lend itself to indirection within the data store
# (mostly because I (cdent) didn't want TiddlyWeb dealing with this
# issue, rather other systems should deal with it.
# For now we just use the openid as the identifier.
@do_html()
def userpage(environ, start_response):
    userpage = environ['wsgiorg.routing_args'][1]['userpage']
    user = environ['tiddlyweb.usersign']

    if userpage == 'home':
        userpage = user['name']
    if userpage == 'GUEST' or 'MEMBER' not in user['roles']:
        location = '%s/' % server_base_url(environ)
        raise HTTP302(location)

    # we want to get a list of recipes and a list of bags
    # that are readable by the current user and owned by the userpage.
    # this part should probably be a separate plugin, something
    # that provides a sort "my stuff on this server" page.

    def _get_stuff(store, entities):
        kept_entities = []
        for entity in entities:
            if hasattr(entity, 'skinny'):
                entity.skinny = True
            entity = store.get(entity)
            if entity.policy.owner == userpage:
                try:
                    entity.policy.allows(user, 'read')
                    kept_entities.append(entity)
                except (UserRequiredError, ForbiddenError):
                    pass
        return kept_entities

    store = environ['tiddlyweb.store']
    kept_recipes = _get_stuff(store, store.list_recipes())
    kept_bags = _get_stuff(store, store.list_bags())
    data = {'bags': kept_bags,
            'recipes': kept_recipes,
            'home': userpage,
            'user': _get_user_object(environ)}

    return _send_template(environ, 'profile.html', data)


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


@do_html()
def front(environ, start_response):
    user = _get_user_object(environ)
    data = {}
    data['user'] = user
    return _send_template(environ, 'home.html', data)


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

