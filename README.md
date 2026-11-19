# CampusConnect

Plateforme de campus connecte : acces par badge, reservation de salles, capteurs de salle et exploitation des donnees (data lake, Power BI).


## Groupe

| Membre | Role |
|---|---|
| Ethan CORCHER |Big Data, Archi Cloud, BI, CT HA |
| Ilyes HBADA |Big Data, Archi Cloud, BI, CT HA|
| Khedim Mohammed | Secu x2 |
| Abderraouf REDJECHTA | Archi Cloud , Secu , BI, CT HA |

## Machines

10 VM sur l'hote esx4 (vSphere ESIPE), dossier `CampusConnect/Sirius3`. Nom de la VM = hostname = `cc-vm-<role>`.

| VM | IP réseau école | VLAN | IP | Service en place |
|---|---|---|---|---|
| cc-vm-fw | 172.31.250.211 (WAN) | APP / DONNEES / ADMIN / MOCKS | 10.20.10.1 / 10.20.20.1 / 10.20.30.1 / 10.20.40.1 | OPNsense |
| cc-vm-rp | 172.31.252.201 | APP | 10.20.10.10 | Nginx |
| cc-vm-sec | 172.31.253.82 | APP | 10.20.10.11 | Keycloak (a venir) |
| cc-vm-app | 172.31.253.19 | APP | 10.20.10.12 | gestion-acces (service de test) |
| cc-vm-db | 172.31.249.168 | APP | 10.20.10.13 | PostgreSQL |
| cc-vm-bus | 172.31.252.23 | APP + DONNEES | 10.20.10.14 / 10.20.20.14 | RabbitMQ + MQTT |
| cc-vm-data | 172.31.250.254 | DONNEES | 10.20.20.20 | ingestion, MongoDB (data lake), PostgreSQL (staging, datamart) |
| cc-vm-cicd | 172.31.252.214 | ADMIN | 10.20.30.30 | CI/CD (a venir) |
| cc-vm-logs | 172.31.252.93 | ADMIN | 10.20.30.31 | Dozzle (logs de toutes les VM) |
| cc-vm-mocks | 172.31.252.56 | MOCKS | 10.20.40.40 | simulateurs |

Reseau, VLAN et pare-feu : `reseau/README.md`.

## Contenu

```
.github/workflows/         pipeline GitHub Actions (a venir)
reseau/                    VLAN, plan d'adressage, OPNsense, netplan de chaque VM
vm-rp/nginx/               reverse proxy : /api/acces/ -> gestion-acces
vm-sec/keycloak/           Keycloak (a venir)
vm-app/gestion-acces/      service de test (traefik/whoami) sur 10.20.10.12:8081
vm-app/reservations/       (a venir)
vm-app/notifications/      (a venir)
vm-app/collectors/         collector-badges, collector-comptage, collector-capteurs (a venir)
vm-db/postgresql/          bases bdd_acces et bdd_reservations, un utilisateur par base
vm-bus/rabbitmq/           RabbitMQ avec les plugins management et MQTT, script de creation des files
vm-data/collecte-externe/  open data (a venir)
vm-data/ingestion/         file datalake -> MongoDB raw (un document par message)
vm-data/datalake/          MongoDB, bases raw et curated
vm-data/spark/             traitements raw -> curated -> staging (a venir)
vm-data/postgresql/        bases staging et datamart (utilisateurs etl et powerbi)
vm-cicd/ansible/           deploiement automatise (a venir)
vm-logs/dozzle/            interface web des logs
vm-logs/agent/             agent Dozzle a lancer sur rp, app, db, bus et data
vm-mocks/                  simulateurs MQTT de badges et de capteurs
```

## Flux des messages

```
simulateurs (vm-mocks) --MQTT--> RabbitMQ (vm-bus), exchange amq.topic
    badges.#   -> file badges   (collectors de vm-app, a venir)
    capteurs.# -> file capteurs (collectors de vm-app, a venir)
    badges.# + capteurs.# -> file datalake -> ingestion (vm-data) -> MongoDB raw
```

## Lancer un service

Chaque dossier se copie sur sa VM et se lance avec Docker Compose :

```
scp -r vm-bus/rabbitmq sirius@<ip vm>:
ssh sirius@<ip vm>
cd rabbitmq
cp .env.example .env      # renseigner les mots de passe
docker compose up -d
```

Les fichiers `.env` ne sont pas versionnes.

Apres le premier demarrage de RabbitMQ : `./init-files.sh` dans `rabbitmq/` pour creer les files.
Les scripts `init/` de PostgreSQL et MongoDB s'executent seuls au premier demarrage (volume vide).

## Verifier

| Quoi | Commande |
|---|---|
| Reverse proxy | `curl http://<vm-rp>/api/acces/` puis `docker logs -f nginx` sur vm-rp |
| Bases | `docker exec -it postgres psql -U admin -c '\l'` sur vm-db |
| Bus | interface web `http://<vm-bus>:15672`, onglet Queues |
| Message MQTT | sur vm-mocks : `sudo apt install -y python3-paho-mqtt` puis `MQTT_PASS=<mdp> BUS_HOST=<ip vm-bus> python3 simulateur-badges.py` (ou `simulateur-capteurs.py`) |
| Ingestion | `docker logs -f ingestion` sur vm-data |
| Data lake | `docker exec mongo mongosh -u sirius -p <mdp> --quiet --eval 'db.getSiblingDB("raw").badges.countDocuments()'` sur vm-data, ou MongoDB Compass |
| Staging / datamart | `docker exec -it postgres-dm psql -U admin -c '\l'` sur vm-data |
| Logs | interface web `http://<vm-logs>:8080` |
