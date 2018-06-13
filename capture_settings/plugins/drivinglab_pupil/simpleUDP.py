
import sys
import socket as s
import time

#setup receive socket
PORT1 = 5000
SIZE = 1024
host = s.gethostbyname('0.0.0.0')

eyetrikesock = s.socket( s.AF_INET, s.SOCK_DGRAM )
#sock.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR,1)
et_addr = (host,PORT1)
eyetrikesock.bind(et_addr)

time.sleep(.5)

#setup send socket
PORT2 = 5002
TARGET_IP = '192.168.0.5'
venlabsock = s.socket(s.AF_INET, s.SOCK_DGRAM)
vl_addr = (TARGET_IP,PORT2)


while True:

	data, addr = eyetrikesock.recvfrom(SIZE)
	print ("received:", data.decode('utf-8'))

	if data: 
		sent = venlabsock.sendto('hi back'.encode('utf-8'),(TARGET_IP,PORT2))
		print ('sent',sent)
		break
		


print ("finished...")
sys.exit()

