#!/bin/bash
# Cree les files et leurs liaisons avec l'exchange amq.topic (via l'API de RabbitMQ).
# A lancer sur vm-bus, dans ce dossier, une fois RabbitMQ demarre. Relancable sans risque.
#   badges, capteurs : pour les collectors de vm-app
#   datalake         : pour l'ingestion de vm-data (recoit une copie des badges et des capteurs)
set -e
[ -f .env ] && . ./.env
API=http://localhost:15672/api
AUTH="sirius:${RABBITMQ_PASS:?RABBITMQ_PASS manquant}"

file() {
  curl -fsS -o /dev/null -u "$AUTH" -X PUT -H "content-type: application/json" \
    -d '{"durable":true}' "$API/queues/%2F/$1"
}

liaison() {
  curl -fsS -o /dev/null -u "$AUTH" -X POST -H "content-type: application/json" \
    -d "{\"routing_key\":\"$2\"}" "$API/bindings/%2F/e/amq.topic/q/$1"
  echo "$1 <- amq.topic ($2)"
}

file badges;   liaison badges   "badges.#"
file capteurs; liaison capteurs "capteurs.#"
file datalake; liaison datalake "badges.#"; liaison datalake "capteurs.#"
