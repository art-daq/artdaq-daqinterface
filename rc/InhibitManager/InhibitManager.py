import sys
import zmq
import thismoduledoesnotexist
import datetime, time

STATUS_MSG_MARKER = "STATUSMSG"
if isinstance(STATUS_MSG_MARKER, bytes):
    STATUS_MSG_MARKER = STATUS_MSG_MARKER.decode("ascii")

INHIBIT_MSG_MARKER = "INHIBITMSG"
if isinstance(INHIBIT_MSG_MARKER, bytes):
    INHIBIT_MSG_MARKER = INHIBIT_MSG_MARKER.decode("ascii")


class StatusMsg:
    def __init__(self, msg):
        self.raw_msg = str(msg)
        self.msg_list = msg.split("_")
        if len(self.msg_list) != 5:
            print("MESSAGE is malformed! raw_msg=%s\n" % self.raw_msg)
            self.msg_ok = False
        else:
            self.msg_ok = True

    def raw_msg(self):
        s = "%s" % (self.raw_msg)
        return s

    def type(self):
        return self.msg_list[0]

    def process(self):
        return self.msg_list[1]

    def marker(self):
        return self.msg_list[2]

    def status(self):
        return self.msg_list[3]

    def time(self):
        return self.msg_list[4]


def CreateStatusMsg(process, marker, status):
    return "%s_%s_%s_%s_%s" % (
        STATUS_MSG_MARKER,
        str(process),
        str(marker),
        str(status),
        datetime.datetime.now(),
    )


class StatusSUBNode:
    def __init__(self, zmq_context):
        self.socket = zmq_context.socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, STATUS_MSG_MARKER)

    def connect(self, address):
        self.socket.connect(str(address))

    def recv_status_msg_timeout(self, timeout=0.5):  # timeout in seconds
        timeinit = datetime.datetime.now()
        timenow = timeinit
        diff = timenow - timeinit
        while diff.total_seconds() < timeout:
            try:
                msg = self.socket.recv_string(flags=zmq.NOBLOCK)
                return msg
            except zmq.ZMQError:
                timenow = datetime.datetime.now()
                diff = timenow - timeinit
        return "TIMEOUT"


class StatusPUBNode:
    def __init__(self, zmq_context, address):
        self.socket = zmq_context.socket(zmq.PUB)
        self.socket.bind(address)

    def send_status_msg(self, process, marker, status):
        msg = CreateStatusMsg(process, marker, status)
        self.socket.send_string(msg)


class InhibitPUBNode:
    def __init__(self, zmq_context, address):
        self.socket = zmq_context.socket(zmq.PUB)
        self.socket.bind(address)

    def send_inhibit_msg(self, msg, details):
        self.socket.send_string(
            "%s_%s_%s (%s)"
            % (INHIBIT_MSG_MARKER, str(msg), datetime.datetime.now(), str(details))
        )


class InhibitSUBNode:
    def __init__(self, zmq_context):
        self.socket = zmq_context.socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, INHIBIT_MSG_MARKER)

    def connect(self, address):
        self.socket.connect(str(address))

    def recv_status_msg_timeout(self, timeout=5.0):  # timeout in seconds
        timeinit = datetime.datetime.now()
        timenow = timeinit
        diff = timenow - timeinit
        while diff.total_seconds() < timeout:
            try:
                msg = self.socket.recv_string(flags=zmq.NOBLOCK)
                return msg
            except zmq.ZMQError:
                timenow = datetime.datetime.now()
                diff = timenow - timeinit
        return "TIMEOUT"


class InhibitManager:

    def __init__(self, update_freq=1.0, verbose=False):  # timeout in seconds
        self.frontend_dict = {"INHIBITMANAGER": "OK"}
        self.current_status = "XON"
        self.update_freq = update_freq
        self.verbose = verbose

    def print_status():
        print("Current Status = %s" % self.current_status)
        for fe in self.frontend_dict:
            print("\t%s : %s" % (fe, frontend_dict[fe]))

    def status(self):
        return self.current_status

    def update_status(self):
        tmp_status = "XON"
        for stat in self.frontend_dict.values():
            if stat != "OK":
                tmp_status = "XOFF"
                break
        self.current_status = tmp_status

    def register_status_msg(self, msg):
        self.frontend_dict[msg.process()] = msg.status()
        if msg.status() != self.status():
            self.update_status()

    def run(self, subscriber, publisher):
        timelast = datetime.datetime.now()
        while True:
            init_status = self.status()
            msg = subscriber.recv_status_msg_timeout(self.update_freq)
            if self.verbose:
                print("Msg received: %s" % msg)
            if msg != "TIMEOUT":
                self.register_status_msg(StatusMsg(msg))
                if self.status() != init_status:
                    publisher.send_inhibit_msg(self.status(), "global status change")
            timenow = datetime.datetime.now()
            diff = timenow - timelast
            if diff.total_seconds() > self.update_freq:
                publisher.send_inhibit_msg(self.status(), "no change")
                timelast = timenow
