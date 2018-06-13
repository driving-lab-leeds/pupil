#!/usr/bin/env python3
#adapted 30-10-17 to enable integration with driving code. Last updated 01/12/17
#get_ET enables retrieval of packets from EyeTrike (eyetracker linux laptop)
#author c.d.mole@leeds.ac.uk. to interface with Eyetrike.
#also adds head markers to the scene. 

#from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM
import socket as s
import sys
import viz
import math as mt
import numpy as np

class comms:
	def __init__(self):
		
		self.ET_Flag = viz.ask('Use Eyetracking?')
		
		if self.ET_Flag==1:
			
			viz.callback(viz.EXIT_EVENT,self.close_all)
			
			print "if ADDRESS_IN_USE error, incremement portnumbers of self.PORT2 and corresponding portnumber in venlab_comms.py"
			
			#send settings
			self.PORT1 = 5000		
			self.SIZE = 1024
			self.TARGET_IP   = '192.168.0.6' #eyetrike PC. 
			
			self.eyetrikesock = s.socket( s.AF_INET, s.SOCK_DGRAM )
			self.et_addr = (self.TARGET_IP, self.PORT1)
			
			#receive settings 
			self.PORT2 = 5002 #needs to be the same as eyetrike script.
			self.hostName = s.gethostbyname( '0.0.0.0' )
			self.venlabsock = s.socket( s.AF_INET, s.SOCK_DGRAM )
			self.vl_addr = (self.hostName,self.PORT2)
			self.venlabsock.bind( self.vl_addr )	
			
			#add markers
			self.markers = markers()
						
			viz.message('Pupil Capture and venlab_comms.py must be running on Eyetrike Laptop') #could be a yes/no at the start of the experimental file. #addchecklist.
			
			print 'testing connection...if experiment hangs here, check venlab_comms.py is running on eyetrike'
			#check connection
			chk = self.send('p')
			
			print 'testing comms...if experiment hangs here, check pupil-remote port is 50020'
			timestamp = self.fetchtime()
			print (timestamp)
		else:
			print "Eyetracking Disabled"
		
	
	def send(self,msg):
		
		#msg: 'C','c' to start and stop calibration. 
		#'R','r' to start and stop recording. 'R XXX' to name recording.
		#'check' to check connection.
		
		#should get a bound-back with an affirmative connection
		
		if self.ET_Flag == 1:
		
			try:
				#print "COMMS attempted send: " , msg
				self.eyetrikesock.sendto(msg.encode('utf-8'), self.et_addr)
				print "COMMS sent: ", msg
				
				data, server = self.venlabsock.recvfrom(self.SIZE)
				print "COMMS recv: ",data
			except:
				print 'failed! Check connection'
			
	def sendAnnotation(self,msg):
		#same as send, just adds "A" to signal to venlab_comms.
		
		if self.ET_Flag==1:

			label = "A"+msg
			try:
				#print "COMMS attempted send: " , msg
				self.eyetrikesock.sendto(label.encode('utf-8'), self.et_addr)
				print "COMMS sent: ", label
				
				data, server = self.venlabsock.recvfrom(self.SIZE)
				print "COMMS recv: ",data
			except:
				print 'failed! Check connection'

	def fetchtime(self):
		#fetch data stream. But return -999 if no connection.
		#try:
			#msg = self.sock.recvfrom(self.SIZE)
			#this isn't the most up to date time.
		#request time
		if self.ET_Flag==1:
		 
			self.eyetrikesock.sendto('t'.encode('utf-8'), self.et_addr)
		
			data, server = self.venlabsock.recvfrom(self.SIZE)					
			return (data)
				
			#except:
			#	print ('-999')
			#	return ('-999')
	
	def resettime(self):

		if self.ET_Flag==1:
			
			#resettime timestamp to 0. 
			self.eyetrikesock.sendto('T 0.00'.encode('utf-8'), self.et_addr)
			data, server = self.venlabsock.recvfrom(self.SIZE)					
			return "COMMS recv: ", data

	def close_all(self):
		
		if self.ET_Flag==1:
			self.finish_trial()
			self.venlabsock.close() 
			self.eyetrikesock.close()
			
			print "COMMS closed..."
			
	def start_trial(self, filename,trialtype_signed):
		
		#for starting a trial
		if self.ET_Flag == 1:
			
			#reset time
			print "reset timestamp"
			self.resettime()
			
			#start eyetracking recording
			self.send('R ' + filename)
			
			#annotate condition
			comms.sendAnnotation(self,str(trialtype_signed))
		
	def finish_trial(self):
		
		#finish recording.
		if self.ET_Flag==1:
			
			#stop eyetrike recording.
			self.send('r')
	

