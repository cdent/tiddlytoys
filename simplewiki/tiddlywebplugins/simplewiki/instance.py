"""
Data structures used for creating a new instance of
simplewiki.
"""

from tiddlywebplugins.instancer.util import get_tiddler_locations

store_contents = {
        'wiki': [
            'file:basecontent/FrontPage.tid',
            ]
        }

store_structure = {
        "bags": {
                "wiki": {
                        "desc": "simplewiki contents",
                        # Use default open policy. This is old skool
                        # wiki.
                },
        },
        "recipes": {
                "wiki": {
                        "desc": "simplewiki",
                        "recipe": [
                                ("wiki", "")
                        ],
                }
        }
}


instance_config = {
        "system_plugins": ["tiddlywebplugins.simplewiki"],
        }

instance_tiddlers = get_tiddler_locations(store_contents, 'tiddlywebplugins.simplewiki')
