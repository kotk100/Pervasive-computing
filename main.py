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
from TobiiProGlasses2_PyCtrl.tobiiglassesctrl.tobiiglassesctrl import TobiiGlassesController

# Connect to Tobii glasses
tobiiglasses = TobiiGlassesController("192.168.71.50%17")
#"fe80::76fe:48ff:fe34:595f%10"
#"192.168.71.50%17"            fe80::2c20:15ff:fea8:3b01

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


tobiiglasses.start_streaming()
video_freq = tobiiglasses.get_video_freq()
print(video_freq)

frame_duration = 1000.0/float(video_freq) #frame duration in ms

input("Press ENTER to start the video scene")

cap = cv2.VideoCapture("rtsp://%s:8554/live/scene" % tobiiglasses.get_address())
#cap = cv2.VideoCapture("rtsp://184.72.239.149:554/vod/mp4:BigBuckBunny_175k.mov")

# Check if camera opened successfully
if (cap.isOpened()== False):
    print("Error opening video stream or file")

# Read until video is completed
while(cap.isOpened()):
  # Capture frame-by-frame
  ret, frame = cap.read()
  if ret == True:

    height, width = frame.shape[:2]
    data_gp  = tobiiglasses.get_data()['gp']
    data_pts = tobiiglasses.get_data()['pts']
    offset = data_gp['ts']/1000000.0 - data_pts['ts']/1000000.0
    if offset > 0.0 and offset <= frame_duration:
        cv2.circle(frame,(int(data_gp['gp'][0]*width),int(data_gp['gp'][1]*height)), 30, (0,0,255), 2)
    # Display the resulting frame
    cv2.imshow('Tobii Pro Glasses 2 - Live Scene',frame)

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

tobiiglasses.stop_streaming()
tobiiglasses.close()