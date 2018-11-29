from phue import Bridge
import random

b = Bridge("192.168.1.33")  # Enter bridge IP here. Change depending on local bridge IP.

keyColors = {}
# If running for the first time, press button on bridge and run with b.connect() uncommented
# b.connect()

lights = b.get_light_objects()


def setLightState(id, state):       # True=on, False=off
  lights[id].on = state


def setBrightness(id, brightness):      # Range 0-254
  lights[id].brightness = brightness

def incBrightness(id):
    if lights[id].brightness <= 229:
        lights[id].brightness += 25
    else:
        print("Brightness is already set to maximum")

def decBrightness(id):
    if lights[id].brightness >= 25:
        lights[id].brightness += 25
    else:
        print("Brightness is already set to minimum")


def setColor(id, x, y):                 # Range x: 0.0-1.0, y: 0.0-1.0
  lights[id].xy = [x, y]

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
