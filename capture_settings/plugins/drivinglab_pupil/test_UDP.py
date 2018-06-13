import socket as s

#send settings
PORT = 5000		
SIZE = 1024
address  = 'localhost' 

eyetrikesock = s.socket( s.AF_INET, s.SOCK_DGRAM )
et_addr = (address, PORT)


while True:
    msg = input("Type a command ")
    eyetrikesock.sendto(msg.encode('utf-8'), et_addr)