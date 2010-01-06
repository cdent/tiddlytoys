"""
A twanager command for doing simple weight recording
management via Tiddlers.
"""

from uuid import uuid4 as uuid

from tiddlywebplugins.utils import ensure_bag, get_store
from tiddlyweb.manage import make_command

from tiddlyweb.model.tiddler import Tiddler

@make_command()
def weight(args):
    """Record a daily weight."""
    store = get_store(global_config)
    bag_name = 'weight'
    bag = ensure_bag(bag_name, store)
    title = str(uuid())
    tiddler = Tiddler(title, bag_name)
    tiddler.fields['weight'] = args[0]
    store.put(tiddler)

def init(config_in):
    global global_config
    global_config = config_in
