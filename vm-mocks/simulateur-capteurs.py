# Simulateur de capteurs de salle : publie une mesure en MQTT toutes les 10 secondes.
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

SALLES = ["S101", "S102", "S201", "AMPHI-1"]

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # paho-mqtt 2.x
except AttributeError:
    client = mqtt.Client()  # paho-mqtt 1.x
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(BUS_HOST, BUS_PORT)
client.loop_start()

while True:
    salle = random.choice(SALLES)
    message = {
        "salle": salle,
        "temperature": round(random.uniform(18, 26), 1),
        "humidite": random.randint(35, 65),
        "presence": random.randint(0, 40),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    client.publish(f"capteurs/{salle}", json.dumps(message))
    print("envoye :", message)
    time.sleep(10)
