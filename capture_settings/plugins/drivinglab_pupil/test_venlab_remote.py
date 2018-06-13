#Authors: callum mole and yuki okafuji. 
#Purpose: interface between venlab comp and pupil_remote. 
import sys, time
from uvc import get_time_monotonic
import socket as s

#setup pupil remote
import zmq, msgpack
ctx = zmq.Context()

#create a zmq REQ socket to talk to Pupil Service/Capture
req = ctx.socket(zmq.REQ)
#req.connect('tcp://localhost:44749') #needs to match pupil-remote settings on pupil-labs
req.connect('tcp://localhost:50020') #needs to match pupil-remote settings on pupil-labs


#wait for orders and relay to pupil capture
acceptedcommands = ['R','r','C','c','T','t']


# msg = 'C'
# req.send_string(msg) #send through to pupil_remote
# recv = req.recv_string() #get bounce-back
# print (recv)


# notification = {'subject':'annotation','label':label,'timestamp':float(recvtime),'duration':5.0,'source':'eyetrike','record':True}
# topic = 'notify.'+ notification['subject']
# payload = msgpack.dumps(notification)
# req.send_string(topic,flags=zmq.SNDMORE)
# req.send(payload)
# recv = req.recv_string()

			
notification = {'subject': 'accuracy_test.should_start'}
topic = 'notify.' + notification['subject']

payload = msgpack.dumps(notification)

req.send_string(topic, flags = zmq.SNDMORE)
req.send(payload)
recv = req.recv_string()

print(recv)


time.sleep(10)


notification = {'subject': 'accuracy_test.should_stop'}
topic = 'notify.' + notification['subject']

payload = msgpack.dumps(notification)

req.send_string(topic, flags = zmq.SNDMORE)
req.send(payload)
recv = req.recv_string()

print(recv)