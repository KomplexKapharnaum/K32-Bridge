import time
import json

import paho.mqtt.client as mqtt
import liblo


def callback(path, args, types, src, mqttc):
    # p = json.dumps({"path": path, "args": args})  # JSON payload
    p = "§".join([str(i) for i in args])            # string payload
    mqttc.publish('k32'+path, payload=p, qos=1, retain=True)
    print("OSC:", path, p.replace("§", " "))


class OscInterface():
    def __init__(self, port, addr):
        self.port = port

        self.mqttc = mqtt.Client()
        self.mqttc.connect(addr)
        self.mqttc.loop_start()

        self.server = liblo.ServerThread(self.port)
        self.server.add_method(None, None, callback, self.mqttc)
        self.server.start()

    def stop(self):
        self.mqttc.loop_stop(True)

        


