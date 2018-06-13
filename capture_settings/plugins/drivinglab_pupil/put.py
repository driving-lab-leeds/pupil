#author = yuki okafuji.
#created = oct 2017

import sys
import time
from socket import socket, AF_INET, SOCK_DGRAM

TARGET_IP   = '192.168.0.1'
PORT_NUMBER = 5000
SIZE = 1024

mySocket = socket( AF_INET, SOCK_DGRAM )
i = 0

for i in range(1,11):
    time.sleep(0.3)
    print (str(i))    	
    mySocket.sendto(str(i).encode('utf-8'),(TARGET_IP,PORT_NUMBER))

    data, server = mySocket.recvfrom(SIZE)
    print ('received:',data)

print ("finished...")
sys.exit()

