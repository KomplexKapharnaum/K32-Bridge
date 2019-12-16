from interfaces import midi
import paho.mqtt.client as mqtt
import time
from threading import Thread, Event

FIXTURE_SIZE = 16
FIXTURE_SIZEDMX = 12*4

class UpdateLeds(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent

    def run(self):
        while not self.parent.stopFlag.wait(0.01):
            self.parent.sendAll()

#
#  MIDI Handler (PUBLIC)
#
class Midi2MQTT(object):
    def __init__(self, broker):
        self._wallclock = time.time()
        
        # MQTT Client
        self.mqttc = mqtt.Client()
        self.mqttc.connect(broker)
        self.mqttc.loop_start()
        print(f"-- LEDS: sending to broker at {broker}\n")

        # Internal state
        self.payload = [0]*16
        self.dirty = [False]*16
        self.clear()

        # Push state
        self.stopFlag = Event()
        self.thread = UpdateLeds(self)
        self.thread.start()


    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)        
        
        if mm.maintype() == 'NOTEON' or mm.maintype() == 'CC' or mm.maintype() == 'NOTEOFF':

            # NOTEON 0-15 or CC 20-35
            note = mm.values[0]
            if mm.maintype() == 'CC':
                note -= 20    
            if note >= 0:
                if (note < FIXTURE_SIZE) or (mm._channel == 15 and note < FIXTURE_SIZEDMX):
                    if mm.maintype() == 'NOTEOFF': 
                        self.payload[mm._channel][note] = 0
                    else: 
                        self.payload[mm._channel][note] = mm.values[1]*2
                    # self.send(mm._channel)
                    self.dirty[mm._channel] = True

            # CC 119 / 120 / 123 == ALL OFF
            if mm.maintype() == 'CC' and (mm.values[0] == 120 or mm.values[0] == 119 or mm.values[0] == 123):
                self.clear()
                # self.send(mm._channel)   
                self.dirty[mm._channel] = True


    def stop(self):
        self.stopFlag.set()
        self.thread.join()
            
    def clear(self):
        for i in range(15):
            self.payload[i] = bytearray(FIXTURE_SIZE)
        self.payload[15] = bytearray(FIXTURE_SIZEDMX)

    def send(self, chan):
        self.mqttc.publish('k32/c'+str(chan+1)+'/leds', payload=self.payload[chan], qos=1, retain=False)
        print('k32/c'+str(chan+1)+'/leds', list(self.payload[chan]))

    def sendAll(self):
        for i in range(16):
            if self.dirty[i]:
                self.dirty[i] = False
                self.mqttc.publish('k32/c'+str(i+1)+'/leds', payload=self.payload[i], qos=1, retain=False)
                print('k32/c'+str(i+1)+'/leds', list(self.payload[i]))