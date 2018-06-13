#cdm adapted put.py to stream clock_monotonic continuously to venlab. uses python3. 
import sys
import time
from uvc import get_time_monotonic
import socket as s

#setup venlab socket
TARGET_IP   = '192.168.0.1'
PORT_NUMBER = 5000
SIZE = 1024
host = s.gethostbyname('0.0.0.0')

sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
sock.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR,1)
sock.bind((host,PORT_NUMBER))

#setup pupil remote
#import zmq, msgpack
#ctx = zmq.Context()

#create a zmq REQ socket to talk to Pupil Service/Capture
#req = ctx.socket(zmq.REQ)
#req.connect('tcp://localhost:50020')

#convenience functions
#def get_pupil_timestamp():#
#	req.send_string('t') #see Pupil Remote plugin for details
#	return float(req.recv())
	

#i = 0
#hz = 120 #number of times a second
#freq = 1/hz
#STREAM data. CTRL+C to interrupt.
while True:
	#time.sleep(freq) #stream at 120hz
#	monoTime = time.clock_gettime(time.CLOCK_MONOTONIC) #same as that used in pupil.
		
	#monoTime = get_time_monotonic() #this is pretty identical to pupil-labs time-stamp, just  little quicker.
	#print (monoTime)	#check with pupil-labs comms.
		#convert monoTime to sendable bytes.
	#newTime = str(monoTime).encode('utf-8')
		#send across
	#venlabSocket.sendto(newTime,(TARGET_IP,PORT_NUMBER))
#		venlabSocket.send(newTime)
	#print ('newtime:',newTime.decode('utf-8'))

	#pupil_time = get_pupil_timestamp()
	#print ('pupiltime:',pupil_time)

	data, addr = sock.recvfrom(SIZE)
	print ("received:", data)

	if data: 
	 	sent = sock.sendto(data,addr)
		



print ("finished...")
sys.exit()

