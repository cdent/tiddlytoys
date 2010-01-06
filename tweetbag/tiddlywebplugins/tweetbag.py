"""
"""
import oauth
import urllib2
import simplejson

from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.web.http import HTTP302, HTTP303, HTTP400
from tiddlyweb.web.util import server_base_url
from tiddlywebplugins.utils import (do_html, entitle,
        require_any_user, ensure_bag)
from tiddlywebplugins.templates import get_template

from tiddlyweb.store import NoTiddlerError

OAUTH_BAG = 'oauth_info'
OAUTH_BAG_POLICY = {
        'read': ["NONE"],
        'write': ["NONE"],
        'create': ["NONE"],
        'delete': ["NONE"],
        'manage': ["NONE"],
        'accept': ["NONE"],
        }
OAUTH_BAG_OWNER = 'administrator'
SERVICE_NAME = 'twitter'

class twitter:
    # XXX this information should come from a tiddler
    # probably one called service_<something>
    # the key and secret should be unique to any given installation
    # where possible
    CONSUMER_KEY = 'ux6RvTyvlK6BtGTcrw7KfQ'
    CONSUMER_SECRET = 'JxKoTVwITcZjoA5fzxdJWHJJ9cSCteBNrOti35xQblA'
    REQUEST_TOKEN_URL = 'http://twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL  = 'http://twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'http://twitter.com/oauth/authorize'


def init(config):
    if config['selector']:
        config['selector'].add('/tweetbag', GET=send, POST=handle)


@require_any_user()
def handle(environ, start_response):
    """
    Handle a POST. That is, start the current user on the path
    to having their credentials setup, based on their POST to here.
    """
    query = environ['tiddlyweb.query']
    store = environ['tiddlyweb.store']
    username = environ['tiddlyweb.usersign']['name']

    if query.get('make'):
        consumer = oauth.OAuthConsumer(twitter.CONSUMER_KEY,
                twitter.CONSUMER_SECRET)

        request = oauth.OAuthRequest.from_consumer_and_token(
                consumer,
                callback=_callback_url(environ),
                http_url=twitter.REQUEST_TOKEN_URL)

        request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(),
                consumer,
                None)
        request_url = request.to_url()
        response = urllib2.urlopen(request_url)
        token = oauth.OAuthToken.from_string(response.read())

        set_user_token(store, 'request_token', token, username)

        oauth_request = oauth.OAuthRequest.from_token_and_callback(
                token=token, http_url=twitter.AUTHORIZATION_URL)
        raise HTTP302(oauth_request.to_url())

    # the post was made oddly. do we care?
    raise HTTP400('Missing data')


@do_html()
@entitle("Get your tweets Yo")
@require_any_user()
def send(environ, start_response):
    query = environ['tiddlyweb.query']
    store = environ['tiddlyweb.store']

    username = environ['tiddlyweb.usersign']['name']

    consumer = oauth.OAuthConsumer(twitter.CONSUMER_KEY,
            twitter.CONSUMER_SECRET)

    access_token = get_user_token(store, 'access_token', username)

    if query.get('oauth_token'):
        request_token_string = get_user_token(store, 'request_token', username)
        if request_token_string == None:
            # we've reached this stage in weirdness
            raise HTTP302(_callback_url(environ))
        request_token = oauth.OAuthToken.from_string(request_token_string)

        query_oauth_token = environ['tiddlyweb.query']['oauth_token'][0]
        query_oauth_verifier = environ['tiddlyweb.query']['oauth_verifier'][0]

        assert query_oauth_token == request_token.key

        request = oauth.OAuthRequest.from_consumer_and_token(
                consumer,
                token=request_token,
                verifier=query_oauth_verifier,
                http_url=twitter.ACCESS_TOKEN_URL)
        request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(),
                consumer,
                request_token)

        request_url = request.to_url()
        response = urllib2.urlopen(request_url)
        token = oauth.OAuthToken.from_string(response.read())

        set_user_token(store, 'access_token', token, username)
        raise HTTP302(_callback_url(environ))
    elif access_token:
        access_token = oauth.OAuthToken.from_string(access_token)

        request = oauth.OAuthRequest.from_consumer_and_token(
                consumer,
                token=access_token,
                http_url='http://twitter.com/statuses/user_timeline.json')
        request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(),
                consumer,
                access_token)

        url = request.to_url()
        response = urllib2.urlopen(url)

        tweets = simplejson.loads(response.read())
        return _send_template(environ, 'tweetbag.html', {'tweets': tweets}) 
    else:
        return _send_template(environ, 'tweetbag.html') 


def _send_template(environ, template_name, template_data=None):
    if template_data == None:
        template_data = {}
    template = get_template(environ, template_name)
    server_prefix = environ['tiddlyweb.config']['server_prefix']
    template_defaults = {
            'user': environ['tiddlyweb.usersign'],
            'server_prefix': server_prefix,
            }
    template_defaults.update(template_data)
    return template.generate(template_defaults)


def _callback_url(environ):
    return server_base_url(environ) + '/tweetbag'


def get_user_token(store, token_name, username):
    ensure_bag(OAUTH_BAG, store, OAUTH_BAG_POLICY,
            description='oauth info', owner=OAUTH_BAG_OWNER)
    user_tiddler_title = '%s_%s' % (SERVICE_NAME, username)
    tiddler = Tiddler(user_tiddler_title, OAUTH_BAG)
    print 'getting tiddler', tiddler
    try:
        tiddler = store.get(tiddler)
        print 'got', tiddler.fields
        return tiddler.fields[token_name]
    except (NoTiddlerError, KeyError):
        return None


def set_user_token(store, token_name, token, username):
    ensure_bag(OAUTH_BAG, store, OAUTH_BAG_POLICY,
            description='oauth info', owner=OAUTH_BAG_OWNER)
    user_tiddler_title = '%s_%s' % (SERVICE_NAME, username)
    tiddler = Tiddler(user_tiddler_title, OAUTH_BAG)
    try:
        tiddler = store.get(tiddler)
    except NoTiddlerError:
        pass # we okay if it isn't there
    tiddler.fields[token_name] = token.to_string()
    store.put(tiddler)
