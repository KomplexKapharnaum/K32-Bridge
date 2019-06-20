import paho.mqtt.client as mqtt
import sys, time, signal

#
# MQTT
#
mqttc = mqtt.Client()
mqttc.connect('localhost')
mqttc.loop_start()

