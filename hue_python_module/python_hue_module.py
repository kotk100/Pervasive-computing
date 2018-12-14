from hue_python_module.phue import Bridge
from rgbxy import Converter
import random


b = Bridge("192.168.1.151")  # Enter bridge IP here. Change depending on local bridge IP.
conv = Converter()

keyColors = {}
# If running for the first time, press button on bridge and run with b.connect() uncommented
# b.connect()

lights = b.get_light_objects()
print(lights)

light_states = {}

def saveLightState(id):
    light_states[id] = {}
    light_states[id]["state"] = lights[id].on
    light_states[id]["brightness"] = lights[id].brightness
    light_states[id]["color"] = lights[id].xy

def loadLightState(id):
    lights[id].on = light_states[id]["state"]
    lights[id].brightness = light_states[id]["brightness"]
    lights[id].xy = light_states[id]["color"]

def setLightState(id, state):       # True=on, False=off
    lights[id].on = state

def toggleLightState(id):
    lights[id].on = not lights[id].on

def setBrightness(id, brightness):      # Range 0-254
  lights[id].brightness = brightness

def loopBrightness(id):
    if lights[id].brightness <= 253:
        br = lights[id].brightness + 25
        if br > 254:
            br = 254
        lights[id].brightness = br
    else:
        lights[id].brightness = 10

def loopColor(id):
    if lights[id].hue <= 65534:
        br = lights[id].hue + 3000
        if br > 65535:
            br = 65535
        lights[id].hue = br
    else:
        lights[id].hue = 1

def incBrightness(id):
    if lights[id].brightness <= 229:
        lights[id].brightness += 25
    else:
        print("Brightness is already set to maximum")

def decBrightness(id):
    if lights[id].brightness >= 25:
        lights[id].brightness -= 25
    else:
        print("Brightness is already set to minimum")


def setColor(id, rgb):
    #lights[id].transitiontime = 0
    lights[id].xy = conv.rgb_to_xy(rgb[0], rgb[1], rgb[2])

def setRed(id):
    lights[id].xy = [0.7, 0.27]

def setGreen(id):
    lights[id].xy = [0.38, 0.48]

def setBlue(id):
    lights[id].xy = [0.17, 0.02]

#def changeAll():
#  for light in lights:
#      x = random.random()
#      y = random.random()
#      keyColors[b.name] = x, y
#      light.xy = [x, y]
#      print(keyColors)

def setLightsRGB():
    RGB = {"Red": "", "Green": "", "Blue": ""}
    for light in lights:
        color = random.randint(1, 4)
        if color == 0:
            RGB["Red"] += light.name
            setRed(light)
        elif color == 1:
            RGB["Green"] += light.name
            setGreen(light)
        else:
            RGB["Blue"] += light.name
            setBlue(light)
    print(RGB)
