'''
(*)~---------------------------------------------------------------------------
Pupil - eye tracking platform
Copyright (C) 2012-2018 Pupil Labs

Distributed under the terms of the GNU
Lesser General Public License (LGPL v3.0).
See COPYING and COPYING.LESSER for license details.
---------------------------------------------------------------------------~(*)
'''

from time import sleep
import socket
import audio
import zmq, msgpack
import zmq_tools
from pyre import zhelper
from pyglui import ui
from plugin import Plugin
import logging
logger = logging.getLogger(__name__)

import background_helper as bh
import socket as s


def rcv_msg_from_venlab(sock, SIZE):

    while True:

        data, addr = sock.recvfrom(SIZE)
        msg = data.decode('utf-8')
        yield msg

class Venlab_Remote(Plugin):
    """
    """
    icon_chr = chr(0xe307)
    icon_font = 'pupil_icons'


    def __init__(self, g_pool):
        super().__init__(g_pool)
        self.order = .02  

        self.connect_to_pupil_remote()

        self.start_eyetrike_server()

    def connect_to_pupil_remote(self):

        ctx = zmq.Context()
        
        #create a zmq REQ socket to talk to Pupil Service/Capture
        self.req = ctx.socket(zmq.REQ)
        self.req.connect('tcp://localhost:50020') #needs to match pupil-remote settings on pupil-labs

        logger.info("venlab remote has connected to venlab comms")

    def start_eyetrike_server(self):

            #setup receive socket
        PORT = 5000
        SIZE = 1024
        host = s.gethostbyname('0.0.0.0')

        self.eyetrikesock = s.socket( s.AF_INET, s.SOCK_DGRAM )

        self.eyetrikesock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        et_addr = (host,PORT)


        self.eyetrikesock.bind(et_addr)

        logger.info("venlab remote has started a server on port: {}".format(PORT))

        self.proxy = bh.Task_Proxy('Background', rcv_msg_from_venlab, args=(self.eyetrikesock, SIZE))

    def recent_events(self, events):
            # fetch all available results
            for msg in self.proxy.fetch():
          
                self.forward_message(msg)

    def forward_message(self, msg):

        if msg in ('R','r','C','c','T','t'):

            self.req.send_string(msg) #send through to pupil_remote
            recv = self.req.recv_string() #get bounce-back
                

        elif msg == 'P':

            notification = {'subject': 'accuracy_test.should_start'}
            topic = 'notify.' + notification['subject']
            payload = msgpack.dumps(notification)

            self.req.send_string(topic, flags = zmq.SNDMORE)
            self.req.send(payload)
            recv = self.req.recv_string()

        elif msg == 'p':

            notification = {'subject': 'accuracy_test.should_stop'}
            topic = 'notify.' + notification['subject']
            payload = msgpack.dumps(notification)

            self.req.send_string(topic, flags = zmq.SNDMORE)
            self.req.send(payload)
            recv = self.req.recv_string()
                    
    def cleanup(self):
        """gets called when the plugin get terminated.
           This happens either voluntarily or forced.
        """
        self.eyetrikesock.close()
        self.proxy.cancel()

    def on_notify(self, notification):
        """send simple string messages to control application functions.

        Emits notifications:
            ``recording.should_start``
            ``recording.should_stop``
            ``calibration.should_start``
            ``calibration.should_stop``
            Any other notification received though the reqrepl port.
        """
        pass

