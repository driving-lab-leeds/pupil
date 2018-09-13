"""A script to test the timesync between venlab and eyetrike"""

from UDP_comms import pupil_comms
import time


if __name__ == '__main__':

    #If networking
    # comms = pupil_comms()

    test_markers = [[5, 2], [6,20], [9,3]]
    #If debugging on eyetrike
    #comms = pupil_comms(send_IP = '0.0.0.0', send_PORT = 5000, recv_IP = '0.0.0.0', recv_PORT = 5020, SIZE = 1024)
    comms = pupil_comms()

    #Check the connection is live
    connected = comms.check_connection()

    

    if connected:

        comms.send_marker_positions(test_markers)

        # #Test in cosole
        # comms.send_message_from_console()        



    else:

        raise Exception("Not connected to comms")
    
    currtime = time.time()
    #comms.reset_time(currtime)
    comms.reset_time(0)

    polled = False
    while not polled:
        msgs = comms.poll_msg()
        if len(msgs) > 0:
            polled = True
            print (msgs)
    #print (comms.poll_msg())

    print('After poll: ' + str(time.time()))

    # comms.send_message_from_console()
    