class markers:
	def __init__(self):
		

		#function to add headmarkers
		self.file_hm1 = '../textures/marker1_white.png'
		self.file_hm2 = '../textures/marker2_white.png'
		self.file_hm3 = '../textures/marker3_white.png'
		self.file_hm4 = '../textures/marker4_white.png'
		self.file_hm5 = '../textures/marker5_white.png'
		self.file_hm6 = '../textures/marker6_white.png'
		self.file_hm7 = '../textures/marker7_white.png'
	
		boxsize = [.8,.5] #xy box size
		lowerleft = [.1,.1] #starting corner
		sc = .8
	
		#two ways of doing it
		#bottom left
		self.hm1 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
		self.hm1.texture(viz.add(self.file_hm1))
		self.hm1.setPosition([lowerleft[0],lowerleft[1],0])
		self.hm1.scale(sc,sc,sc)
		
		#top left
		self.hm2 = viz.add(viz.TEXQUAD,viz.SCREEN)
		self.hm2.texture(viz.add(self.file_hm2))	
		self.hm2.setPosition([lowerleft[0],lowerleft[1]+boxsize[1],0])
		self.hm2.scale(sc,sc,sc)
		
		#bottom right
		self.hm3 = viz.add(viz.TEXQUAD,viz.SCREEN)
		self.hm3.texture(viz.add(self.file_hm3))
		self.hm3.setPosition([lowerleft[0]+boxsize[0],lowerleft[1],0])
		self.hm3.scale(sc,sc,sc)
		
		#top right
		self.hm4 = viz.add(viz.TEXQUAD,viz.SCREEN)
		self.hm4.texture(viz.add(self.file_hm4))
		self.hm4.setPosition([lowerleft[0]+boxsize[0],lowerleft[1]+boxsize[1],0])
		self.hm4.scale(sc,sc,sc)
	
		#add middle markers
#		#middle top
#		self.hm5 = viz.add(viz.TEXQUAD,viz.SCREEN)
#		self.hm5.texture(viz.add(self.file_hm5))
#		self.hm5.setPosition([lowerleft[0]+boxsize[0]/2,lowerleft[1]+boxsize[1],0])
#		self.hm5.scale(sc,sc,sc)
		
		#middle top right
		self.hm6 = viz.add(viz.TEXQUAD,viz.SCREEN)
		self.hm6.texture(viz.add(self.file_hm6))
		self.hm6.setPosition([lowerleft[0]+(boxsize[0]*2)/3,lowerleft[1]+boxsize[1],0])
		self.hm6.scale(sc,sc,sc)
		
		#middle top left
		self.hm7 = viz.add(viz.TEXQUAD,viz.SCREEN)
		self.hm7.texture(viz.add(self.file_hm7))
		self.hm7.setPosition([lowerleft[0]+(boxsize[0]*1)/3,lowerleft[1]+boxsize[1],0])
		self.hm7.scale(sc,sc,sc)

def GazeAngleToScreen(h,v):
	#takes desired gaze angle and translate it into screen coords.
	#h = horizontal GA; v=vertical GA. Assumes +ve = right; -ve = left; input in degrees
	proj_width = 1.965 #real-world measurements of projection in metres
	proj_height = 1.115 
	
	hrad = (h*mt.pi)/180 #convert to radians
	vrad = (v*mt.pi)/180
	
	centre = .5 #assumes centre of screen is centre of display. 	
	screen_dist = 1.0 #in metres
		
	real_h = mt.tan(hrad)*screen_dist #desired onscreen distance in metres
	real_v = mt.tan(vrad)*screen_dist #desired onscreen distance in metres
	
	#print "real h: " + str(real_h)
	#print "real v: " + str(real_v)
	
	scaled_h = real_h/proj_width #scaled difference to centre
	scaled_v = real_v/proj_height #scaled difference to centre
	
	x = scaled_h+centre #add centre to obtain on screen coords.
	y = scaled_v+centre
	
	return [x,y]
	
