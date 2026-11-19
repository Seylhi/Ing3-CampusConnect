# Ingestion : lit la file datalake de RabbitMQ et depose les messages bruts dans le bucket raw du data lake (RustFS, API S3).
# Les messages sont regroupes par source dans un fichier JSON Lines, toutes les FLUSH_SECONDS secondes :
#   s3://raw/badges/date=2026-11-19/163012-ab12cd34.jsonl

import json
import os
import time
import uuid
from datetime import datetime, timezone

import boto3
import pika
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

AMQP_HOST = os.environ.get("AMQP_HOST", "10.20.20.14")
AMQP_USER = os.environ.get("AMQP_USER", "sirius")
AMQP_PASS = os.environ["AMQP_PASS"]
QUEUE = os.environ.get("QUEUE", "datalake")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "sirius")
S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]
BUCKET = os.environ.get("BUCKET", "raw")
FLUSH_SECONDS = int(os.environ.get("FLUSH_SECONDS", "10"))
MAX_BATCH = int(os.environ.get("MAX_BATCH", "100"))

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name="us-east-1",
    config=Config(
        s3={"addressing_style": "path"},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
)


def creer_buckets():
    for nom in (BUCKET, "curated"):
        try:
            s3.head_bucket(Bucket=nom)
        except ClientError:
            s3.create_bucket(Bucket=nom)
            print("bucket cree :", nom, flush=True)


def deposer(lots):
    maintenant = datetime.now(timezone.utc)
    for source, lignes in lots.items():
        cle = f"{source}/date={maintenant:%Y-%m-%d}/{maintenant:%H%M%S}-{uuid.uuid4().hex[:8]}.jsonl"
        s3.put_object(Bucket=BUCKET, Key=cle, Body=("\n".join(lignes) + "\n").encode(), ContentType="application/x-ndjson")
        print(f"depose : s3://{BUCKET}/{cle} ({len(lignes)} messages)", flush=True)


while True:
    try:
        creer_buckets()
        credentials = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
        connection = pika.BlockingConnection(pika.ConnectionParameters(AMQP_HOST, credentials=credentials, heartbeat=60))
        channel = connection.channel()
        channel.basic_qos(prefetch_count=MAX_BATCH * 2)
        print("en attente de messages sur la file", QUEUE, flush=True)

        lots, dernier, nombre, debut = {}, None, 0, time.monotonic()
        for method, properties, body in channel.consume(QUEUE, inactivity_timeout=1):
            if method is not None:
                source = method.routing_key.split(".")[0]
                try:
                    payload = json.loads(body)
                except ValueError:
                    payload = body.decode(errors="replace")
                lots.setdefault(source, []).append(json.dumps({
                    "_source": source,
                    "_routing_key": method.routing_key,
                    "_ingested_at": datetime.now(timezone.utc).isoformat(),
                    "payload": payload,
                }, ensure_ascii=False))
                dernier = method.delivery_tag
                nombre += 1
            if nombre == 0:
                debut = time.monotonic()
            elif nombre >= MAX_BATCH or time.monotonic() - debut >= FLUSH_SECONDS:
                deposer(lots)
                channel.basic_ack(dernier, multiple=True)  # acquitte seulement apres le depot
                lots, dernier, nombre = {}, None, 0
    except (pika.exceptions.AMQPError, BotoCoreError, ClientError) as erreur:
        print("RabbitMQ ou RustFS injoignable, nouvel essai dans 5 s :", erreur, flush=True)
        time.sleep(5)
