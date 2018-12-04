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
from ColorRecognition import getColorFromImage

import hue_python_module.python_hue_module as hue
from TobiiProGlasses2_PyCtrl.tobiiglassesctrl.tobiiglassesctrl import TobiiGlassesController

NUMBER_FRAMES_BLINK = 7
NUMBER_OF_LIGHTS = 2
LIGHT_COLORS = [[0, 0, 255], [0, 255, 0], [255, 0, 0]]
LIGHT_NAME = ["blue", "green", "red"]
DEBUG = False
BLINK_CONTR_DURATION = 0.4

# Turn all lights off
for light in range(NUMBER_OF_LIGHTS):
	hue.setLightState(light, False)

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

#project_name = input("Please insert the project's name: ")
project_id = tobiiglasses.create_project("")

#participant_name = input("Please insert the participant's name: ")
participant_id = tobiiglasses.create_participant(project_id, "")

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

# input("Press ENTER to start the video scene")

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


# Turn all lights on
for light in range(NUMBER_OF_LIGHTS):
	hue.setLightState(light, True)
	hue.setBrightness(light, 100)
	hue.setColor(light, [255, 255, 255])

# Read until video is completed
counter = 0
while (cap.isOpened()):
	# Capture frame-by-frame
	cap.grab()

	try:
		blink = detected_blinks.get_nowait()
		data_gp = blink['gp']

		if blink['eye'] == 'right' and blink['duration'] > BLINK_CONTR_DURATION:
			print("Detecting light bulb...")
			for light in range(NUMBER_OF_LIGHTS):
				hue.saveLightState(light)
				hue.setLightState(light, True)
				hue.setColor(light, LIGHT_COLORS[light])
				hue.setBrightness(light, 155)

			before = time.time()
			while time.time() - before < 1.0:
				cap.grab()

			ret, frame = cap.read()

			for light in range(NUMBER_OF_LIGHTS):
				hue.loadLightState(light)

			height, width = frame.shape[:2]
			x = int(data_gp[0] * width)
			y = int(data_gp[1] * height)

			x1 = max(0, x - 150)
			x2 = min(width, x + 150)
			y1 = max(0, y - 150)
			y2 = min(height, y + 150)
			light = frame[y1:y2, x1:x2]
			if DEBUG:
				cv2.imshow(str(counter), light)
			#cv2.imwrite("ColorRecognition/TestImages/" + str(counter) + ".jpg", light)
			image = getColorFromImage.ImageProcessor(light)
			value = image.get_avg_pixel_color()
			print(value)

			cv2.rectangle(light, (0, 0), (30, 30), tuple([int(x) for x in value[0]]), -1)
			cv2.imwrite("./Test/" + str(counter) + ".jpg", light)
			counter += 1

			if value[0] == [0, 0, 0]:
				continue

			selected_light = 0
			for c in LIGHT_NAME:
				if c == value[1]:
					break;
				selected_light += 1

			if selected_light < NUMBER_OF_LIGHTS:
				print("Selected light: " + value[1])
				# Wait for next blink to occur in 1 seconds
				while True:
					try:
						cont_blink = detected_blinks.get_nowait()

						if cont_blink["eye"] == "both":
							hue.toggleLightState(selected_light)
						elif cont_blink["eye"] == "right":
							hue.loopBrightness(selected_light)
						elif cont_blink["eye"] == "left" and cont_blink['duration'] < BLINK_CONTR_DURATION:
							hue.loopColor(selected_light)
						else:
							print("Controlling " + value[1] + " bulb done.")
							break

					except Empty:
						pass
	except Empty:
		pass



	# 	# Get blink gaze point if detected and process blink
	# 	if ('blink' in locals()) and  ((not DEBUG) or (blink_display_frames == NUMBER_FRAMES_BLINK)):
	# 		data_gp = blink['gp']
	#
	# 		if blink['eye'] == 'right':
	# 			print("Detecting light bulb...")
	# 			for light in range(NUMBER_OF_LIGHTS):
	# 				hue.saveLightState(light)
	# 				hue.setLightState(light, True)
	# 				hue.setColor(light, LIGHT_COLORS[light])
	# 				hue.setBrightness(light, 155)
	#
	# 			before = time.time()
	# 			while time.time() - before < 0.5:
	# 				ret, frame = cap.read()
	#
	# 			for light in range(NUMBER_OF_LIGHTS):
	# 				hue.loadLightState(light)
	#
	# 			x = int(data_gp[0] * width)
	# 			y = int(data_gp[1] * height)
	#
	# 			x1 = max(0, x - 150)
	# 			x2 = min(width, x + 150)
	# 			y1 = max(0, y - 150)
	# 			y2 = min(height, y + 150)
	# 			light = frame[y1:y2, x1:x2]
	# 			if DEBUG:
	# 				cv2.imshow(str(counter), light)
	# 			#cv2.imwrite("ColorRecognition/TestImages/" + str(counter) + ".jpg", light)
	# 			image = getColorFromImage.ImageProcessor(light)
	# 			value = image.get_avg_pixel_color()
	# 			print(value)
	#
	# 			if value[0] == [0, 0, 0]:
	# 				continue
	#
	#
	# 			if DEBUG:
	# 				print(value)
	# 				cv2.rectangle(light, (0, 0), (30, 30), tuple([int(x) for x in value[0]]), -1)
	# 				cv2.imshow(str(counter), light)
	# 				counter += 1
	#
	# 			selected_light = 0
	# 			for c in LIGHT_NAME:
	# 				if c == value[1]:
	# 					break;
	# 				selected_light += 1
	#
	# 			if selected_light < NUMBER_OF_LIGHTS:
	# 				print("Selected light: " + value[1])
	# 				# Wait for next blink to occur in 2 seconds
	# 				while True:
	# 					try:
	# 						cont_blink = detected_blinks.get(True, 2.0)
	#
	# 						if cont_blink["eye"] == "both":
	# 							hue.toggleLightState(selected_light)
	# 						elif cont_blink["eye"] == "right":
	# 							hue.incBrightness(selected_light)
	# 						elif cont_blink["eye"] == "left":
	# 							hue.decBrightness(selected_light)
	# 					except Empty:
	# 						print("Controlling " + value[1] + " bulb done.")
	# 						break
	#
	# 	else:
	# 		data_gp = tobiiglasses.get_data()['gp']['gp']
	#
	# 	#data_pts = tobiiglasses.get_data()['pts']  # TODO not receiving PTS sync packets for some reason
	#
	# 	# Seconds after video start, used for sync
	# 	#pst = cap.get(cv2.CAP_PROP_POS_MSEC)
	#
	# 	# if offset > 0.0 and offset <= frame_duration:
	# 	# Display detected blinks by filling the appropriate part of circle for blink_display_frames number of frames
	# 	if DEBUG == True:
	# 		if 'blink' in locals():
	# 			if blink['eye'] == 'both':
	# 				cv2.circle(frame, (int(data_gp[0] * width), int(data_gp[1] * height)), 30, (0, 0, 255), -1)
	# 			elif blink['eye'] == 'left':
	# 				cv2.ellipse(frame, (int(data_gp[0] * width), int(data_gp[1] * height)), (30, 30), 0, 90, 270, (0, 0, 255), -1)
	# 			elif blink['eye'] == 'right':
	# 				cv2.ellipse(frame, (int(data_gp[0] * width), int(data_gp[1] * height)), (30, 30), 0, -90, 90, (0, 0, 255), -1)
	# 			blink_display_frames -= 1
	# 			if blink_display_frames < 1:
	# 				del blink
	#
	# 		cv2.circle(frame, (int(data_gp[0] * width), int(data_gp[1] * height)), 30, (0, 0, 255), 2)
	# 		# Display the resulting frame
	# 		cv2.imshow('Tobii Pro Glasses 2 - Live Scene', frame)
	#
	# 		# Press Q on keyboard to  exit
	# 		if cv2.waitKey(1) & 0xFF == ord('q'):
	# 			break
	#
	# # Break the loop
	#else:
	#	break

# When everything done, release the video capture object
cap.release()

# Closes all the frames
cv2.destroyAllWindows()

# tobiiglasses.send_event("stop_recording", "Stop of the recording " + str(recording_id))
# tobiiglasses.stop_recording(recording_id)

tobiiglasses.stop_streaming()
tobiiglasses.close()
