import python_hue_module
import time

t = python_hue_module

t.setLightState(0, True)
t.setRed(0)
time.sleep(2)
t.setGreen(0)
time.sleep(2)
t.setBlue(0)
time.sleep(2)
t.setLightState(0, False)

