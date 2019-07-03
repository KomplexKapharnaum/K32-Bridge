from interfaces import midi
import paho.mqtt.client as mqtt
import time

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
        self.payload = [ bytearray(FIXTURE_SIZE) ]*16

    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)
        
        
        if mm.maintype() == 'NOTEON' or mm.maintype() == 'CC':

            # NOTEON 0-15 or CC 20-35
            note = mm.values[0]
            if mm.maintype() == 'CC':
                note -= 20
            if note >= 0 and note < FIXTURE_SIZE:
                self.payload[mm.channel][note] = mm.values[1]*2
                self.mqttc.publish('leds/c'+str(mm.channel+1), payload=self.payload[mm.channel], qos=1, retain=False)
                print('leds/c'+str(mm.channel+1), list(self.payload[mm.channel]))

            # CC 120 / 123 == ALL OFF
            if mm.maintype() == 'CC' and (mm.values[0] == 120 or mm.values[0] == 123):
                self.payload = [ bytearray(FIXTURE_SIZE) ]*16
                self.mqttc.publish('leds/c'+str(mm.channel+1), payload=self.payload[mm.channel], qos=1, retain=False)
                print('leds/c'+str(mm.channel+1), list(self.payload[mm.channel]))
            
