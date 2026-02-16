import Queue
import contextlib
from rc.threading import threadable
from rc.io import sender, receiver, threaded_receiver, queueing_receiver
from rc.io.rpc import rpc_server, rpc_client
from rc.util import wait_until, eq, raises, is_mac


def test_simple_connection():
    with receiver() as r:
        with sender() as s:
            s.send("1")
            wait_until(lambda: r.recv_nonblock() == "1")


def test_raw_sender():
    with receiver() as r:
        with sender() as s:
            s.sendraw("[1, 2, 3]")

            def done():
                recvd = r.recv_nonblock()
                if recvd == [1, 2, 3]:
                    return True

            wait_until(done)


def test_exception_in_context():

    def should_fail():
        with sender():
            1 / 0

    raises(ZeroDivisionError, should_fail)


def test_threaded_connection():
    wanted = '"some json"'
    recvd = [None]

    with receiver() as r:
        with sender() as s:
            s.send(wanted)

            def get_messages():
                msg = r.recv_nonblock()
                if msg:
                    recvd[0] = msg

            with threadable(func=get_messages) as t:

                def done():
                    if recvd[0] == wanted:
                        return True
                    t.wakeup()

                wait_until(done)


def test_threaded_receiver_context_manager():
    msglist = []

    def handle_message(m):
        msglist.append(m)

    with threaded_receiver(func=handle_message) as (r, t):
        with sender() as s:
            s.send("1")

            def done():
                t.wakeup()
                return msglist

            wait_until(done)


def test_queuing_receiver_context_manager():
    with queueing_receiver(targs={"period": 0.01}) as (q, t):
        with sender() as s:
            s.send("1")

            def done():
                t.wakeup()
                try:
                    data = q.get(timeout=0.01)
                    assert data == "1"
                    return True
                except Queue.Empty:
                    return False

            wait_until(done, timeout=3)


def test_multi_message_queue():
    with queueing_receiver(targs={"period": 0.001}) as (q, t):
        N = 1000
        with sender() as s:
            for i in range(N):
                s.send(str(i))
        got = []

        def done():
            while True:
                try:
                    data = q.get(timeout=0.01)
                    got.append(data)
                except Queue.Empty:
                    if len(got) < N:
                        return False
                    return [str(i) for i in range(N)] == got

        wait_until(done)


def test_create_lots_of_threads_and_each_send_a_message():
    N = 4 if is_mac() else 40
    with queueing_receiver() as (q, t):
        with contextlib.nested(*[sender() for _ in range(N)]) as senders:
            for i, s in enumerate(senders):
                s.send(str(i))

            got = []

            def done():
                t.wakeup()
                try:
                    data = q.get(timeout=0.01)
                    got.append(data)
                except Queue.Empty:
                    return len(got) == N

            wait_until(done)


def test_rpc():
    called = [False]

    def set_called():
        called[0] = True

    with rpc_server(funcs={"setcalled": set_called}):
        with rpc_client() as c:
            c.setcalled()
            eq(called, [True])
