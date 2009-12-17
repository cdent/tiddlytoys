
from tiddlywebplugins.instancer.util import get_tiddler_locations
from tiddlywebwiki.instance import (
        store_contents as tww_store_contents,
        store_structure as tww_store_structure)
from tiddlywebwiki.config import config

store_contents = {
        'hoster': [
            'file:basecontent/main.css.tid',
            ]
        }

store_structure = {
        'bags': {
            'hoster': {
                'desc': 'useful stuff that hoster wants to use',
                'policy': {
                    'read': '',
                    'write': 'R:ADMIN',
                    'create': 'R:ADMIN',
                    'delete': 'R:ADMIN',
                    'manage': 'R:ADMIN',
                    'owner': 'administrator',
                    }
                },
            },
        }

instance_config = {
        'system_plugins': ['tiddlywebplugins.hoster'],
        'auth_systems': ['openid'],
        'css_uri': '/bags/hoster/tiddlers/main.css',
        'register.start_href': '/home',
        }

instance_tiddlers = get_tiddler_locations(store_contents, 'tiddlywebplugins.hoster')
store_contents.update(tww_store_contents)
store_structure.update(tww_store_structure)
instance_tiddlers.update(config['instance_tiddlers'])

