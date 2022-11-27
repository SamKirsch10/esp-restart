#!/usr/bin/env python3

from datetime import datetime
import paho.mqtt.client as mqtt
from paho.mqtt.client import connack_string as ack
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes 
from time import sleep
from json import loads
import requests
import logging
from sys import argv, exit
import os

logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.INFO)

DEVICES = dict()

client = mqtt.Client(
	client_id="restart_cron",
	transport="tcp",
	protocol=mqtt.MQTTv5
	)


def on_connect(client, userdata, flags, rc, v5config=None):
	logging.debug(f"Connected to mqtt with status: [{ack(rc)}]")
	client.subscribe("espresense/rooms/+/telemetry")    

def on_message(client, userdata, message):
    # print("message topic=",message.topic)
    data = loads(str(message.payload.decode("utf-8")))
    # print("telemetry update received " ,data)
    room = message.topic.split("/")[2]
    logging.debug("Adding telemetry data")
    if room not in DEVICES:
    	lastRestarted = datetime.now()
    else:
    	# keep current time...
    	lastRestarted = DEVICES[room]["lastRestarted"]
    DEVICES[room] = {
    	"ip": data["ip"],
    	"lastSeen": datetime.now(),
    	"lastRestarted": lastRestarted
    	}

def restart(room):
	try:
		res = requests.post(f"http://{DEVICES[room]['ip']}/restart")
		DEVICES[room]["lastRestarted"] = datetime.now()
	except ConnectionResetError:
		pass
	sleep(5)

def watcher():
	logging.info("Starting watcher")
	while True:
		logging.debug("watcher loop")
		for room in DEVICES:
			timeDelta = (datetime.now() - DEVICES[room]["lastSeen"]).seconds
			if timeDelta > 300:
				logging.info(f"Room [{room}] hasn't posted a message in awhile...")
				logging.info("Restarting room...")
				restart(room)
			elif (datetime.now() - DEVICES[room]["lastRestarted"]).seconds > 21600: # 6 hours
				logging.debug("6 hour time window reached!")
				logging.info(f"Restarting room. [{room}]..")
				restart(room)
			else:
				logging.debug(f"Room [{room}] is still actively posting!")

		sleep(60)

def run():
	logging.info("Starting MQTT Listener")
	client.on_connect=on_connect
	client.on_message=on_message
	client.username_pw_set(argv[2], argv[3])
	properties=Properties(PacketTypes.CONNECT)
	properties.SessionExpiryInterval=30*60 # in seconds
	client.connect(argv[1], keepalive=300, properties=properties)
	client.loop_start()
	watcher()


if __name__ == '__main__':
	if len(argv) < 3:
		logging.error(f"This script takes three positional arguments: \"./{os.path.basename(__file__)} mqtt_host mqtt_user mqtt_pass\"")
		exit(1)
	run()
