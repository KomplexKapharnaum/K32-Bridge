import time, signal, sys, os
import paho.mqtt.client as mqtt
import socketio
from interfaces import midi
from interfaces import xlsreader


#
#  SOCKETIO link
#
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print(f"-- SOCKETIO: connected to online server")
    sio.emit('command', 'ok')

#
#  MIDI Handler (PUBLIC)
#
class Midi2SocketIO(object):
    def __init__(self, sioURL, xls):
        self._wallclock = time.time()

        try:
            sio.connect(sioURL)
        except:
            print(f"-- SOCKETIO: ERROR connecting remote server at {sioURL} \n\t\tverify internet connection and restart")

        # XLS Read and Parse
        self.xls = xls

        print("")


    def __call__(self, event, data=None):
        mididata, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(mididata)

        msg = 'niet'

        if mm.maintype() == 'NOTEON':
            txt = self.xls.note2txt( 1, mm.note_abs(), mm.octave() )
            if txt: 
                # txt += '§' + getMode(txt)
                msg = {'topic': '/add', 'payload': txt}
                # self.mqttc.publish('titreur/'+str(mm.octave())+'/add', payload=txt, qos=0, retain=False)

        elif mm.maintype() == 'NOTEOFF':
            txt = self.xls.note2txt( 1, mm.note_abs(), mm.octave() )
            if txt:
                # txt += '§' + getMode(txt)
                msg = {'topic': '/rm', 'payload': txt}
                # self.mqttc.publish('titreur/'+str(mm.octave())+'/rm', payload=txt, qos=2, retain=False)

        elif mm.maintype() == 'CC':

            # CC 14 = ARPPEGIO SPEED
            if mm.values[0] == 12:
                msg = {'topic': '/speed', 'payload': str(mm.values[1]*10)}
                # self.mqttc.publish('titreur/all/speed', payload=str(mm.values[1]*10), qos=1, retain=False)

            # CC 0 = Bank
            elif mm.values[0] == 0:
                self.xls.bank(mm.values[1])
                print('bank', mm.values[1])
                
            # CC 120 / 123 == ALL OFF
            if mm.values[0] == 120 or mm.values[0] == 123:
                msg = {'topic': '/clear', 'payload': ""}
                # self.mqttc.publish('titreur/all/clear', payload="", qos=1, retain=False)
        
        else: 
            return

        if msg != 'niet':
            print('webapp', msg)
            sio.emit('mqtt', msg)


    def stop(self):
        pass

    def clear(self):
        msg = {'topic': '/clear', 'payload': ""}
        sio.emit('mqtt', msg)
        # self.mqttc.publish('titreur/clear', payload="", qos=2, retain=False)