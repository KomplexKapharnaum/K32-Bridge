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
        if len(txt.split('/')[1]) < 25: return 'NO_SCROLL_NORMAL'
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

        self.bank = 0

        print("")


    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)

        # print(mm.maintype(), 'chan '+str(mm.channel()), mm.values)

        if mm.maintype() in ['NOTEON', 'NOTEOFF']:

            # NOTEON 127
            if mm.maintype() == 'NOTEON' and mm.note() == 127:
                self.mqttc.publish('k32/c'+str(mm.channel())+'/titre/clear', payload="", qos=1, retain=False)
                print('NOTE 127: k32/c'+str(mm.channel())+'/titre/clear')

            # NOTES TXT from XLS
            else:
                txt = self.xls.getCell( self.bank, mm.channel()+1, mm.note()+2 )
                if txt: 
                    txt = txt.replace("\n", "/")
                    txt = txt.replace("\r", "")

                    sub = txt.split("/")
                    if len(sub) > 1:
                        sub1 = ("_").join(sub[1:])
                        txt = sub[0]+"/"+sub1

                    txt += '§' + getMode(txt)

                    if mm.maintype() == 'NOTEON':
                        self.mqttc.publish('k32/c'+str(mm.channel())+'/titre/text', payload=txt, qos=0, retain=False)   #add
                        print('k32/c'+str(mm.channel())+'/titre/add', txt)

                    elif mm.maintype() == 'NOTEOFF':
                        self.mqttc.publish('k32/c'+str(mm.channel())+'/titre/clear', payload=txt, qos=2, retain=False) #rm
                        print('k32/c'+str(mm.channel())+'/titre/rm', txt)

            

        elif mm.maintype() == 'CC':

            # CC 14 = ARPPEGIO SPEED
            if mm.values[0] == 12:
                self.mqttc.publish('k32/c'+str(mm.channel())+'/titre/speed', payload=str(mm.values[1]*10), qos=1, retain=False)
                print('k32/c'+str(mm.channel())+'/titre/speed', str(mm.values[1]*10))

            # CC 0 = Bank
            elif mm.values[0] == 0:
                self.bank = mm.values[1]
                self.mqttc.publish('k32/all/titre/clear', payload="", qos=1, retain=False)
                print('bank', mm.values[1])
                
            # CC 120 / 123 == ALL OFF
            if mm.values[0] == 120 or mm.values[0] == 123:
                self.mqttc.publish('k32/c'+str(mm.channel())+'/titre/clear', payload="", qos=1, retain=False)
                print('CC 120/127: k32/c'+str(mm.channel())+'/titre/clear')


    def stop(self):
        self.mqttc.loop_stop(True)

    def clear(self):
        self.mqttc.publish('k32/all/titre/clear', payload="", qos=2, retain=False)
        print('k32/all/titre/clear')