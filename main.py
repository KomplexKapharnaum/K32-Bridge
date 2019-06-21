from PyQt5 import QtWidgets, uic
import sys, time, signal

from interfaces import midi
from interfaces import osc


#
# MIDI
#
midiIN = midi.MidiInterface("K32-Midi", "localhost")

#
# MIDI
#
oscIN = osc.OscInterface(9037, "localhost")

#
# QT INTERFACE
#
# app = QtWidgets.QApplication([]) 
# win = uic.loadUi("qt/interface.ui") #specify the location of your .ui file 
# win.show()
# sys.exit(app.exec())


def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        midiIN.stop()
        oscIN.stop()
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C')
signal.pause()

