import zmq
import InhibitManager

context = zmq.Context()
publisher = InhibitManager.InhibitPUBNode(context, "tcp://*:5566")

subscriber = InhibitManager.StatusSUBNode(context)
subscriber.connect("tcp://localhost:5556")
subscriber.connect("tcp://localhost:5557")

im = InhibitManager.InhibitManager(0.5, False)

im.run(subscriber, publisher)
