import rtmidi
import time
import json

import paho.mqtt.client as mqtt

#
# MIDI
#
MIDITYPE = {
                8: 'NOTEOFF', 
                9: 'NOTEON',
                10: 'AFTERTOUCH',
                11: 'CC',
                12: 'PC',
                13: 'PRESSURE',
                14: 'PITCHBEND',
                15: 'SYSTEM'
            }

MIDISYS = {
                0: 'SYSEX', 
                1: 'MTC',
                2: 'SONGPOS',
                3: 'SONGSEL',
                4: 'UNDEFINED1',
                5: 'UNDEFINED2',
                6: 'TUNE',
                7: 'SYSEXEND',
                8: 'CLOCK',
                9: 'UNDEFINED3',
                10: 'START',
                11: 'CONTINUE',
                12: 'STOP',
                13: 'UNDEFINED4',
                14: 'SENSING',
                15: 'RESET'
            }

class MidiMessage():
    def __init__(self, message):
        self.message = message
        mChunk1 = bin(message[0])[2:6]
        mChunk2 = bin(message[0])[6:] 

        self.type = message[0]//16
        self.channel = message[0]%16

        self.values = message[1:]

        if self.maintype() == 'NOTEON' and self.values[1] == 0:
            self.type == 8     # convert to NOTEOFF

        # Convert Note Value
        # if self.type == 'NOTEON' or self.type == 'NOTEOFF':
            # self.values[0] += 1     
    
    def maintype(self):
        return MIDITYPE[self.type]
    
    def systype(self):
        return MIDISYS[self.channel]

    def payload_json(self):
        p = json.dumps({"event": self.type, "values": self.values}, sort_keys=True)
        return p

    def payload_raw(self):
        return '-'.join([str(v).zfill(3) for v in self.message[:3] ])



class MidiToMQTTHandler(object):
    def __init__(self, mqttc):
        self._wallclock = time.time()
        self._mqttc = mqttc

    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = MidiMessage(msg)

        if mm.maintype() == 'SYSTEM':
            self._mqttc.publish('midi/sys', payload=mm.payload_raw(), qos=1, retain=True)
            print(mm.maintype(), mm.systype(), mm.values, mm.payload_raw())
        else:
            self._mqttc.publish('midi/c'+str(mm.channel+1), payload=mm.payload_raw(), qos=1, retain=True)
            print(mm.maintype(), mm.channel, mm.values, mm.payload_raw())


class MidiInterface():
    def __init__(self, name, addr):
        self.name = name

        self.mqttc = mqtt.Client()
        self.mqttc.connect(addr)
        self.mqttc.loop_start()

        self.midiIN = rtmidi.MidiIn()
        self.midiIN.open_virtual_port(name)
        self.midiIN.set_callback( MidiToMQTTHandler(self.mqttc), data=None)
    
    def stop(self):
        self.mqttc.loop_stop(True)
        del self.midiIN
