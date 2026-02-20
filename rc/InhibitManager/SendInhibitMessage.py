import zmq
import InhibitManager
import sys, time
import getpass

context = zmq.Context()
publisher = InhibitManager.StatusPUBNode(context, "tcp://*:5556")

time.sleep(0.5)
# while(True):
#    msg = raw_input("Enter MSG to send:")
#    publisher.send_status_msg("CommandLineMessage",getpass.getuser(),msg)
#    print "\n"
# msg = raw_input("Enter MSG to send:")
publisher.send_status_msg("CommandLineMessage", getpass.getuser(), sys.argv[1])
# time.sleep(2)
# print "\n"
