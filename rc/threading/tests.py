raise Exception("JCF, Sep-6-2017: At least for the time being, this file is deprecated")

import sys

sys.path.append("/home/nfs/dunedaq/jcfree/standalone_daq")

from rc.util import eq, wait_until
from rc.threading import Threadable, threadable
import threading
import time


def test_thread_start_stop():
    t = Threadable()
    t.start()
    eq(threading.active_count(), 2)
    t.stop()


def test_multiple_starts():
    [test_thread_start_stop() for _ in range(10)]


def test_simultaneous_threads():
    num_threads = 4
    threads = [Threadable() for _ in range(num_threads)]
    [t.start() for t in threads]
    eq(threading.active_count(), num_threads + 1)
    [t.stop() for t in threads]


def test_thread_context_manager():
    with threadable():
        eq(threading.active_count(), 2)


def test_thread_function_executes():
    i = [0]

    def increment():
        i[0] += 1

    with threadable(func=increment, period=0.001):
        wait_until(lambda: i[0] > 10)


def test_long_thread_periods_can_be_interrupted():
    acc = [0]

    def increment():
        acc[0] += 1

    t0 = time.time()

    with threadable(func=increment, period=100) as t:

        def done(i):
            if acc[0] > i:
                return True
            t.wakeup()

        for i in range(10):
            wait_until(lambda: done(i))

    assert time.time() - t0 < 3