def ScreenToGazeAngle(x,y):
	#takes onscreen x,y coords and returns gaze angle
	proj_width = 1.965
	proj_height = 1.115
	
	centre = .5 #assumes centre of screen is centre of display. 	
	screen_dist = 1.0 #in metres
	
	#convert the scale to real-distances from centre.
	real_h = (x-centre)*proj_width
	real_v = (y-centre)*proj_height
	#real_h = (x-centre)*1
	#real_v = (y-centre)*1
	
	#print "real h: " + str(real_h)
	#print "real v: " + str(real_v)
	
	#calculate gaze angle
	hrad = mt.atan(real_h/screen_dist)
	vrad = mt.atan(real_v/screen_dist)
	
	#convert to degrees
	h = (hrad*180)/mt.pi
	v = (vrad*180)/mt.pi
	
	return [h, v]

def OpticalGrid(RoadCentreR=None,RoadCentreL=None,GazeAngles=None):
	
	#if roadcentre and gaze angles are specified, return positions of a optical grid focussed on roadcentre
	#3 on first and second row. 5 on third row.
	#assumes GazeAngles is 2x1 vector with horiz eccentricity and vertical eccentry.
	#RoadCentre is 2x1 array specifying on-screen roadcentre coords.
	ElevationFar = 5.0 #5 degrees below 
	proj_height = 1.115
	
	GridR = []	
	GridL = []
	
	if RoadCentreR==None:
		#specify default road centre.		
		ElevationFarPos = (proj_height/2 - 1*mt.tan(ElevationFar*mt.pi/180))/proj_height
		AzimuthFarMid =  0.655 #this is determined by print-screening a road-centre placed in the road.		
		RoadCentreR = [AzimuthFarMid, ElevationFarPos]
		
	if RoadCentreL==None:
		#specify default road centre for left grid		
		
		ElevationFarPos = (proj_height/2 - 1*mt.tan(ElevationFar*mt.pi/180))/proj_height
		AzimuthFarMid =  .365 #this is determined by print-screening a road-centre placed in the road.		
		RoadCentreL = [AzimuthFarMid, ElevationFarPos]
		
			
	if GazeAngles==None:
		print "Please specify GazeAngles"
		return GridR, GridL
	else:
		
		GA_RCR = ScreenToGazeAngle(RoadCentreR[0],RoadCentreR[1])
		GA_leftR = GA_RCR[0] - GazeAngles[0]
		GA_rightR = GA_RCR[0] + GazeAngles[0]
		GA_extremeRR = GA_RCR[0] + (GazeAngles[0]*2)
		GA_extremeLR = GA_RCR[0] - (GazeAngles[0]*2)
			
		GridR.append(GazeAngleToScreen(GA_leftR,GA_RCR[1])) #Topleft
		GridR.append(RoadCentreR) #RoadCentre
		GridR.append(GazeAngleToScreen(GA_rightR,GA_RCR[1])) #TopRight				
			
		GA_midR = GA_RCR[1] - GazeAngles[1] #the further left/right values are merely double the previous. 
			
		GridR.append(GazeAngleToScreen(GA_leftR,GA_midR)) #middleleft
		GridR.append(GazeAngleToScreen(GA_RCR[0],GA_midR)) #middlecentre
		GridR.append(GazeAngleToScreen(GA_rightR,GA_midR)) #middleright		
			
		GA_lowR = GA_RCR[1] - GazeAngles[1]*2 
		
		GridR.append(GazeAngleToScreen(GA_leftR,GA_lowR)) #bottomleft
		GridR.append(GazeAngleToScreen(GA_RCR[0],GA_lowR)) #bottomcentre
		GridR.append(GazeAngleToScreen(GA_rightR,GA_lowR)) #bottomright
		
		GridR.append(GazeAngleToScreen(GA_extremeLR,GA_lowR)) #bottomfurther_right
		GridR.append(GazeAngleToScreen(GA_extremeRR,GA_lowR)) #bottomfurther_left
		
		
		###LEFT ROAD GRID
		GA_RCL = ScreenToGazeAngle(RoadCentreL[0],RoadCentreL[1])
		GA_leftL = GA_RCL[0] - GazeAngles[0]
		GA_rightL = GA_RCL[0] + GazeAngles[0]
		GA_extremeRL = GA_RCL[0] + (GazeAngles[0]*2)
		GA_extremeLL = GA_RCL[0] - (GazeAngles[0]*2)
			
		GridL.append(GazeAngleToScreen(GA_leftL,GA_RCL[1])) #Topleft
		GridL.append(RoadCentreL) #RoadCentre
		GridL.append(GazeAngleToScreen(GA_rightL,GA_RCL[1])) #TopRight		
			
		GA_midL = GA_RCL[1] - GazeAngles[1] #the further left/right values are merely double the previous. 
			
		GridL.append(GazeAngleToScreen(GA_leftL,GA_midL)) #middleleft
		GridL.append(GazeAngleToScreen(GA_RCL[0],GA_midL)) #middlecentre
		GridL.append(GazeAngleToScreen(GA_rightL,GA_midL)) #middleright
			
		GA_lowL = GA_RCL[1] - GazeAngles[1]*2 
		
		GridL.append(GazeAngleToScreen(GA_leftL,GA_lowL)) #bottomleft
		GridL.append(GazeAngleToScreen(GA_RCL[0],GA_lowL)) #bottomcentre
		GridL.append(GazeAngleToScreen(GA_rightL,GA_lowL)) #bottomright
		
		GridL.append(GazeAngleToScreen(GA_extremeLL,GA_lowL)) #bottomfurther_right
		GridL.append(GazeAngleToScreen(GA_extremeRL,GA_lowL)) #bottomfurther_left
				
		return GridR, GridL

