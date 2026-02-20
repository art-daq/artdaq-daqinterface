import zmq
import InhibitManager

context = zmq.Context()
subscriber = InhibitManager.InhibitSUBNode(context)
subscriber.connect("tcp://localhost:5566")

while True:
    msg = subscriber.recv_status_msg_timeout()
    print(msg)
