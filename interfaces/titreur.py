import time, signal, sys, os
import xlrd
import paho.mqtt.client as mqtt
from interfaces import midi

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
# XLS Read and Parse
#
class XlsParser():
    def __init__(self, path):
        self.path = path
        self.workbook = xlrd.open_workbook(self.path)
        self.worksheet = self.workbook.sheet_by_index(0)
        self.bank(1)

    def bank(self, b):
        self.offset = max(1, 16*(b-1)+1)

    def note2txt(self, note):
        # C1 = 24 // C2 = 36
        colx = (note//12)-1 
        rowx = self.offset + (note%12) + 1
        value = "   ----  "
        if rowx in range(self.worksheet.nrows):
            value = self.worksheet.cell_value( rowx, colx )
        # print('Parser:', value)
        return value

    def reload(self):
        self.workbook.release_resources()
        self.workbook = xlrd.open_workbook(self.path)
        self.worksheet = self.workbook.sheet_by_index(0)

    
#
# XLS Watchdog handler
#
class XlsHandler(FileSystemEventHandler):
    def __init__(self, parser, mqttc):
        super().__init__()
        self.parser = parser
        self.mqttc = mqttc

    def on_modified(self, event):
        if os.path.basename(event.src_path) == 'MidiMapping.xls':
            print('-- MidiMapping.xls modified')
            self.mqttc.publish('titreur/clear', payload="", qos=2, retain=False)
            print('titreur/clear')
            self.parser.reload()



#
#  MIDI Handler (PUBLIC)
#
class Midi2MQTT(object):
    def __init__(self, broker, xlspath):
        self._wallclock = time.time()

        # MQTT Client
        self.mqttc = mqtt.Client()
        self.mqttc.connect(broker)
        self.mqttc.loop_start()
        print(f"-- MQTT: connected to broker at {broker}")

        # XLS Read and Parse
        self.xls = XlsParser(xlspath)

        # XLS Watchdog
        self.observer = Observer()
        self.observer.schedule( XlsHandler(self.xls, self.mqttc), path='./', recursive=False)
        self.observer.start()


    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)

        if mm.maintype() == 'NOTEON':
            txt = self.xls.note2txt( mm.values[0] ) 
            txt += '§' + getMode(txt)
            self.mqttc.publish('titreur/add', payload=txt, qos=2, retain=False)
            print('titreur/add', txt)

        elif mm.maintype() == 'NOTEOFF':
            txt = self.xls.note2txt( mm.values[0] ) 
            txt += '§' + getMode(txt)
            self.mqttc.publish('titreur/rm', payload=txt, qos=2, retain=False)
            print('titreur/rm', txt)

        elif mm.maintype() == 'CC':

            # CC 14 = ARPPEGIO SPEED
            if mm.values[0] == 12:
                self.mqttc.publish('titreur/speed', payload=str(mm.values[1]*10), qos=1, retain=False)
                print('titreur/speed', str(mm.values[1]*10))

            # CC 32 = Bank LSB
            elif mm.values[0] == 32:
                self.xls.bank(mm.values[1])
                print('bank', mm.values[1])
                
            # else: print(mm.values[0])
        
        else:
            print('MIDI:', mm.maintype(), mm.subtype(), mm.values  )

    def stop(self):
        self.mqttc.loop_stop(True)