def optical_grid_relativeToRoad():
	fixName = '../textures/fix_trans_calib.gif'
	fixation_size = .2

	###setup invisible lines. For left bends they will need to be mirrored.
	r = 60.0 
	straight_road = 0.5 # Straight Road Length
	OverPosition = -2.5#-0.75
	UnderPosition = 2.5#0.75	
	# 10000 splits during curve because PI = 3.142*1.5*10000 = 47120
	x_right_under = np.zeros(4712)
	z_right_under = np.zeros(4712)
	x_right_over = np.zeros(4712)
	z_right_over = np.zeros(4712)
	x_left_under = np.zeros(4712)
	z_left_under = np.zeros(4712)
	x_left_over = np.zeros(4712)
	z_left_over = np.zeros(4712)
	left_array_fix2 = np.arange(0.0, np.pi*1.5*1000)/1000
	right_array_fix2 = np.arange(np.pi*1000, -np.pi*0.5*1000, -1)/1000  ##arange(start,stop,step). Array with 3142(/10000) numbers

	c = 0
	while c < 4712:
		x_right_under[c] = (r + UnderPosition)*np.cos(right_array_fix2[c]) + r
		z_right_under[c] = (r + UnderPosition)*np.sin(right_array_fix2[c]) + straight_road
		x_right_over[c] = (r + OverPosition)*np.cos(right_array_fix2[c]) + r
		z_right_over[c] = (r + OverPosition)*np.sin(right_array_fix2[c]) + straight_road
		x_left_under[c] = (r + UnderPosition)*np.cos(left_array_fix2[c]) - r
		z_left_under[c] = (r + UnderPosition)*np.sin(left_array_fix2[c]) + straight_road
		x_left_over[c] = (r + OverPosition)*np.cos(left_array_fix2[c]) - r
		z_left_over[c] = (r + OverPosition)*np.sin(left_array_fix2[c]) + straight_road
		
		c += 1

	##return list of fixation objects
	fixations = []
	
	pos = [0, 0, 0]
	
	FarRange_Near = 20.0
	FarRange_Far = 20.2
	
	Interval = 7.0
	
	MidRange_Near = FarRange_Near - Interval
	MidRange_Far = FarRange_Far - Interval
	
	NearRange_Near = MidRange_Near - Interval
	NearRange_Far = MidRange_Far - Interval
	

	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_under[fixation_counter] )**2 ) + ( ( pos[2] - z_right_under[fixation_counter] )**2 ) )
		if ( (fix_dist < FarRange_Near) | (fix_dist > FarRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > FarRange_Near) and (fix_dist < FarRange_Far) ):
			fpx = x_right_under[fixation_counter]
			fpz = z_right_under[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
	
	#Top left
	screen = viz.worldtoscreen([fpx,0,fpz])
	f1 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f1.texture(viz.add(fixName))
	f1.setPosition([screen[0], screen[1], 0])
	f1.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f1)	

	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_mid[fixation_counter] )**2 ) + ( ( pos[2] - z_right_mid[fixation_counter] )**2 ) )
		if ( (fix_dist < FarRange_Near) | (fix_dist > FarRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > FarRange_Near) and (fix_dist < FarRange_Far) ):
			fpx = x_right_mid[fixation_counter]
			fpz = z_right_mid[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
	
	#Top middle
	screen = viz.worldtoscreen([fpx,0,fpz])
	f2 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f2.texture(viz.add(fixName))
	f2.setPosition([screen[0], screen[1], 0])
	f2.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f2)

	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_over[fixation_counter] )**2 ) + ( ( pos[2] - z_right_over[fixation_counter] )**2 ) )
		if ( (fix_dist < FarRange_Near) | (fix_dist > FarRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > FarRange_Near) and (fix_dist < FarRange_Far) ):
			fpx = x_right_over[fixation_counter]
			fpz = z_right_over[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
	
	#Top-Right
	screen = viz.worldtoscreen([fpx,0,fpz])
	f3 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f3.texture(viz.add(fixName))
	f3.setPosition([screen[0], screen[1], 0])
	f3.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f3)

	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_under[fixation_counter] )**2 ) + ( ( pos[2] - z_right_under[fixation_counter] )**2 ) )
		if ( (fix_dist < MidRange_Near) | (fix_dist > MidRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > MidRange_Near) and (fix_dist < MidRange_Far) ):
			fpx = x_right_under[fixation_counter]
			fpz = z_right_under[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
		
	#Middle Left	
	screen = viz.worldtoscreen([fpx,0,fpz])
	f4 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f4.texture(viz.add(fixName))
	f4.setPosition([screen[0], screen[1], 0])
	f4.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f4)

	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_under[fixation_counter] )**2 ) + ( ( pos[2] - z_right_under[fixation_counter] )**2 ) )
		if ( (fix_dist < MidRange_Near) | (fix_dist > MidRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > MidRange_Near) and (fix_dist < MidRange_Far) ):
			fpx = x_right_mid[fixation_counter]
			fpz = z_right_mid[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
		
	#Middle-Middle
	screen = viz.worldtoscreen([fpx,0,fpz])
	f5 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f5.texture(viz.add(fixName))
	f5.setPosition([screen[0], screen[1], 0])
	f5.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f5)
	
	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_mid[fixation_counter] )**2 ) + ( ( pos[2] - z_right_mid[fixation_counter] )**2 ) )
		if ( (fix_dist < MidRange_Near) | (fix_dist > MidRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > MidRange_Near) and (fix_dist < MidRange_Far) ):
			fpx = x_right_over[fixation_counter]
			fpz = z_right_over[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
		
	#Mid-Right
	screen = viz.worldtoscreen([fpx,0,fpz])
	f6 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f6.texture(viz.add(fixName))
	f6.setPosition([screen[0], screen[1], 0])
	f6.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f6)

	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_over[fixation_counter] )**2 ) + ( ( pos[2] - z_right_over[fixation_counter] )**2 ) )
		if ( (fix_dist < NearRange_Near) | (fix_dist > NearRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > NearRange_Near) and (fix_dist < NearRange_Far) ):
			fpx = x_right_under[fixation_counter]
			fpz = z_right_under[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
		
	#Bottom-Left perspective correct
	screen = viz.worldtoscreen([fpx,0,fpz])
	f7 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f7.texture(viz.add(fixName))
	f7.setPosition([screen[0], screen[1], 0])
	f7.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f7)

	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_mid[fixation_counter] )**2 ) + ( ( pos[2] - z_right_mid[fixation_counter] )**2 ) )
		if ( (fix_dist < NearRange_Near) | (fix_dist > NearRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > NearRange_Near) and (fix_dist < NearRange_Far) ):
			fpx = x_right_mid[fixation_counter]
			fpz = z_right_mid[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
		
	#Bottom-Mid
	screen = viz.worldtoscreen([fpx,0,fpz])
	f8 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f8.texture(viz.add(fixName))
	f8.setPosition([screen[0], screen[1], 0])
	f8.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f8)
	
	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_over[fixation_counter] )**2 ) + ( ( pos[2] - z_right_over[fixation_counter] )**2 ) )
		if ( (fix_dist < NearRange_Near) | (fix_dist > NearRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > NearRange_Near) and (fix_dist < NearRange_Far) ):
			fpx = x_right_over[fixation_counter]
			fpz = z_right_over[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
	
	#Bottom-Right, perspective correct
	screen = viz.worldtoscreen([fpx,0,fpz])
	f9 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f9.texture(viz.add(fixName))
	print "screen9x: " + str(screen[0]) 
	print "screen9y: " + str(screen[1]) 
	if screen[0] > 1:
		print 'screen adjusted'
		screen[0] = .99
	print "screen9: " + str(screen)
	f9.setPosition([screen[0], screen[1], 0])
	f9.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f9)
	
