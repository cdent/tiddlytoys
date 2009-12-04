"""
Data structures used for creating a new instance of
simplewiki.
"""
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

try:
    from pkg_resources import resource_filename
    front_page = resource_filename('tiddlywebplugins.simplewiki', 'FrontPage.tid')
    print 'got front page as resource at ', front_page
except (ImportError):
    front_page = os.path.join('tiddlywebplugins', 'simplewiki', 'FrontPage.tid')
    print 'got front page as local at ', front_page

instance_tiddlers = [("wiki", [front_page])]
