import socket as s

class pupil_comms:

    def __init__(self, ip_add = '0.0.0.0', PORT = 5000, SIZE = 1024):
        """A class for communicating with pupil labs over a network connection, using TCP

        Set IP address to '0.0.0.0' if running from pupil labs computer"""

        self.host = ip_add
        self.PORT = PORT
        self.SIZE = SIZE

    def connect_to_pupil(self):
        """Establish a TCP connection with pupil labs.

        Ensure that both the pupil_remote and venlab_remote plugins are turned on in pupil labs"""


        self.server_socket = s.socket( s.AF_INET, s.SOCK_STREAM)
        self.server_socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)

        try:
            self.server_socket.connect((self.host, self.PORT))
        except ConnectionRefusedError:
            raise Exception("Unable to connect to socket. Check network.")

    def send(self, msg):

        if msg == 'q':

            self.server_socket.close()                
        else:
            self.server_socket.send(msg.encode('utf-8'))

    def send_message_from_console(self):
        """Type messages over the console. 
        Enter q to close"""

        while True:
            msg = input("Type a command ")

            if msg == 'q':
                self.server_socket.close()
                return
            else:
                self.server_socket.send(msg.encode('utf-8'))

    def close(self):

        self.server_socket.close()


if __name__ == '__main__':

    comms = pupil_comms()

    comms.connect_to_pupil()

    # comms.send_message_from_console()

    # comms.send('P')

    comms.close()