#	f12 = viz.addTexQuad(parent=viz.WORLD,scene=viz.MainScene)
#	f12.texture(viz.add(fixName))
#	f12.setPosition([fpx, 0, fpz])
#	f12.scale(fixation_size, fixation_size, fixation_size)
	
	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_over[fixation_counter] )**2 ) + ( ( pos[2] - z_right_over[fixation_counter] )**2 ) )
		if ( (fix_dist < NearRange_Near) | (fix_dist > NearRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > NearRange_Near) and (fix_dist < NearRange_Far) ):
			fpx = x_right_under[fixation_counter]
			fpz = z_right_under[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
	
	#bottom left, optically correct	
	#same y as f8, same x as f1 
	f10 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f10.texture(viz.add(fixName))
	f8pos = f8.getPosition()
	f10y = f8pos[1]
	
	f1pos = f1.getPosition()
	f10x = f1pos[0]
	
	f10.setPosition([f10x, f10y, 0])
	f10.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f10)

	fixation_counter = 0
	while fixation_counter < 4712:
		fix_dist = mt.sqrt( ( ( pos[0] - x_right_under[fixation_counter] )**2 ) + ( ( pos[2] - z_right_under[fixation_counter] )**2 ) )
		if ( (fix_dist < NearRange_Near) | (fix_dist > NearRange_Far) ):
			fixation_counter += 1
			#compCount += 1
			continue
		elif ( (fix_dist > NearRange_Near) and (fix_dist < NearRange_Far) ):
			fpx = x_right_under[fixation_counter]
			fpz = z_right_under[fixation_counter]
			#print fix_dist
			break
	else:
		fixation_counter = 0
		fpx = 0
		fpz = 0
	
	#bottom right, optically correct	
	#same x as f3, same y as f8
	
	f11 = viz.addTexQuad(parent=viz.SCREEN, scene=viz.MainWindow)
	f11.texture(viz.add(fixName))
	f8pos = f8.getPosition()
	f11y = f8pos[1]
	
	f3pos = f3.getPosition()
	f11x = f3pos[0]
	
	f11.setPosition([f11x, f11y, 0])
	f11.scale(fixation_size, fixation_size, fixation_size)
	fixations.append(f11)
	
	return fixations