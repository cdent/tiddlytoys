"""
A combination of serializer and some static
content to make a simple client side editor
for Markdown syntax tiddlers.
"""

from tiddlyweb.serializations.html import Serialization as HTML
from tiddlyweb.web.wsgi import HTMLPresenter


MD_SERIALIZERS = {
        'text/html': ['mdedit', 'text/html; charset=UTF-8']
        }


def init(config):
    config['serializers'].update(MD_SERIALIZERS)


class Serialization(HTML):

    def tiddler_as(self, tiddler):
        links = []
        for javascript in self.environ['tiddlyweb.config'].get(
                'mdedit.javascripts', []):
            links.append('<script type="text/javascript" src="%s"></script>'
                    % javascript)
        for css in self.environ['tiddlyweb.config'].get('mdedit.css', []):
            links.append('<link rel="stylesheet" type="text/css" href="%s" />'
                    % css)

        self.environ['tiddlyweb.links'] = links
        return HTML.tiddler_as(self, tiddler)
