import rtmidi
import time

#
# MIDI
#
MIDITYPE = {
                '1000': 'NOTEOFF', 
                '1001': 'NOTEON',
                '1010': 'AFTERTOUCH',
                '1011': 'CC',
                '1100': 'PC',
                '1101': 'PRESSURE',
                '1110': 'PITCHBEND',
                '1011': 'MODE',
                '1111': 'SYSCOM'
            }

MIDISYS = {
                '0000': 'SYSEX', 
                '0001': 'MTC',
                '0010': 'SONGPOS',
                '0011': 'SONGSEL',
                '0110': 'TUNE',
                '0111': 'SYSEXEND',
                '1000': 'CLOCK',
                '1010': 'START',
                '1011': 'CONTINUE',
                '1100': 'STOP',
                '1110': 'SENSING',
                '1111': 'RESET'
            }

class MidiMessage():
    def __init__(self, message):
        self.message = message
        mChunk1 = bin(message[0])[2:6]
        mChunk2 = bin(message[0])[6:] 

        self.type = MIDITYPE[mChunk1]
        if self.type == 'SYSCOM': 
            self.type = MIDISYS[mChunk2]
            self.channel = 0
        else: 
            self.channel = int(mChunk2, 2)+1

        self.values = message[1:]

        # Convert NOTEON velocity O to NOTEOFF
        if self.type == 'NOTEON' and self.values[1] == 0:
            self.type == 'NOTEOFF'

        # Convert Note Value
        if self.type == 'NOTEON' or self.type == 'NOTEOFF':
            self.values[0] += 1     
    
    def payload(self):
        return '-'.join([str(v).zfill(3) for v in self.values])



class MidiToMQTTHandler(object):
    def __init__(self, mqttc):
        self._wallclock = time.time()
        self._mqttc = mqttc

    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = MidiMessage(msg)

        if mm.type == 'NOTEON': 
            self._mqttc.publish('midi/c'+str(mm.channel)+'/noteon', payload=mm.payload(), qos=1, retain=True)
        
        elif mm.type == 'NOTEOFF':
            self._mqttc.publish('midi/c'+str(mm.channel)+'/noteoff', payload=mm.payload(), qos=1, retain=True)
        
        
        print(mm.type, mm.channel, mm.values)


class MidiInterface():
    def __init__(self, name, mqttc):
        self.name = name
        self.midiIN = rtmidi.MidiIn()
        self.midiIN.open_virtual_port(name)
        self.midiIN.set_callback( MidiToMQTTHandler(mqttc), data=None)

