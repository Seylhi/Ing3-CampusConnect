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

| VM | VLAN | IP | Service en place |
|---|---|---|---|
| cc-vm-fw | WAN + 4 VLAN | 10.20.x.1 | OPNsense |
| cc-vm-rp | APP | 10.20.10.10 | Nginx |
| cc-vm-sec | APP | 10.20.10.11 | Keycloak (a venir) |
| cc-vm-app | APP | 10.20.10.12 | gestion-acces (service de test) |
| cc-vm-db | APP | 10.20.10.13 | PostgreSQL |
| cc-vm-bus | APP + DONNEES | 10.20.10.14 / 10.20.20.14 | RabbitMQ + MQTT |
| cc-vm-data | DONNEES | 10.20.20.20 | ingestion, MongoDB (data lake), PostgreSQL (staging, datamart) |
| cc-vm-cicd | ADMIN | 10.20.30.30 | CI/CD (a venir) |
| cc-vm-logs | ADMIN | 10.20.30.31 | Dozzle (logs de toutes les VM) |
| cc-vm-mocks | MOCKS | 10.20.40.40 | simulateurs |

Reseau, VLAN et pare-feu : `reseau/README.md`.

## Acces

Tout passe par OPNsense (172.31.250.211) :

| Quoi | Adresse |
|---|---|
| SSH (bastion cc-vm-cicd) | `ssh -p 2222 sirius@172.31.250.211` |
| Reverse proxy | `http://172.31.250.211` et `http://172.31.250.211/api/acces/` |
| RabbitMQ | `http://172.31.250.211:15672` |
| Logs (Dozzle) | `http://172.31.250.211:8080` |
| Data lake (Compass) | `mongodb://sirius:<mdp>@172.31.250.211:27017/?authSource=admin` |
| Datamart (Power BI) | `172.31.250.211:5432`, base `datamart`, utilisateur `powerbi` |
| OPNsense | `https://172.31.250.211` |

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
scp -J sirius@172.31.250.211:2222 -r vm-bus/rabbitmq sirius@<ip admin vm>:
ssh -J sirius@172.31.250.211:2222 sirius@<ip admin vm>
cd rabbitmq
cp .env.example .env      # renseigner les mots de passe
docker compose up -d
```

Les fichiers `.env` ne sont pas versionnes.

Apres le premier demarrage de RabbitMQ : `./init-files.sh` dans `rabbitmq/` pour creer les files.
Dozzle demande un compte : avant `docker compose up -d`, generer `users.yml` dans `dozzle/` avec `docker run --rm amir20/dozzle generate sirius --password <mdp> --name SIRIUS > users.yml`.
Les scripts `init/` de PostgreSQL et MongoDB s'executent seuls au premier demarrage (volume vide).