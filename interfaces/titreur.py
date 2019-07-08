import time, signal, sys, os
import xlrd
import paho.mqtt.client as mqtt
from interfaces import midi
import socketio

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
# XLS Read and Parse
#
class XlsParser():
    def __init__(self, path):
        self.path = path
        self.workbook = xlrd.open_workbook(self.path)
        self.worksheet = self.workbook.sheet_by_index(0)
        self.bank(1)

    def bank(self, b):
        self.offset = max(1, 16*(b)+1)

    def note2txt(self, noteabs, octave):
        value = None

        if octave >= 0:
            # C1 = 24 // C2 = 36
            if octave == 0: colx = octave + 8
            else: colx = octave 
            rowx = self.offset + noteabs + 1
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
#  SOCKETIO link
#
sioURL = 'https://live.beaucoupbeaucoup.art'
sio = socketio.Client()
sio.connect(sioURL)

@sio.on('connect')
def on_connect():
    print(f"-- SOCKETIO: connected to online server at {sioURL}")
    sio.emit('command', 'ok')


class Mqtt2Socketio(object):
    def __init__(self, broker):
        self.mqttc = mqtt.Client()
        self.mqttc.connect(broker)
        self.mqttc.subscribe('titreur/all/#', 1)
        self.mqttc.subscribe('titreur/0/#', 1)
        self.mqttc.on_message = self.on_mqtt_msg
        self.mqttc.loop_start()
        print(f"-- SOCKETIO: connected to broker at {broker}")

    def on_mqtt_msg(self, client, userdata, message):
        # print("Received message '" + str(message.payload) + "' on topic '"
        #     + message.topic + "' with QoS " + str(message.qos))
        msg = {'topic': '/'.join(message.topic.split('/')[2:]), 'payload': message.payload.decode('utf8', errors='ignore'), 'qos': message.qos}
        # print(msg)
        sio.emit('mqtt', msg)

    def stop(self):
        self.mqttc.loop_stop(True)


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
        print(f"-- TITREUR: connected to broker at {broker}")

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
            txt = self.xls.note2txt( mm.note_abs(), mm.octave() )
            if txt: 
                txt += '§' + getMode(txt)
                self.mqttc.publish('titreur/'+str(mm.octave())+'/add', payload=txt, qos=0, retain=False)
                print('titreur/'+str(mm.octave())+'/add', txt)

        elif mm.maintype() == 'NOTEOFF':
            txt = self.xls.note2txt( mm.note_abs(), mm.octave() )
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
                print('bank', mm.values[1])
                
            # CC 120 / 123 == ALL OFF
            if mm.values[0] == 120 or mm.values[0] == 123:
                self.mqttc.publish('titreur/all/clear', payload="", qos=1, retain=False)
                print('titreur/all/clear')


    def stop(self):
        self.mqttc.loop_stop(True)