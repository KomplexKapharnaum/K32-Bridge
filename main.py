# from PyQt5 import QtWidgets, uic
import sys, time, signal

from interfaces import midi
from interfaces import titreur
from interfaces import sampler
from interfaces import leds
from interfaces import osc


print("KTITREUR - Midi Bridge\n")

if len(sys.argv) < 2:
        print("broker ip missing.. please specify Broker IP")
        sys.exit(1)
brokerIP = sys.argv[1]

#
# MIDI
#
midiTitreur     = midi.MidiInterface( "KTitreur", 
                        titreur.Midi2MQTT( brokerIP , "MidiMapping.xls") )

mobileTitreur   = titreur.Mqtt2Socketio( brokerIP )

midiSampler     = midi.MidiInterface("K32-sampler", 
                        sampler.Midi2MQTT( brokerIP ) )

midiLeds        = midi.MidiInterface("K32-leds", 
                        leds.Midi2MQTT( brokerIP ) )

#
# OSC
#
oscIN           = osc.OscInterface(9037, brokerIP)

#
# QT INTERFACE
#
# app = QtWidgets.QApplication([]) 
# win = uic.loadUi("qt/interface.ui") #specify the location of your .ui file 
# win.show()
# sys.exit(app.exec())


def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        midiTitreur.stop()
        oscIN.stop()
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C')
signal.pause()

