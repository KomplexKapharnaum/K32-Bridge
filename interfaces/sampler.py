from interfaces import midi
import paho.mqtt.client as mqtt
import time

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
        print(f"-- SAMPLER: connected to MQTT broker at {broker}")

    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)

        if mm.maintype() == 'SYSTEM':
            self.mqttc.publish('sampler/sys', payload=mm.payload_midivalues(), qos=1, retain=False)
            print('sampler/sys', mm.payload_midivalues(), mm.maintype())
        else:
            self.mqttc.publish('sampler/c'+str(mm.channel+1), payload=mm.payload_midivalues(), qos=1, retain=False)
            print('sampler/c'+str(mm.channel+1), mm.payload_midivalues(), mm.maintype())