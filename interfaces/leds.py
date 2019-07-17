from interfaces import midi
import paho.mqtt.client as mqtt
import time
import threading

FIXTURE_SIZE = 16

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
        print(f"-- LEDS: connected to MQTT broker at {broker}")

        # Internal state
        self.payload = [0]*16
        self.clear()

    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)
        
        
        if mm.maintype() == 'NOTEON' or mm.maintype() == 'CC' or mm.maintype() == 'NOTEOFF':

            # NOTEON 0-15 or CC 20-35
            note = mm.values[0]
            if mm.maintype() == 'CC':
                note -= 20    
            if note >= 0 and note < FIXTURE_SIZE:
                if mm.maintype() == 'NOTEOFF': 
                    self.payload[mm.channel][note] = 0
                else: 
                    self.payload[mm.channel][note] = mm.values[1]*2
                self.send(mm.channel)

            # CC 120 / 123 == ALL OFF
            if mm.maintype() == 'CC' and (mm.values[0] == 120 or mm.values[0] == 123):
                self.clear()
                self.send(mm.channel)   

    def stop(self):
        self.run = False
        self.thread.join()
            
    def clear(self):
        for i in range(16):
            self.payload[i] = bytearray(FIXTURE_SIZE)

    def send(self, channel):
        self.mqttc.publish('k32/c'+str(channel+1)+'/leds/pyramid', payload=self.payload[channel], qos=1, retain=False)
        print('k32/c'+str(channel+1)+'/leds/pyramid', list(self.payload[channel]))