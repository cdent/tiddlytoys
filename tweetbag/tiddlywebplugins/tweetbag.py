"""
"""
import oauth
import urllib2
import simplejson

from tiddlyweb.model.user import User
from tiddlyweb.web.http import HTTP302, HTTP303
from tiddlyweb.web.util import server_base_url
from tiddlywebplugins.utils import do_html, entitle, require_any_user
from tiddlywebplugins.templates import get_template


class twitter:
    CONSUMER_KEY = 'ux6RvTyvlK6BtGTcrw7KfQ'
    CONSUMER_SECRET = 'JxKoTVwITcZjoA5fzxdJWHJJ9cSCteBNrOti35xQblA'
    request_token_url = 'http://twitter.com/oauth/request_token'
    access_token_url  = 'http://twitter.com/oauth/access_token'
    authorization_url = 'http://twitter.com/oauth/authorize'


def init(config):
    if config['selector']:
        config['selector'].add('/tweetbag', GET=send, POST=handle)


@require_any_user()
def handle(environ, start_response):
    query = environ['tiddlyweb.query']
    store = environ['tiddlyweb.store']
    if query.get('make'):
        consumer = oauth.OAuthConsumer(twitter.CONSUMER_KEY,
                twitter.CONSUMER_SECRET)

        request = oauth.OAuthRequest.from_consumer_and_token(
                consumer,
                callback= _callback_url(environ),
                http_url=twitter.request_token_url)

        request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(),
                consumer,
                None)
        username = environ['tiddlyweb.usersign']['name']
        request_url = request.to_url()
        response = urllib2.urlopen(request_url)
        token = oauth.OAuthToken.from_string(response.read())
        user = User(username)
        user.note = "request_token:%s" % token.to_string()
        store.put(user)
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
                token=token, http_url=twitter.authorization_url)
        raise HTTP302(oauth_request.to_url())

def _callback_url(environ):
    return server_base_url(environ) + '/tweetbag'


@do_html()
@entitle("Get your tweets Yo")
@require_any_user()
def send(environ, start_response):
    query = environ['tiddlyweb.query']
    store = environ['tiddlyweb.store']
    user = User(environ['tiddlyweb.usersign']['name'])
    user = store.get(user)
    notes = user.note.splitlines()
    user_tokens = {}
    for note in notes:
        key, value = note.split(':', 1)
        user_tokens[key] = value
    consumer = oauth.OAuthConsumer(twitter.CONSUMER_KEY,
            twitter.CONSUMER_SECRET)
    if query.get('oauth_token'):
        request_token = oauth.OAuthToken.from_string(
                user_tokens['request_token'])
        query_oauth_token = environ['tiddlyweb.query']['oauth_token'][0]
        query_oauth_verifier = environ['tiddlyweb.query']['oauth_verifier'][0]
        assert query_oauth_token == request_token.key
        request = oauth.OAuthRequest.from_consumer_and_token(
                consumer,
                token=request_token,
                verifier=query_oauth_verifier,
                http_url=twitter.access_token_url)
        request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(),
                consumer,
                request_token)
        request_url = request.to_url()
        response = urllib2.urlopen(request_url)
        token = oauth.OAuthToken.from_string(response.read())
        user_tokens['access_token'] = '%s' % token.to_string()
        note = []
        for key in user_tokens:
            note.append('%s:%s' % (key, user_tokens[key]))
        user.note = '\n'.join(note)
        store.put(user)
        raise HTTP302(_callback_url(environ))
    elif 'access_token' in user_tokens:
        access_token = oauth.OAuthToken.from_string(
                user_tokens['access_token'])
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
