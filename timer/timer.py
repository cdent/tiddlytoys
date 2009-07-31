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

    starts = [int(tiddler.title) for tiddler in start_tiddlers]
    stops = [int(tiddler.title) for tiddler in stop_tiddlers]

    total_time = count_times(starts, stops)

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


def zip_to_type(starts, stops):
    tuples = []
    for start in starts:
        tuples.append(('start', start))
    for stop in stops:
        tuples.append(('stop', stop))

    def key_gen(tuple):
        return tuple[1]

    tuples = sorted(tuples, key=key_gen)

    return tuples


def flush_until_different(type, tuples):
    removals = []
    for tuple in tuples:
        if tuple[0] == type:
            removals.append(tuple)
        else:
            break
    return removals


def de_gap(type, tuples):
    index = 0
    removals = []

    for tuple in tuples:
        if tuple[0] == type:
            removals.extend(flush_until_different(type, tuples[index + 1:]))
        index += 1

    for removeme in removals:
        try:
            tuples.remove(removeme)
        except ValueError:
            pass
    return tuples


def totaller(tuples):
    total = 0
    while 1:
        try:
            try:
                start = tuples.pop(0)[1]
            except IndexError:
                raise
            try:
                stop = tuples.pop(0)[1]
            except IndexError:
                stop = time()
        except IndexError:
            return total
        total += (stop - start)


def count_times(starts, stops):
    return totaller(
        de_gap('stop',
            de_gap('start',
                zip_to_type(starts, stops))))
