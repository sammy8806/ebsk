#!/bin/env python3
import time
import math
import sys
import getopt
from threading import Thread

DEBUG=False

class Sensor:
    def __init__(self):
        self.value = -1
        self.file = None
        self.filename = ''

    def _open(self, name, mode, file = None):
        if not file or file.closed:
            if DEBUG:
                print("Opening %s" % name)
            return open(name, mode)

    def _close(self, file):
        #if DEBUG:
        #    print("Closing %s" % file.name)
        file.close()

    def _read(self, file, name):
        try:
            file = self._open(name, 'r')
        except FileNotFoundError:
            if DEBUG:
                print('File %s was not found' % name)
            return False

        value = file.readline()
        self._close(file)
        if DEBUG:
            print("READ : %s : %s" % (str(file.name),str(value)))
        return value

    def read(self):
        self.value = self._read(self.file, self.filename)
        return self.value

class Actor(Sensor):
    def _write(self, name, value):
        file = self._open(name, 'w')
        if DEBUG:
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
    def __init__(self):
        Actor.__init__(self)
        self.forceOff = False

    def writeForceOff(self, state=True):
        name = '/tmp/ebsk_force_off_' + self.filename.replace('/', '_')
        if state == True or state == 1:
            self._write(name, 1)
        else:
            self._write(name, 0)

    def checkForceOff(self):
        file = None
        name = '/tmp/ebsk_force_off_' + self.filename.replace('/','_')
        value = self._read(file, name)
        if value is False or value == "0":
            self.forceOff = False
            if DEBUG:
                print("[%s] Force OFF ===> NO" % name)
        elif value == "1":
            self.forceOff = True
            if DEBUG:
                print("[%s] Force OFF ===> YES" % name)
        return self.forceOff

    def readMax(self, file=None):
        if file is None:
            file = self.filename.replace('brightness', 'max_brightness')
        self.maxValue = int(self._read(None, file))
        return self.maxValue

    def write(self, value):
        if self.checkForceOff() is True:
           value = 0

        if value <= self.maxValue:
            return Actor.write(self, value)
        else:
            if DEBUG:
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
        self.maxValue = int(self.maxValue * 0.25);

ambient = LightSensor()
backlight = Backlight()
kb_backlight = KeyboardBacklight()

def trigger_action(type, args):
    if type == "acpi":
        if args == "lidclose":
            backlight.writeForceOff()
            kb_backlight.writeForceOff()
        elif args == "lidopen":
            backlight.writeForceOff(False)
            kb_backlight.writeForceOff(False)

def thread_bl():
    print('Starting Backlight Thread')
    while True:
        backlight.fade(
            math.ceil((backlight.maxValue / 255) * (int(ambient.read().split(',')[0][1:]) + 12)),
            math.ceil(backlight.maxValue/(1024/3))
        )
        time.sleep(0.3)

def thread_kbbl():
    print('Starting Keyboard-Backlight Thread')
    while True:
        # an extra if here because the ambient don't need to be read if it's forceOff
        if kb_backlight.forceOff == False:
            kb_backlight.fade(
                math.ceil((kb_backlight.maxValue / 255) * (255 - int(ambient.read().split(',')[0][1:]))),
                math.ceil(kb_backlight.maxValue / 16)
            )
        else:
            kb_backlight.checkForceOff()
        time.sleep(0.3)

def main(argv):
   try:
      opts, args = getopt.getopt(argv,"a::",["acpi="])
   except getopt.GetoptError:
      print('test.py --acpi=<acpi-action>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('test.py --acpi=<acpi-action>')
         sys.exit()
      elif opt in ("--acpi"):
         trigger_action(type="acpi", args=arg)
   if len(opts) == 0:
      t_bl = Thread(target=thread_bl)
      t_kbbl = Thread(target=thread_kbbl)

      t_bl.start()
      t_kbbl.start()

      while True:
        time.sleep(10)

if __name__ == '__main__':
    main(sys.argv[1:])

# Some useless code here
#while True:
    #print((int(ambient.read().split(',')[0][1:]) + 10))
    #print(backlight.maxValue / 255)
    #print((backlight.maxValue / 255) * (int(ambient.read().split(',')[0][1:]) + 10))
#    time.sleep(10)

#for x in range(0,backlight.maxValue, math.ceil(backlight.maxValue/1024)):
#    backlight.write(x)
#    print("Setting BL to %s" % str(x) )
#    time.sleep(0.01)

#for x in range(0,kb_backlight.maxValue, math.ceil(backlight.maxValue/32)):
#    kb_backlight.write(x)
#    print("Setting KBBL to %s" % str(x) )
#    time.sleep(0.05)
