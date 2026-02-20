from __future__ import print_function
from rc.util.exc_string import exc_string
import contextlib
import datetime
import inspect
import os
import os.path
import pprint
import sys
import time


def eq(x, y, pretty=False):
    if x != y and pretty:  # no-coverage
        pprint.PrettyPrinter().pprint((x, y))
    assert x == y, "%s %s != %s %s!" % (type(x).__name__, x, type(y).__name__, y)


def gt(x, y):
    assert x > y, "%s <= %s !" % (x, y)


def isin(x, l):
    assert x in l, '"%s" is not in "%s"!' % (x, l)


def isnotin(x, l):
    assert x not in l, '"%s" is in "%s"!' % (x, l)


class NotDoneException(Exception):
    pass


def wait_until(done, interval=0.01, trace=False, timeout=1.0):
    maxtries = max(1, int(timeout / float(interval)))
    for _ in range(maxtries):
        if trace:  # no-coverage
            print("Checking: ", inspect.getsource(done))
        x = done()
        if x:
            if trace:  # no-coverage
                print("Result: ", x)
            return x
        time.sleep(interval)

    raise NotDoneException(  # no-coverage
        "The following function never returned True:\n%s" % inspect.getsource(done)
    )


def remove_if_exists(f):
    if os.path.exists(f):
        os.unlink(f)


@contextlib.contextmanager
def file_cleanup(f):
    try:
        yield
    finally:
        remove_if_exists(f)


def andn(*l):
    return reduce(lambda a, b: a and b, l, True)


def orn(*l):
    return reduce(lambda a, b: a or b, l, True)


def wait_forever():  # no-coverage
    while True:
        time.sleep(100)


def wait_for_interrupt():  # no-coverage
    try:
        wait_forever()
    except KeyboardInterrupt:
        return


def raises(e, f, *args, **kwargs):
    fail = False
    try:
        f(*args, **kwargs)
        fail = True  # no-coverage
    except e:
        return
    if fail:  # no-coverage
        raise Exception("Expected exception '%s', which was not raised." % e)


def is_mac():
    """
    Handle wimpy max open files on Mac (multi-thread tests)
    """
    return "darwin" in sys.platform


def convert_to_time(t):
    if t is None or type(t) is datetime.datetime:
        return None
    try:
        rt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S.%f")
        return rt
    except ValueError:
        rt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        return rt


def complement(f):
    def inner(*args, **kwargs):
        return not f(*args, **kwargs)

    return inner


def stringify_times(d):
    if type(d) is datetime.datetime:
        return str(d)
    if type(d) is dict:
        return dict((k, stringify_times(v)) for (k, v) in d.items())
    elif type(d) is list:
        return map(stringify_times, d)
    elif type(d) is tuple:
        return tuple(map(stringify_times, d))
    else:
        return d


def print_on_exc(f):  # no-coverage
    """
    Use this decorator when running the test server to print out
    exceptions as they occur
    """

    def new(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            print(exc_string())

    return new


def setup_django_env():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rc.web.main.settings")
