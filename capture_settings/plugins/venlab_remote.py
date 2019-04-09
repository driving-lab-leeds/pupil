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

# import matplotlib.pyplot as plt




def recv_socket_process(host, PORT, SIZE):


    recv_sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
    recv_sock.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR,1)
       
    recv_sock.bind((host, PORT))


    while True:

        # data = recv_msg(recv_sock)
        # print(data)
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


        #When running on network
        self.send_IP = '192.168.0.1' #IP of machine you want to send messages to 
        self.send_port = 5020

        self.recv_host = '192.168.0.2'
        self.recv_port = 5000

        #When debuggin on eyetrike
        # self.send_IP = '0.0.0.0' #IP of machine you want to send messages to 
        # self.send_port = 5020

        # self.recv_host = '0.0.0.0'
        # self.recv_port = 5000

   
        self.connect_to_pupil_remote()
        self.start_eyetrike_server()

        #Variables for calculating calibration accuracy

        self.accuracy = None
        self.precision = None
        self.error_lines = None
        self.recent_input = None
        self.recent_labels = None
        self.test_markers = None

        # .5 degrees, used to remove outliers from precision calculation
        self.succession_threshold = np.cos(np.deg2rad(.5))
        self._outlier_threshold = 5.0  # in degrees

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

     
        print(msg)
        accepted_commands = ('R','r','C','c','T','t')

    
        if msg[0] in accepted_commands:

            self.req.send_string(msg) #send through to pupil_remote
            recv = self.req.recv_string() #get bounce-back      

            self.send_rply('ipc', recv)

            if msg[0] == 'T':
                #Send timestamp back
                self.req.send_string('t') #send through to pupil_remote
                recvtime = self.req.recv_string() #get bounce-back     
                self.send_rply('Timesync', 'timestamp: ' + str(recvtime))        
        
            

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
            self.recent_surfaces = notification.get('surface_list', [])
            self.marker_times = notification.get('marker_times', [])

            if (self.recent_surfaces) and (self.test_markers is not None):

                logger.info("Running pixel accuracy test")

                # all_av_error, all_sd_error = self.get_pixel_accuracy(self.recent_surfaces, self.test_markers, self.recent_input, self.recent_labels, self.marker_times)

                # pickle.dump([all_av_error, all_sd_error], open('calib_data.pkl', 'wb'))
                # pickle.dump(self.test_markers, open('test_markers.pkl', 'wb'))

                # pickle.dump(self.recent_surfaces, open('surface_list.pkl', 'wb'))
                # pickle.dump(self.test_markers, open('test_markers.pkl', 'wb'))

                # pickle.dump(self.recent_input, open('recent_input.pkl', 'wb'))
                # pickle.dump(self.recent_labels, open('recent_labels.pkl', 'wb'))

                # pickle.dump(self.marker_times, open('marker_times.pkl', 'wb'))

            if self.recent_input and self.recent_labels:

                self.recalculate()

             
                msg = '{}//{}'.format(self.accuracy, self.precision)

                self.send_rply('calibration', msg)


        elif notification['subject'] in ('calibration.marker_sample_completed'):
            
            #Here i should recprd the timestep when these happen so we know which marker has just finished

            self.send_rply('calibration', 'marker_sample_completed')

    



    def send_rply(self, subject, msg):

        out = '{}.{}'.format(subject, msg)

        # send_msg(self.send_sock, self.send_addr, out.encode())
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


    def closest_matches_monocular_surface(self, ref_pts, pupil_pts, surfaces, max_dispersion=1/15.):
        '''
        get pupil positions closest in time to ref points.
        return list of dict with matching ref and pupil datum.

        if your data is binocular use:
        pupil0 = [p for p in pupil_pts if p['id']==0]
        pupil1 = [p for p in pupil_pts if p['id']==1]
        to get the desired eye and pass it as pupil_pts
        '''

        ref = ref_pts
        pupil0 = pupil_pts
        pupil0_ts = np.array([p['timestamp'] for p in pupil0])

        #surface timestamp
        surface_ts = np.array([s['timestamp'] for s in surfaces])

        def find_nearest_idx(array,value):
            idx = np.searchsorted(array, value, side="left")
            try:
                if abs(value - array[idx-1]) < abs(value - array[idx]):
                    return idx-1
                else:
                    return idx
            except IndexError:
                return idx-1

        matched = []
        if pupil0:
            for r in ref_pts:
                closest_p0_idx = find_nearest_idx(pupil0_ts,r['timestamp'])
                closest_p0 = pupil0[closest_p0_idx]
                dispersion = max(closest_p0['timestamp'],r['timestamp']) - min(closest_p0['timestamp'],r['timestamp'])

                #Do the same for surfaces
                closest_s_idx = find_nearest_idx(surface_ts, r['timestamp'])
                closest_s = surfaces[closest_s_idx]
                surf_dispersion = max(closest_s['timestamp'],r['timestamp']) - min(closest_s['timestamp'],r['timestamp'])

                if (dispersion < max_dispersion) and (surf_dispersion < max_dispersion):
                    matched.append({'ref':r,'pupil':closest_p0, 'surface': closest_s})
                else:
                    pass
        return matched

    def get_marker_index(self, surf_ts, times):

        times = np.append(times, np.Inf)

        out = np.empty(surf_ts.size)
        out.fill(np.NaN)

        for i in range(times.size -1):

            marker_mask = np.logical_and(surf_ts < times[i + 1], surf_ts >= times[i])

            out[marker_mask] = i


        return out


    def get_pixel_accuracy(self, surface_list, test_markers, recent_input, recent_labels, marker_times):

        #Make surface list one list
        surface_list = [i for s in surface_list for i in s ]
        #use recent input and recent_labels (ref pos)
        matched_surf = self.closest_matches_monocular_surface(recent_input, recent_labels, surface_list)#

        matched_surf_tf = np.array([s['ref']['timestamp'] for s in matched_surf])

        marker_at_time = self.get_marker_index(matched_surf_tf, marker_times)


        all_avg_errors = np.empty(np.array(test_markers.shape))
        all_std_errors = np.empty(np.array(test_markers.shape))

        msg = 'Accuracy//{}.Precision//{}'.format(all_avg_errors, all_std_errors)

        self.send_rply('calibration', msg)

        # plt.figure()
        # ax = plt.gca()
        # colors = sns.color_palette("Set1", 12)
        # ax.set_xlim([0, 1])
        # ax.set_ylim([0, 1])

        for i in range(len(test_markers)):
            m0 = np.array(matched_surf)[marker_at_time == i].tolist()

            norm_pos = [m['surface']['norm_pos'] for m in m0]

            # ax.scatter(np.array(norm_pos)[:,0], np.array(norm_pos)[:,1], color = colors[i])

            error = (np.array(norm_pos) - test_markers[0])

            all_avg_errors[i] = error.mean(0)
            all_std_errors[i] = error.std(0)

            mean_error = np.mean(all_avg_errors)
            std_error = np.mean(all_std_errors)

            

      
        # plt.plot(np.array(test_markers)[:,0], np.array(test_markers)[:,1], 'ko', ms =10)
        # plt.legend()

        # plt.savefig('calibration.jpg')

        return all_avg_errors, all_std_errors 
