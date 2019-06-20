from PyQt5 import QtWidgets, uic
import paho.mqtt.client as mqtt
import sys, time, signal

from interfaces import midi

#
# MQTT
#
mqttc = mqtt.Client()
mqttc.connect('localhost')
mqttc.loop_start()


#
# MIDI
#
midiIN = midi.MidiInterface("K32-Midi", mqttc)


# app = QtWidgets.QApplication([]) 
# win = uic.loadUi("interface.ui") #specify the location of your .ui file 
# win.show()
# sys.exit(app.exec())


def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        mqttc.loop_stop(True)
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C')
signal.pause()

