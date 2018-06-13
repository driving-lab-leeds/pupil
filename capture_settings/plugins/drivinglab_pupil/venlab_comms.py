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

#setup receive socket
PORT1 = 5000
SIZE = 1024
host = s.gethostbyname('0.0.0.0')

eyetrikesock = s.socket( s.AF_INET, s.SOCK_DGRAM )
#sock.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR,1)
et_addr = (host,PORT1)
eyetrikesock.bind(et_addr)

#setup send socket
PORT2 = 5015 #needs to match venlab
TARGET_IP = '192.168.0.5'
venlabsock = s.socket(s.AF_INET, s.SOCK_DGRAM)
vl_addr = (TARGET_IP,PORT2)

#wait for orders and relay to pupil capture
acceptedcommands = ['R','r','C','c','T','t']


while True:
	data, addr = eyetrikesock.recvfrom(SIZE)

	if data: 
		#decode message
		msg = data.decode('utf-8')
		print ("received:", msg)
		
		if msg[0] in acceptedcommands:
			
			req.send_string(msg) #send through to pupil_remote
			recv = req.recv_string() #get bounce-back
			print (recv)
			venlabsock.sendto(recv.encode('utf-8'),vl_addr) #send result to venlab
				
		elif msg[0] == 'p':
			venlabsock.sendto('receiving...'.encode('utf-8'),vl_addr)
		
		elif msg[0] == 'A':
			##annotation
			label = msg[1:] #grab trialtype
			print (label)

			#fetch time
			req.send_string('t') #send through to pupil_remote
			recvtime = req.recv_string() #get bounce-back

			notification = {'subject':'annotation','label':label,'timestamp':float(recvtime),'duration':5.0,'source':'eyetrike','record':True}
			topic = 'notify.'+ notification['subject']
			payload = msgpack.dumps(notification)
			req.send_string(topic,flags=zmq.SNDMORE)
			req.send(payload)
			recv = req.recv_string()
			venlabsock.sendto(recv.encode('utf-8'),vl_addr) #send result to venlab


