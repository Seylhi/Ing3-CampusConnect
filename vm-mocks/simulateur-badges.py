# Simulateur de lecteurs de badges : publie un passage de badge en MQTT toutes les 5 secondes.
# Variables : BUS_HOST, BUS_PORT, MQTT_USER, MQTT_PASS

import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BUS_HOST = os.environ.get("BUS_HOST", "10.20.10.14")
BUS_PORT = int(os.environ.get("BUS_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "sirius")
MQTT_PASS = os.environ["MQTT_PASS"]

PORTES = ["A", "B", "C"]

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # paho-mqtt 2.x
except AttributeError:
    client = mqtt.Client()  # paho-mqtt 1.x
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(BUS_HOST, BUS_PORT)
client.loop_start()

while True:
    porte = random.choice(PORTES)
    message = {
        "badge": f"E{random.randint(10000, 10050)}",
        "porte": porte,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    client.publish(f"badges/porte-{porte}", json.dumps(message))
    print("envoye :", message)
    time.sleep(5)
