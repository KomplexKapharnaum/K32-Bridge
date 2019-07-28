# from PyQt5 import QtWidgets, uic
import sys, time, signal

from interfaces import midi
from interfaces import titreur
from interfaces import webapp
from interfaces import sampler
from interfaces import leds
from interfaces import xlsreader

webappURL = 'https://live.beaucoupbeaucoup.art'


print("KTITREUR - Midi Bridge\n")


if len(sys.argv) < 2:
        print('no broker specified, default to 2.0.0.1')
        brokerIP = "2.0.0.1"
else : 
        brokerIP = sys.argv[1]

print("Connecting...\n")

#  XLS
xls = xlsreader.XlsParser("MidiMapping.xls")

#
# MIDI BRIDGES
#

midiMon        = midi.MidiInterface("K32-monitor", 
                        midi.MidiMonitor() )


midiLeds        = midi.MidiInterface("K32-leds", 
                        leds.Midi2MQTT( brokerIP ) )

midiTitreur     = midi.MidiInterface( "KTitreur", 
                        titreur.Midi2MQTT( brokerIP , xls) )

midiWebapp      = midi.MidiInterface( "KWebapp", 
                        webapp.Midi2SocketIO( webappURL , xls, brokerIP) )


# midiSampler     = midi.MidiInterface("K32-sampler", 
#                         sampler.Midi2MQTT( brokerIP ) )



#
# OSC
#
# oscIN           = osc.OscInterface(9037, brokerIP)

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
        # oscIN.stop()
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C to quit')

try:
        while True:
                signal.pause()
                
except AttributeError:
        # signal.pause() is missing for Windows; wait 1ms and loop instead
        while True:
                time.sleep(1)

