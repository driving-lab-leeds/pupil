###script to check cv2

import cv2, os

vidpath = "/home/eyetrike/drivinglab_pupil/world_old.mp4"
if os.path.exists(vidpath):
	video = cv2.VideoCapture(vidpath)
	print ("Opened: ", video.isOpened())
else:
	print ("File does not exist")
