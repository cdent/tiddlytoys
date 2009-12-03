"""
A twanager command for doing simple to do item 
management via Tiddlers.
"""

from tiddlywebplugins.utils import ensure_bag, get_store
from tiddlyweb.manage import make_command
from tiddlyweb import control

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler

@make_command()
def do(args):
    """Establish a to do item."""
    store = get_store(global_config)
    bag_name = 'do'
    bag = ensure_bag(bag_name, store)
    title = ' '.join(args)
    tiddler = Tiddler(title, bag_name)
    store.put(tiddler)


@make_command()
def done(args):
    """Move a to do item to the done bag."""
    store = get_store(global_config)
    do_bag_name = 'do'
    done_bag_name ='done'
    bag = ensure_bag(done_bag_name, store)
    title = ' '.join(args)
    tiddler = Tiddler(title, do_bag_name)
    tiddler = store.get(tiddler)
    store.delete(tiddler)
    tiddler.bag = done_bag_name
    store.put(tiddler)

@make_command()
def todos(args):
    """List the todos."""
    store = get_store(global_config)
    bag = Bag('do')
    bag = store.get(bag)
    titles = [(tiddler.modified, tiddler.title) for tiddler in
            control.filter_tiddlers_from_bag(bag, 'sort=modified')]
    print '\n'.join(['%s: %s' % title for title in titles])

def init(config_in):
    global global_config
    global_config = config_in
