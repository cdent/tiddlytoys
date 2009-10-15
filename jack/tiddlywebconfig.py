from whoosh.fields import Schema, ID, KEYWORD, TEXT

config = {
        'LOG_LEVEL': 'DEBUG',
        'system_plugins': ['whoosher', 'jack', 'tiddlywebwiki', 'formreader','static'],
        'twanager_plugins': ['whoosher', 'tiddlywebwiki'],
        'server_store': ['sql', {'db_config': 'sqlite:///store.db'}],
        'instance_tiddlers': [
            ('bag0', ['http://svn.tiddlywiki.org/Trunk/contributors/JeremyRuston/verticals/cecily/index.html.recipe']),
            ],
        'css_uri': 'http://peermore.com/tiddlyweb.css',
        'wsearch.schema': {'title': TEXT,
            'id': ID(stored=True, unique=True),
            'bag': TEXT,
            'text': TEXT,
            'modified': ID,
            'modifier': ID,
            'created': ID,
            'tags': KEYWORD,
            'price': TEXT,
            'address': TEXT,
            },
        'wsearch.default_fields': [
            'title',
            'text',
            'price',
            'address',
            ],
        }
