"""
A twanager command for recording some time tracking
information via Tiddlers.
"""

config = {
        'twanager_plugins': ['timer'],
        }

from time import time

from tiddlyweb import control
from tiddlywebplugins import ensure_bag, get_store
from tiddlyweb.manage import make_command

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import NoBagError

@make_command()
def starttime(args):
    """Record start time in a bag: <bag>"""
    store = get_store(global_config)
    bag_name ='%s-start' % args[0]
    bag = ensure_bag(bag_name, store)
    tiddler = Tiddler(int(time()), bag_name)
    try:
        tiddler.text = args[1]
    except IndexError:
        pass
    store.put(tiddler)


@make_command()
def stoptime(args):
    """Record stop time in a bag: <bag>"""
    print args
    store = get_store(global_config)
    bag_name ='%s-stop' % args[0]
    bag = ensure_bag(bag_name, store)
    tiddler = Tiddler(int(time()), bag_name)
    try:
        tiddler.text = args[1]
    except IndexError:
        pass
    store.put(tiddler)

@make_command()
def reporttime(args):
    """Report total time from bag: <bag>"""
    store = get_store(global_config)
    start_bag_name = '%s-start' % args[0]
    stop_bag_name = '%s-stop' % args[0]
    try:
        start_bag = store.get(Bag(start_bag_name))
        start_tiddlers = control.filter_tiddlers_from_bag(start_bag, 'sort=title')
    except NoBagError:
        start_tiddlers = []
    try:
        stop_bag = store.get(Bag(stop_bag_name))
        stop_tiddlers = control.filter_tiddlers_from_bag(stop_bag, 'sort=title')
    except NoBagError:
        stop_tiddlers = []
    total_time = 0

    def _clean(list_a, list_b):
        new_a = []
        new_b = []
        for index, tiddler in enumerate(list_a):
            try:
                mate = list_b[index]
            except IndexError:
                new_a.append(tiddler)
                return new_a, new_b
            try:
                successor = list_a[index + 1]
            except IndexError:
                new_a.append(tiddler)
                new_b.append(mate)
                return new_a, new_b
            if int(successor.title) < int(mate.title):
                del list_a[index + 1]
            new_a.append(tiddler)
            new_b.append(mate)
        return new_a, new_b

    starts, stops = _clean(start_tiddlers, stop_tiddlers)

    for index, tiddler in enumerate(starts):
        start = int(tiddler.title)
        try:
            next_stop_tiddler = stops[index]
            next_stop = int(next_stop_tiddler.title)
        except IndexError:
            next_stop = int(time())
            gap = next_stop - start
            total_time += gap
            break

        gap = next_stop - start
        if gap < 0:
            print 'skipping a bad gap'
        else:
            total_time += gap

    print 'Total time: %s' % (float(total_time)/(60*60))


def init(config_in):
    global global_config
    global_config = config_in

def run_tests():
    store = get_store(global_config)
    start_bag = ensure_bag('test1-start', store)
    stop_bag = ensure_bag('test1-stop', store)
    store.put(Tiddler('1', 'test1-start'))
    store.put(Tiddler('2', 'test1-stop'))
    store.put(Tiddler('3', 'test1-start'))
    store.put(Tiddler('4', 'test1-stop'))
    reporttime(['test1']) # 2

    start_bag = ensure_bag('test2-start', store)
    stop_bag = ensure_bag('test2-stop', store)
    store.put(Tiddler('1', 'test2-start'))
    store.put(Tiddler('2', 'test2-start'))
    store.put(Tiddler('5', 'test2-stop'))
    reporttime(['test2']) # 4

    start_bag = ensure_bag('test3-start', store)
    stop_bag = ensure_bag('test3-stop', store)
    store.put(Tiddler('1', 'test3-start'))
    store.put(Tiddler('2', 'test3-stop'))
    store.put(Tiddler('5', 'test3-stop'))
    reporttime(['test3']) # 1




if __name__ == '__main__':
    from tiddlyweb.config import config as global_config
    run_tests()
