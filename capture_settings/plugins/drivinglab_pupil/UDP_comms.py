import socket as s
import multiprocessing as mp
import time


class pupil_comms:

    def __init__(self, send_IP = '192.168.0.2', send_PORT = 5000, recv_IP = '192.168.0.1', recv_PORT = 5015, SIZE = 1024):
        """args:
            send_IP: IP of machine you are sending requests to (Eyetrike)
            recv_IP: IP of machine running this code
        """

        self.send_IP = send_IP
        self.send_PORT = send_PORT

        self.recv_IP = recv_IP
        self.recv_PORT = recv_PORT

        self.SIZE = SIZE

        self.start_send_socket()
        self.start_recv_socket()

        self.send_msg("test")
        time.sleep(.25)
        print (self.poll_msg())


    def start_send_socket(self):

        self.send_sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
        self.send_addr = (self.send_IP, self.send_PORT)

    def start_recv_socket(self):

        self.recv_sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
        self.recv_sock.bind((self.recv_IP, self.recv_PORT))

        self.recv_sock.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR,1)

        self.parent_conn, self.child_conn = mp.Pipe(False)
        self.recv_process = mp.Process(target = message_receiver, args = (self.recv_sock, self.child_conn, self.SIZE))
        self.recv_process.daemon = True

        self.recv_process.start()
        
    def send_msg(self, msg):

        self.send_sock.sendto(msg.encode(), self.send_addr)

    def send_message_from_console(self):
        """Type messages over the console. 
        Enter q to close"""

        while True:
            msg = input("Type a command ")
           
            if msg == 'q':

                return
            self.send_msg(msg)

    def poll_msg(self):
        """See if any messages have appeared in the message thread"""

    
        all_messages = []

        while self.parent_conn.poll():
       
            all_messages.append(self.parent_conn.recv())

           
       # print(all_messages)

        return all_messages

        

  

def message_receiver(recv_socket, output_pipe, SIZE = 1024):

    """Recieve messages from a socket and flush the messages to a pipe"""

    while True:
        data, addr = recv_socket.recvfrom(SIZE)

        if data: 
            #decode message
            msg = data.decode('utf-8')

            output_pipe.send(msg)
		



if __name__ == '__main__':

    comms = pupil_comms()

    comms.send_message_from_console()


    print (comms.poll_msg())

    # comms.send_message_from_console()
    