import time
import json

import paho.mqtt.client as mqtt
import liblo


class OscInterface():
    def __init__(self, port, handler):
        self.server = liblo.ServerThread(port)
        self.server.add_method(None, None, handler)
        self.server.start()


class Osc2MQTT(object):
    def __init__(self, broker):
        self.port = port

        self.mqttc = mqtt.Client()
        self.mqttc.connect(broker)
        self.mqttc.loop_start()

    def __call__(self, path, args, types, src, userdata):
        p = "§".join([str(i) for i in args])            # string payload
        self.mqttc.publish('k32'+path, payload=p, qos=1, retain=False)
        print("Osc2MQTT:", path, p.replace("§", " "))
        
    def stop(self):
        self.mqttc.loop_stop(True)



        


