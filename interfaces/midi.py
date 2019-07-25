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

        self.type = message[0]//16
        self.channel = message[0]%16
        self.values = message[1:]


        if self.maintype() == 'NOTEON' and self.values[1] == 0:
            self.type == 8     # convert to NOTEOFF

        # MONITOR
        # if self.maintype() in ['NOTEON', 'NOTEOFF', 'CC']:
        #     print(self.maintype(), 'c'+str(self.subtype()+1), self.values)
        # else:   
        #     print(self.maintype(), self.subtype(), self.values)

        # Convert Note Value
        # if self.type == 'NOTEON' or self.type == 'NOTEOFF':
            # self.values[0] += 1     
    
    def maintype(self):
        return MIDITYPE[self.type]
    
    def systype(self):
        return MIDISYS[self.channel]

    def subtype(self):
        return  self.channel if (self.maintype() != 'SYSTEM') else self.systype()

    def note_abs(self):
        return (self.values[0]%12)

    def octave(self):
        return (self.values[0]//12)-2


class MidiInterface():
    def __init__(self, name, midiHandler):
        self.midiHandler = midiHandler

        self.midiIN = rtmidi.MidiIn()
        self.midiIN.open_virtual_port( name )
        self.midiIN.set_callback( self.midiHandler, data=None)
    
    def stop(self):
        self.midiHandler.stop()
        del self.midiIN


class MidiMonitor(object):
    def __init__(self):
        self._wallclock = time.time()
        
        print("-- MIDI MONITOR: started \n")


    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = MidiMessage(msg)
        
        # FILTERS
        # if mm.maintype() not in ['NOTEON', 'NOTEOFF', 'CC']: 
        #     return
        # if mm.maintype() == 'CC':
        #     if mm.values[0] not in [32, 1, 2, 7, 119, 120]: 
        #         return

        # MONITOR
        if mm.maintype() in ['NOTEON', 'NOTEOFF', 'CC']:
            print(mm.maintype(), 'c'+str(mm.subtype()+1), mm.values)
        else:   
            print(mm.maintype(), mm.subtype(), mm.values)

        

