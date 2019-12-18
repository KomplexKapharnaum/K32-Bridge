from interfaces import midi
import paho.mqtt.client as mqtt
import time
from threading import Thread, Event
import liblo

FIXTURE_SIZE = 32  # 512 / 16
DIRTY_PUSH = 10 # number of re-push on dirty


class UpdateLeds(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent

    def run(self):
        while not self.parent.stopFlag.wait(0.01):  # PUSH refresh
            self.parent.push()


#
#  MIDI Handler (Base class) 
#
class Midi2Base(object):
    def __init__(self):
        self._wallclock = time.time()
        
        # Internal state for each channel
        self.payload = [0]*16
        self.dirty = [0]*16
        self.clear()

        # Push state
        self.stopFlag = Event()
        self.thread = UpdateLeds(self)
        self.thread.start()


    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)        
        
        if mm.maintype() == 'NOTEON' or mm.maintype() == 'CC' or mm.maintype() == 'NOTEOFF':

            # NOTEON = dmx channel // CC moins 20 = dmx channel

            # CC shift -20
            note = mm.values[0]
            if mm.maintype() == 'CC':
                note -= 20

            # Set new value
            if note >= 0:
                if note < FIXTURE_SIZE:
                    if mm.maintype() == 'NOTEOFF':
                        if  self.payload[mm._channel][note] != 0:
                            self.payload[mm._channel][note] = 0
                            self.dirty[mm._channel] = DIRTY_PUSH
                    else: 
                        if self.payload[mm._channel][note] != mm.values[1]*2:
                            self.payload[mm._channel][note] = mm.values[1]*2
                            self.dirty[mm._channel] = DIRTY_PUSH
                
                # CLEAR channel 
                elif note == 127:
                    self.payload[mm._channel] = bytearray(FIXTURE_SIZE)
                    self.dirty[mm._channel] = DIRTY_PUSH

            # CC 119 / 120 / 123 == ALL OFF
            if mm.maintype() == 'CC' and (mm.values[0] == 120 or mm.values[0] == 119 or mm.values[0] == 123):
                self.clear()
                self.dirty[mm._channel] = True


    def stop(self):
        self.stopFlag.set()
        self.thread.join()
            
    def clear(self):
        for i in range(16):
            self.payload[i] = bytearray(FIXTURE_SIZE)

    def push(self):
        print('Base class.. nothing to do')

    

#
#  MIDI Handler to MQTT
#
class Midi2MQTT(Midi2Base):
    def __init__(self, broker):
        # Init Midi handler
        super().__init__()

        # MQTT Client
        self.mqttc = mqtt.Client()
        self.mqttc.connect(broker)
        self.mqttc.loop_start()
        print(f"-- LEDS: sending to broker at {broker}\n")

        
    def push(self):
        for i in range(16):
            if self.dirty[i] > 0:
                self.dirty[i] -= 1
                dev = 'c'+str(i+1) if i < 15 else 'all'
                self.mqttc.publish('k32/'+dev+'/leds/dmx', payload=self.payload[i], qos=1, retain=False)
                print('k32/'+dev+'/leds/dmx', list(self.payload[i]))

#
#  MIDI Handler to MQTT
#
class Midi2OSC(Midi2Base):
    def __init__(self, port, ip):
        # Init Midi handler
        super().__init__()

        # OSC Client
        self.port = port
        self.ip = ip
        print(f"-- LEDS: sending OSC on {ip} : {port}\n")

        
    def push(self):
        for i in range(16):
            if self.dirty[i] > 0:
                self.dirty[i] -= 1
                dev = 'c'+str(i+1) if i < 15 else 'all'
                liblo.send( (self.ip, self.port), '/k32/'+dev+'/leds/dmx', list(self.payload[i]) )
                print('OSC send: k32/'+dev+'/leds/dmx', list(self.payload[i]))