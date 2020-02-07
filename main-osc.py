# from PyQt5 import QtWidgets, uic
import sys, time, signal

from interfaces import osc


print("K32 Bridge OSC\n")


if len(sys.argv) < 2:
        print('no broker specified, default to 10.0.0.1')
        # print("broker ip missing.. please specify Broker IP")
        # sys.exit(1)
        brokerIP = "10.0.0.1"
else : 
        brokerIP = sys.argv[1]

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
        oscIN.stop()
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C')
signal.pause()

