'''
(*)~---------------------------------------------------------------------------
Pupil - eye tracking platform
Copyright (C) 2012-2018 Pupil Labs

Distributed under the terms of the GNU
Lesser General Public License (LGPL v3.0).
See COPYING and COPYING.LESSER for license details.
---------------------------------------------------------------------------~(*)
'''

import pickle 
import numpy as np
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
import numpy as np
from calibration_routines.calibrate import closest_matches_monocular

from collections import namedtuple
Calculation_Result = namedtuple('Calculation_Result', ['result', 'num_used', 'num_total'])


def recv_socket_process(host, PORT, SIZE):


    recv_sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
    recv_sock.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR,1)
       
    recv_sock.bind((host, PORT))


    while True:

        data, addr = recv_sock.recvfrom(SIZE)

        if data: 
            #decode message
            msg = data.decode('utf-8')
            yield msg




class Venlab_Remote(Plugin):
    """
    """
    icon_chr = chr(0xe307)
    icon_font = 'pupil_icons'


    def __init__(self, g_pool):
        super().__init__(g_pool)
        self.order = .3


        # #When running on network
        # self.send_IP = '192.168.0.1' #IP of machine you want to send messages to 
        # self.send_port = 5020

        # self.recv_host = '192.168.0.2'
        # self.recv_port = 5000

        #When debuggin on eyetrike
        self.send_IP = '0.0.0.0' #IP of machine you want to send messages to 
        self.send_port = 5020

        self.recv_host = '0.0.0.0'
        self.recv_port = 5000

   
        self.connect_to_pupil_remote()
        self.start_eyetrike_server()

        #Variables for calculating calibration accuracy

        self.accuracy = None
        self.precision = None
        self.error_lines = None
        self.recent_input = None
        self.recent_labels = None

        # .5 degrees, used to remove outliers from precision calculation
        self.succession_threshold = np.cos(np.deg2rad(.5))
        self._outlier_threshold = .5  # in degrees

    @property
    def outlier_threshold(self):
        return self._outlier_threshold

    def connect_to_pupil_remote(self):

        ctx = zmq.Context()
        
        #create a zmq REQ socket to talk to Pupil Service/Capture
        self.req = ctx.socket(zmq.REQ)
        self.req.connect('tcp://localhost:50020') #needs to match pupil-remote settings on pupil-labs

        logger.info("venlab remote has connected to venlab comms")

    def start_eyetrike_server(self):

        #setup receive socket
        recv_PORT = self.recv_port 
        SIZE = 1024

        recv_host = self.recv_host
     
        self.recv_proxy = bh.Task_Proxy('Background', recv_socket_process, args=( recv_host, recv_PORT, SIZE))



        #setup send socket
        send_PORT = self.send_port #needs to match venlab
      
        self.send_sock = s.socket(s.AF_INET, s.SOCK_DGRAM)
        self.send_addr = (self.send_IP, send_PORT)



    def recent_events(self, events):

      
        for msg in self.recv_proxy.fetch():            
          
            self.forward_message(msg)

       
    def forward_message(self, msg):

     
        accepted_commands = ('R','r','C','c','T','t')

        if msg[0] in accepted_commands:

            self.req.send_string(msg) #send through to pupil_remote
            recv = self.req.recv_string() #get bounce-back                
        
            self.send_rply('ipc', recv)

        elif msg[0] == 'A':

            ##annotation
            label = msg[1:] #grab trialtype


            #fetch time
            self.req.send_string('t') #send through to pupil_remote
            recvtime = self.req.recv_string() #get bounce-back

            notification = {'subject':'annotation','label':label,'timestamp':float(recvtime),'duration':5.0,'source':'eyetrike','record':True}
            topic = 'notify.'+ notification['subject']
            payload = msgpack.dumps(notification)
            self.req.send_string(topic,flags=zmq.SNDMORE)
            self.req.send(payload)
            recv = self.req.recv_string()

            self.send_rply('ipc', recv)



        elif msg == 'P':

            notification = {'subject': 'accuracy_test.should_start'}
            topic = 'notify.' + notification['subject']
            payload = msgpack.dumps(notification)

            self.req.send_string(topic, flags = zmq.SNDMORE)
            self.req.send(payload)
            recv = self.req.recv_string()

            self.send_rply('ipc', recv)


        elif msg == 'p':

            notification = {'subject': 'accuracy_test.should_stop'}
            topic = 'notify.' + notification['subject']
            payload = msgpack.dumps(notification)

            self.req.send_string(topic, flags = zmq.SNDMORE)
            self.req.send(payload)
            recv = self.req.recv_string()

            self.send_rply('ipc', recv)

        elif msg == '__test':

            print("venlab_remote: replying to test message")
            self.send_rply('comms', 'online')

        elif msg[:8] == 'markers:':

            test_markers = msg[8:]

            test_markers = [float(i) for i in test_markers.split("__")]

            self.test_markers = np.array(test_markers).reshape(len(test_markers)//2, 2)
       
        

        
                    
    def cleanup(self):
        """gets called when the plugin get terminated.
           This happens either voluntarily or forced.
        """
        
        self.send_sock.close()
                   

    def on_notify(self, notification):
        """send simple string messages to control application functions.

        Emits notifications:
            ``recording.should_start``
            ``recording.should_stop``
            ``calibration.should_start``
            ``calibration.should_stop``
            Any other notification received though the reqrepl port.
        """

        if notification['subject'] in ('calibration.calibration_data', 'accuracy_test.data'):
            
            self.recent_input = notification['pupil_list']
            self.recent_labels = notification['ref_list']

            #Get surface data (optionally used to get normalised position data)
            self.recent_surfaces = notification['surface_list']

            if (self.recent_surfaces) and (self.test_markers):

                logger.info("Running pixel accuracy test")

                pickle.dump(self.recent_surfaces, open('surface_list.pkl', 'wb'))
                pickle.dump(self.test_markers, open('test_markers.pkl', 'wb'))

            if self.recent_input and self.recent_labels:

                self.recalculate()

                msg = 'Accuracy.{}.Precision.{}'.format(self.accuracy, self.precision)

                self.send_rply('calibration', msg)


        elif notification['subject'] in ('calibration.marker_sample_completed'):
            
            #Here i should recprd the timestep when these happen so we know which marker has just finished

            self.send_rply('calibration', 'marker_sample_completed')


    def send_rply(self, subject, msg):

        out = '{}.{}'.format(subject, msg)
        self.send_sock.sendto(out.encode(), self.send_addr)


    def recalculate(self):
        assert self.recent_input and self.recent_labels
        prediction = self.g_pool.active_gaze_mapping_plugin.map_batch(self.recent_input)
        results = self.calc_acc_prec_errlines(prediction, self.recent_labels,
                                              self.g_pool.capture.intrinsics)
     
        self.accuracy = results[0].result
        self.precision = results[1].result
        self.error_lines = results[2]

     

    def calc_acc_prec_errlines(self, gaze_pos, ref_pos, intrinsics):
        width, height = intrinsics.resolution

        # reuse closest_matches_monocular to correlate one label to each prediction
        # correlated['ref']: prediction, correlated['pupil']: label location
        correlated = closest_matches_monocular(gaze_pos, ref_pos)
        
        # [[pred.x, pred.y, label.x, label.y], ...], shape: n x 4
        locations = np.array([(*e['ref']['norm_pos'], *e['pupil']['norm_pos']) for e in correlated])
        error_lines = locations.copy()  # n x 4
        locations[:, ::2] *= width
        locations[:, 1::2] = (1. - locations[:, 1::2]) * height
        locations.shape = -1, 2

        # Accuracy is calculated as the average angular
        # offset (distance) (in degrees of visual angle)
        # between fixations locations and the corresponding
        # locations of the fixation targets.
        undistorted_3d = intrinsics.unprojectPoints(locations, normalize=True)

        # Cosine distance of A and B: (A @ B) / (||A|| * ||B||)
        # No need to calculate norms, since A and B are normalized in our case.
        # np.einsum('ij,ij->i', A, B) equivalent to np.diagonal(A @ B.T) but faster.
        angular_err = np.einsum('ij,ij->i', undistorted_3d[::2, :], undistorted_3d[1::2, :])

        # Good values are close to 1. since cos(0) == 1.
        # Therefore we look for values greater than cos(outlier_threshold)
        selected_indices = angular_err > np.cos(np.deg2rad(self.outlier_threshold))
        selected_samples = angular_err[selected_indices]
        num_used, num_total = selected_samples.shape[0], angular_err.shape[0]

        error_lines = error_lines[selected_indices].reshape(-1, 2)  # shape: num_used x 2
        accuracy = np.rad2deg(np.arccos(selected_samples.mean()))
        accuracy_result = Calculation_Result(accuracy, num_used, num_total)

        # lets calculate precision:  (RMS of distance of succesive samples.)
        # This is a little rough as we do not compensate headmovements in this test.

        # Precision is calculated as the Root Mean Square (RMS)
        # of the angular distance (in degrees of visual angle)
        # between successive samples during a fixation
        undistorted_3d.shape = -1, 6  # shape: n x 6
        succesive_distances_gaze = np.einsum('ij,ij->i', undistorted_3d[:-1, :3], undistorted_3d[1:, :3])
        succesive_distances_ref = np.einsum('ij,ij->i', undistorted_3d[:-1, 3:], undistorted_3d[1:, 3:])

        # if the ref distance is to big we must have moved to a new fixation or there is headmovement,
        # if the gaze dis is to big we can assume human error
        # both times gaze data is not valid for this mesurement
        selected_indices = np.logical_and(succesive_distances_gaze > self.succession_threshold,
                                          succesive_distances_ref > self.succession_threshold)
        succesive_distances = succesive_distances_gaze[selected_indices]
        num_used, num_total = succesive_distances.shape[0], succesive_distances_gaze.shape[0]
        precision = np.sqrt(np.mean(np.arccos(succesive_distances) ** 2))
        precision_result = Calculation_Result(precision, num_used, num_total)

        return accuracy_result, precision_result, error_lines