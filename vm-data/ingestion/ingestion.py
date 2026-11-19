# Ingestion : lit la file datalake de RabbitMQ et ecrit chaque message, tel quel, dans la base raw de MongoDB.
# Une collection par source : badges.porte-A -> raw.badges, capteurs.S101 -> raw.capteurs

import json
import os
import time
from datetime import datetime, timezone

import pika
from pymongo import MongoClient

AMQP_HOST = os.environ.get("AMQP_HOST", "10.20.20.14")
AMQP_USER = os.environ.get("AMQP_USER", "sirius")
AMQP_PASS = os.environ["AMQP_PASS"]
MONGO_URI = os.environ["MONGO_URI"]
QUEUE = os.environ.get("QUEUE", "datalake")

raw = MongoClient(MONGO_URI)["raw"]


def on_message(channel, method, properties, body):
    source = method.routing_key.split(".")[0]
    try:
        payload = json.loads(body)
    except ValueError:
        payload = body.decode(errors="replace")
    raw[source].insert_one({
        "_source": source,
        "_routing_key": method.routing_key,
        "_ingested_at": datetime.now(timezone.utc),
        "payload": payload,
    })
    channel.basic_ack(method.delivery_tag)
    print("ingere :", method.routing_key, flush=True)


while True:
    try:
        credentials = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
        connection = pika.BlockingConnection(pika.ConnectionParameters(AMQP_HOST, credentials=credentials, heartbeat=60))
        channel = connection.channel()
        channel.basic_qos(prefetch_count=10)
        channel.basic_consume(queue=QUEUE, on_message_callback=on_message)
        print("en attente de messages sur la file", QUEUE, flush=True)
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError:
        print("RabbitMQ injoignable, nouvel essai dans 5 s", flush=True)
        time.sleep(5)
