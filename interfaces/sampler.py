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
        
        # FILTERS
        if mm.maintype() not in ['NOTEON', 'NOTEOFF', 'CC']: 
            print('discarded')
            return
        if mm.maintype() == 'CC':
            if mm.values[0] not in [1, 2, 7, 119, 120]: 
                print('discarded')
                return

        
        ## QOS
        # VOLUME CC 7
        if mm.maintype() == 'CC' and mm.values[0] == 7:
            qos = 0
        # OTHERS
        else:
            qos = 1

        # PAYLOAD
        payload = '-'.join([str(v).zfill(3) for v in mm.message[:3] ])

        if mm.channel+1 == 16:
            self.mqttc.publish('k32/all/midi', payload=payload, qos=qos, retain=False)
            print('k32/all/midi', payload, mm.maintype())
        else:
            self.mqttc.publish('k32/c'+str(mm.channel+1)+'/midi', payload=payload, qos=qos, retain=False)
            print('k32/c'+str(mm.channel+1)+'/midi', payload, mm.maintype())