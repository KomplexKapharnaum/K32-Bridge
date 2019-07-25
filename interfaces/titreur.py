import time, signal, sys, os
import paho.mqtt.client as mqtt
from interfaces import midi
from interfaces import xlsreader

# DEVICES = ['2.0.11.44', '2.0.11.45', '2.0.11.48', '2.0.11.50', '2.0.11.51', '2.0.11.52', '2.0.11.54']

#
# TITREUR MODE
#
def getMode(txt):
    if '/' in txt:
        if len(txt.split('/')[1]) < 9: return 'NO_SCROLL_NORMAL'
        else: return 'SCROLL_LOOP_NORMAL'
    else:
        if len(txt) < 13: return 'NO_SCROLL_BIG'
        else: return 'SCROLL_LOOP_BIG'


#
#  MIDI Handler (PUBLIC)
#
class Midi2MQTT(object):
    def __init__(self, broker, xls):
        self._wallclock = time.time()

        # MQTT Client
        self.mqttc = mqtt.Client()
        self.mqttc.connect(broker)
        self.mqttc.loop_start()
        print(f"-- TITREUR: sending to broker at {broker}")

        # XLS Read and Parse
        self.xls = xls

        print("")


    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)

        if mm.maintype() == 'NOTEON':
            txt = self.xls.note2txt( 0, mm.note_abs(), mm.octave() )
            if txt: 
                txt += '§' + getMode(txt)
                self.mqttc.publish('titreur/'+str(mm.octave())+'/add', payload=txt, qos=0, retain=False)
                print('titreur/'+str(mm.octave())+'/add', txt)

        elif mm.maintype() == 'NOTEOFF':
            txt = self.xls.note2txt( 0, mm.note_abs(), mm.octave() )
            if txt:
                txt += '§' + getMode(txt)
                self.mqttc.publish('titreur/'+str(mm.octave())+'/rm', payload=txt, qos=2, retain=False)
                print('titreur/'+str(mm.octave())+'/rm', txt)

        elif mm.maintype() == 'CC':

            # CC 14 = ARPPEGIO SPEED
            if mm.values[0] == 12:
                self.mqttc.publish('titreur/all/speed', payload=str(mm.values[1]*10), qos=1, retain=False)
                print('titreur/all/speed', str(mm.values[1]*10))

            # CC 0 = Bank
            elif mm.values[0] == 0:
                self.xls.bank(mm.values[1])
                self.mqttc.publish('titreur/all/clear', payload="", qos=1, retain=False)
                print('bank', mm.values[1])
                
            # CC 120 / 123 == ALL OFF
            if mm.values[0] == 120 or mm.values[0] == 123:
                self.mqttc.publish('titreur/all/clear', payload="", qos=1, retain=False)
                print('titreur/all/clear')


    def stop(self):
        self.mqttc.loop_stop(True)

    def clear(self):
        self.mqttc.publish('titreur/clear', payload="", qos=2, retain=False)
        print('titreur/clear')