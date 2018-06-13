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

msg = 'C'
req.send_string(msg) #send through to pupil_remote
recv = req.recv_string() #get bounce-back
print (recv)
			