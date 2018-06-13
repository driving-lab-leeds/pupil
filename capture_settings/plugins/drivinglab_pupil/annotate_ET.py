#cdm adapted put_ET to push annotations onto pupil-lab
#pupil capture needs to be running and calibrated.
import sys, time
from uvc import get_time_monotonic
from socket import socket, AF_INET, SOCK_DGRAM

#setup pupil remote
import zmq, msgpack
ctx = zmq.Context()

#create a zmq REQ socket to talk to Pupil Service/Capture
req = ctx.socket(zmq.REQ)
req.connect('tcp://localhost:50020')


	
##annotation
tn = 3 #number of trials
gap = 3 #number of seconds between each annotation
#STREAM data. CTRL+C to interrupt.
for i in range(1,tn+1):

	t = get_time_monotonic()
	#start recording
	label = "trial" + str(i)
	print (label,'_start: ',str(t))

	t1 = get_time_monotonic()
	req.send_string('R annotations4')
	#req.send_string('start_record')
	print ('start_record')
	print (req.recv_string())
	t2 = get_time_monotonic()
	print ('startlag:',t2-t1)
	
	label = "trial" + str(i)
	print (label,'_start: ',str(t))
	
	#fetch time
	req.send_string('t') #send through to pupil_remote
	recvtime = req.recv_string() #get bounce-back
	print (recvtime)
				
	notification = {'subject':'annotation','label':label,'timestamp':float(recvtime), 'duration':1.0,'source':'eyetrike','record':True}
	topic = 'notify.'+ notification['subject']
	payload = msgpack.dumps(notification)
	req.send_string(topic,flags=zmq.SNDMORE)
	req.send(payload)
	print( req.recv_string())
	
	time.sleep(gap) #trial length. in reality this will be triggered on msg.receive.	
#stop recording
	t3 = get_time_monotonic()
	req.send_string('r')
	print ('finish_record')
	print (req.recv_string())
	t4 = get_time_monotonic()
	print ('stoplag:',t4-t3)
	


print ("finished...")
sys.exit()

