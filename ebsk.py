#!/bin/env python3
import time
import math

DEBUG=True

class Sensor:
    def __init__(self):
        self.value = -1
        self.file = None
        self.filename = ''

    def _open(self, name, mode, file = None):
        if not file or file.closed:
            #if DEBUG:
            #    print("Opening %s" % name)
            return open(name, mode)

    def _close(self, file):
        #if DEBUG:
        #    print("Closing %s" % file.name)
        file.close()

    def _read(self, file, name):
        file = self._open(name, 'r')
        value = file.readline()
        self._close(file)
        print("READ : %s : %s" % (str(file.name),str(value)))
        return value

    def read(self):
        self.value = self._read(self.file, self.filename)
        return self.value

class Actor(Sensor):
    def _write(self, name, value):
        file = self._open(name, 'w')
        print("WRITE : %s : %s" % (str(file.name),str(value)))
        value = file.write(str(value))
        self._close(file)
        return value

    def write(self, value):
        self.value = self._write(self.filename, value)
        return self.value

class LightSensor(Sensor):
    def __init__(self):
        Sensor.__init__(self)
        self.filename = '/sys/devices/platform/applesmc.768/light'

class LightActor(Actor):
    def readMax(self, file=None):
        if file is None:
            file = self.filename.replace('brightness', 'max_brightness')
        self.maxValue = int(self._read(None, file))
        return self.maxValue

    def write(self, value):
        if value <= self.maxValue:
            return Actor.write(self, value)
        else:
            print("Value %s is out of actor-limits" % str(value))
            return self.write(self.maxValue)

    def fade(self, targetValue, valueStep, timeStep=0.01):
        actualValue = int(self.read())
        if targetValue < actualValue:
            valueStep = valueStep * (-1)
        elif targetValue == actualValue:
            return

        for x in range(int(self.read()), targetValue, valueStep):
            self.write(x)
            time.sleep(timeStep)

class Backlight(LightActor):
    def __init__(self):
        LightActor.__init__(self)
        self.filename = '/sys/class/backlight/intel_backlight/brightness'
        self.readMax()

class KeyboardBacklight(LightActor):
    def __init__(self):
        LightActor.__init__(self)
        self.filename = '/sys/class/leds/smc::kbd_backlight/brightness'
        self.readMax()

ambient = LightSensor()
backlight = Backlight()
kb_backlight = KeyboardBacklight()

while True:
    #print((int(ambient.read().split(',')[0][1:]) + 10))
    #print(backlight.maxValue / 255)
    #print((backlight.maxValue / 255) * (int(ambient.read().split(',')[0][1:]) + 10))
    backlight.fade(
        math.ceil((backlight.maxValue / 255) * (int(ambient.read().split(',')[0][1:]) + 13)),
        math.ceil(backlight.maxValue/512)
    )
    kb_backlight.fade(
        math.ceil((kb_backlight.maxValue / 255) * (255 - int(ambient.read().split(',')[0][1:]))),
        math.ceil(kb_backlight.maxValue / 32)
    )

    time.sleep(2)

for x in range(0,backlight.maxValue, math.ceil(backlight.maxValue/1024)):
    backlight.write(x)
    print("Setting BL to %s" % str(x) )
    time.sleep(0.01)


for x in range(0,kb_backlight.maxValue, math.ceil(backlight.maxValue/32)):
    kb_backlight.write(x)
    print("Setting KBBL to %s" % str(x) )
    time.sleep(0.05)
