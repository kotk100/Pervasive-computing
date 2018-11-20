# live_scene_and_gaze.py : A demo for video streaming and synchronized gaze
#
# Copyright (C) 2018  Davide De Tommaso
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>

import cv2
import numpy as np
import sys
import time
from queue import Queue
from queue import Empty
from TobiiProGlasses2_PyCtrl.tobiiglassesctrl.tobiiglassesctrl import TobiiGlassesController

# Create queue for receiving detected blinks
detected_blinks = Queue()

# Connect to Tobii glasses
tobiiglasses = TobiiGlassesController(detected_blinks, "192.168.71.50%17")
# Might be different on a different computer, call function without parameter to go through all interfaces (slow)
# "fe80::76fe:48ff:fe34:595f%10" Wired
# "192.168.71.50%17"             Wireless

# Print info from glasses
print(tobiiglasses.get_battery_info())
print(tobiiglasses.get_storage_info())

if tobiiglasses.is_recording():
	rec_id = tobiiglasses.get_current_recording_id()
	tobiiglasses.stop_recording(rec_id)

project_name = input("Please insert the project's name: ")
project_id = tobiiglasses.create_project(project_name)

participant_name = input("Please insert the participant's name: ")
participant_id = tobiiglasses.create_participant(project_id, participant_name)

calibration_id = tobiiglasses.create_calibration(project_id, participant_id)

input("Put the calibration marker in front of the user, then press enter to calibrate")
tobiiglasses.start_calibration(calibration_id)

res = tobiiglasses.wait_until_calibration_is_done(calibration_id)

if res is False:
	print("Calibration failed!")
	exit(1)
print("Calibration FINISHED!")

tobiiglasses.start_streaming()
video_freq = tobiiglasses.get_video_freq()
print(video_freq)

frame_duration = 1000.0 / float(video_freq)  # frame duration in ms

input("Press ENTER to start the video scene")

# Only works on wireless/ipv4 for some reason
cap = cv2.VideoCapture("rtsp://%s:8554/live/scene" % tobiiglasses.get_address())
# cap = cv2.VideoCapture("rtsp://184.72.239.149:554/vod/mp4:BigBuckBunny_175k.mov")

# Check if camera opened successfully
if (cap.isOpened() == False):
	print("Error opening video stream or file")

# Need to start a recording if we want to recieve pts packets to be able to sync tracking data with video
# recording_id = tobiiglasses.create_recording(participant_id)
# print("Important! The recording will be stored in the SD folder projects/%s/recordings/%s" % (project_id, recording_id))
# tobiiglasses.start_recording(recording_id)
# tobiiglasses.send_event("start_recording", "Start of the recording ")

# Read until video is completed

while (cap.isOpened()):
	# Capture frame-by-frame
	ret, frame = cap.read()

	# Get any blinks that were detected between the frames, only keep the last one
	while True:
		try:
			blink = detected_blinks.get_nowait()
			# Number of frames to display the blink
			blink_display_frames = 7
		except Empty:
			break

	if ret == True:

		height, width = frame.shape[:2]
		data_gp = tobiiglasses.get_data()['gp']
		data_pts = tobiiglasses.get_data()['pts']  # TODO not receiving PTS sync packets for some reason
		offset = data_gp['ts'] / 1000000.0 - data_pts['ts'] / 1000000.0  # offset in ms

		# Seconds after video start, used for sync
		pst = cap.get(cv2.CAP_PROP_POS_MSEC)
		# print(offset)

		# if offset > 0.0 and offset <= frame_duration:
		# Display detected blinks by filling the appropriate part of circle for blink_display_frames number of frames
		if 'blink' in locals():
			if blink == 'both':
				cv2.circle(frame, (int(data_gp['gp'][0] * width), int(data_gp['gp'][1] * height)), 30, (0, 0, 255), -1)
			elif blink == 'left':
				cv2.ellipse(frame, (int(data_gp['gp'][0] * width), int(data_gp['gp'][1] * height)), (30, 30), 0, 90, 270, (0, 0, 255), -1)
			elif blink == 'right':
				cv2.ellipse(frame, (int(data_gp['gp'][0] * width), int(data_gp['gp'][1] * height)), (30, 30), 0, -90, 90, (0, 0, 255), -1)
			blink_display_frames -= 1
			if blink_display_frames < 1:
				blink = ''

		cv2.circle(frame, (int(data_gp['gp'][0] * width), int(data_gp['gp'][1] * height)), 30, (0, 0, 255), 2)
		# Display the resulting frame
		cv2.imshow('Tobii Pro Glasses 2 - Live Scene', frame)

		# Press Q on keyboard to  exit
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	# Break the loop
	else:
		break

# When everything done, release the video capture object
cap.release()

# Closes all the frames
cv2.destroyAllWindows()

# tobiiglasses.send_event("stop_recording", "Stop of the recording " + str(recording_id))
# tobiiglasses.stop_recording(recording_id)

tobiiglasses.stop_streaming()
tobiiglasses.close()
