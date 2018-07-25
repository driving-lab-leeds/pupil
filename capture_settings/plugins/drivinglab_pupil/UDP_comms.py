import socket as s
import threading 
import Queue
import time


class pupil_comms:

    def __init__(self, send_IP = '192.168.0.2', send_PORT = 5000, recv_IP = '192.168.0.1', recv_PORT = 5020, SIZE = 1024):
        """
        When you create an instance it will set up all the connections and send a test signal to the Eyetrike machine.
        

        To check the connection is live call self.send_msg("test"). Then sleep for half a second or so. Then call self.poll_msg(). This should return 'comms.online'
        
        
        args:
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
        
    def start_send_socket(self):

        self.send_sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
        self.send_addr = (self.send_IP, self.send_PORT)

    def start_recv_socket(self):

        self.output_queue = Queue.Queue()

        self.recv_process = threading.Thread(target = message_receiver, args = (self.recv_IP, self.recv_PORT, self.output_queue, self.SIZE))
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

                self.close_comms()

                return

            elif msg == 'poll':

                messages = self.poll_msg()

                print(messages)
                
            self.send_msg(msg)

    def poll_msg(self):
        """See if any messages have appeared in the message thread"""

    
        all_messages = []

        while not self.output_queue.empty():
       
            all_messages.append(self.output_queue.get())

           
       # print(all_messages)

        return all_messages

    def check_connection(self):
        """Check that we have communication with eyetrike"""


        #Check the connection is live
        time.sleep(0.5)
        self.send_msg('__test')
        time.sleep(0.5)

        msg_recv = self.poll_msg()

        if 'comms.online' in msg_recv:

            return True
        
        else:

            return False

    def close_comms(self):
        """Close the communications down.

        Just joins the message thread"""

        self.recv_process.join(.01)

    def reset_time(self):
        """Reset the timer on eyetrike"""

        self.send_msg('T 0.00')


    def start_trial(self, fname):
        """Start recording a new file on eyetrike"""

        #reset time
        print "reset timestamp"
        self.reset_time()
        
        #start eyetracking recording
        self.send_msg('R ' + fname)
        
   
    def annotate(self, msg):
        """Tell eyetrike to annotate file with msg"""

        label = "A" + msg
        self.send_msg(label)


    def stop_trial(self):
        """Stop recording on eyetrike"""

        self.send_msg('r')



  

def message_receiver(recv_IP, recv_PORT, output_queue, SIZE = 1024):

    """Recieve messages from a socket and flush the messages to a pipe"""

    
    recv_sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
    recv_sock.bind((recv_IP, recv_PORT))

    recv_sock.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR,1)

    while True:
        data, addr = recv_sock.recvfrom(SIZE)

        if data: 
            #decode message
            msg = data.decode('utf-8')

            output_queue.put(msg)
		



if __name__ == '__main__':

    #If networking
    comms = pupil_comms()


    #If debugging on eyetrike
#    comms = pupil_comms(send_IP = '0.0.0.0', send_PORT = 5000, recv_IP = '0.0.0.0', recv_PORT = 5020, SIZE = 1024)

    #Check the connection is live
    connected = comms.check_connection()

    if connected:

        #Test in cosole
        comms.send_message_from_console()

    else:

        raise Exception("Not connected to comms")

    print (comms.poll_msg())

    # comms.send_message_from_console()
    