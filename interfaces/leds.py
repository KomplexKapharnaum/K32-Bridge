from interfaces import midi
import paho.mqtt.client as mqtt
import time
import threading

FIXTURE_SIZE = 16

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
        print(f"-- LEDS: connected to MQTT broker at {broker}")

        # Internal state
        self.payload = []
        self.clear()

        # Send thread
        # self.run = True
        # self.thread = threading.Thread(target=self.sender)
        # self.thread.start()

    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = midi.MidiMessage(msg)
        
        
        if mm.maintype() == 'NOTEON' or mm.maintype() == 'CC' or mm.maintype() == 'NOTEOFF':

            # NOTEON 0-15 or CC 20-35
            note = mm.values[0]
            if mm.maintype() == 'CC':
                note -= 20    
            if note >= 0 and note < FIXTURE_SIZE:
                if mm.maintype() == 'NOTEOFF': 
                    self.payload[mm.channel][note] = 0
                else: 
                    self.payload[mm.channel][note] = mm.values[1]*2
                for i in range(16):
                    print('channel ', i+1, self.payload[i])
                self.send(mm.channel)
                print('')

            # CC 120 / 123 == ALL OFF
            if mm.maintype() == 'CC' and (mm.values[0] == 120 or mm.values[0] == 123):
                self.clear()
                self.send(mm.channel)
                


    def sender(self):
        while self.run:
            for c in range(16):
                self.mqttc.publish('k32/c'+str(c+1)+'/leds', payload=self.payload[c], qos=1, retain=False)
                print('k32/c'+str(c+1)+'/leds', list(self.payload[c]))
            time.sleep(0.1)
    

    def stop(self):
        self.run = False
        self.thread.join()
            
    def clear(self):
        for i in range(16):
            self.payload[i] = bytearray(FIXTURE_SIZE)

    def send(self, channel):
        self.mqttc.publish('k32/c'+str(channel+1)+'/leds', payload=self.payload[channel], qos=1, retain=False)
        print('k32/c'+str(channel+1)+'/leds', list(self.payload[channel]))