
from tiddlywebplugins.instancer.util import get_tiddler_locations

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
        "system_plugins": ["tiddlywebplugins.hoster"],
        }

instance_tiddlers = get_tiddler_locations(store_contents, 'tiddlywebplugins.hoster')
