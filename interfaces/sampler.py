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
        payload = '-'.join([str(v).zfill(3) for v in self.message[:3] ])

        self.mqttc.publish('k32/c'+str(mm.channel+1)+'/sampler', payload=payload, qos=1, retain=False)
        print('k32/c'+str(mm.channel+1)+'/sampler', payload, mm.maintype())