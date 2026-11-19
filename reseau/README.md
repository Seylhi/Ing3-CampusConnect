# Reseau

## VLAN

Commutateur standard `vSwitch116` sur esx4, sans carte physique : seul OPNsense relie ces VLAN a l'exterieur.

| VLAN | Port group vSphere | ID | Reseau | Passerelle (OPNsense) |
|---|---|---|---|---|
| APP | CC - SIRIUS - LAN APP | 10 | 10.20.10.0/24 | 10.20.10.1 |
| DONNEES | CC - SIRIUS - LAN DONNEES | 20 | 10.20.20.0/24 | 10.20.20.1 |
| ADMIN | CC - SIRIUS - LAN ADMIN | 30 | 10.20.30.0/24 | 10.20.30.1 |
| MOCKS | CC - SIRIUS - LAN MOCKS | 40 | 10.20.40.0/24 | 10.20.40.1 |
| Ecole | LAN | - | 172.31.248.0/21 (DHCP) | 172.31.251.249 |

Les flux entre VLAN internes ne passent pas par le pare-feu : chaque VM a une carte dans le VLAN ADMIN (SSH, logs) et vm-bus a une carte dans le VLAN DONNEES (lecture du bus par l'ingestion).

## Adressage

Une VM garde le meme dernier octet dans tous ses VLAN. Les IP sont fixees par netplan (`netplan/`, copie de `/etc/netplan/60-sirius.yaml`). La carte ens192 porte la passerelle par defaut et le DNS : OPNsense, en 10.20.x.1 dans son VLAN.

| VM | ens192 (passerelle) | ens224 | ens256 |
|---|---|---|---|
| cc-vm-rp | APP 10.20.10.10 | ADMIN 10.20.30.10 | |
| cc-vm-sec | APP 10.20.10.11 | ADMIN 10.20.30.11 | |
| cc-vm-app | APP 10.20.10.12 | ADMIN 10.20.30.12 | |
| cc-vm-db | APP 10.20.10.13 | ADMIN 10.20.30.13 | |
| cc-vm-bus | APP 10.20.10.14 | DONNEES 10.20.20.14 | ADMIN 10.20.30.14 |
| cc-vm-data | DONNEES 10.20.20.20 | ADMIN 10.20.30.20 | |
| cc-vm-cicd | ADMIN 10.20.30.30 | | |
| cc-vm-logs | ADMIN 10.20.30.31 | | |
| cc-vm-mocks | MOCKS 10.20.40.40 | ADMIN 10.20.30.40 | |

### Reseau de l'ecole (LAN)

Chaque VM garde une premiere carte `ens160` sur le LAN de l'ecole (172.31.248.0/21, DHCP), mais cette carte est debranchee dans vSphere sur les 9 VM depuis la bascule du 19/11 : elles ne sont plus joignables par le reseau de l'ecole.

Seule `cc-vm-fw` (OPNsense) reste branchee sur ce LAN, par son WAN en `172.31.250.211` (DHCP). C'est le seul point d'entree vers les VLAN : SSH par le bastion et interfaces web par les redirections (voir plus bas).

## Pare-feu OPNsense (cc-vm-fw)

| Carte vSphere | Reseau | Interface | IP |
|---|---|---|---|
| 1 | LAN (ecole) | WAN | DHCP (172.31.250.211) |
| 2 | CC - SIRIUS - LAN ADMIN | ADMIN | 10.20.30.1/24 |
| 3 | CC - SIRIUS - LAN DONNEES | DONNEES | 10.20.20.1/24 |
| 4 | CC - SIRIUS - LAN MOCKS | MOCKS | 10.20.40.1/24 |
| 5 | CC - SIRIUS - LAN APP | APP | 10.20.10.1/24 |

Regles :

| Interface | Source | Destination | Port | Action |
|---|---|---|---|---|
| WAN | 172.31.240.0/21 (VPN ecole) | This Firewall | TCP 443 | Pass |
| WAN | WAN net (reseau ecole) | This Firewall | TCP 443 | Pass |
| WAN | any | 10.20.30.30 | TCP 22 | Pass (bastion) |
| WAN | any | 10.20.10.10 | TCP 80 | Pass (Nginx) |
| WAN | any | 10.20.10.14 | TCP 15672 | Pass (RabbitMQ) |
| WAN | any | 10.20.30.31 | TCP 8080 | Pass (Dozzle) |
| WAN | any | 10.20.20.20 | TCP 9001 | Pass (console RustFS) |
| WAN | any | 10.20.20.20 | TCP 5432 | Pass (datamart) |
| ADMIN | ADMIN net | any | any | Pass |
| APP | APP net | any | any | Pass |
| DONNEES | DONNEES net | any | any | Pass |
| MOCKS | MOCKS net | any | any | Pass |

Sur le WAN, "Block private networks" et "Block bogon networks" sont decoches (le reseau de l'ecole est en adresses privees). NAT sortant automatique.

## Redirections (Destination NAT sur le WAN)

Seule entree depuis l'ecole : l'IP WAN d'OPNsense, 172.31.250.211. Chaque redirection vise l'IP de la carte qui porte la passerelle de la VM (sinon la reponse repartirait par un autre chemin).

| Port WAN | Vers | Service |
|---|---|---|
| 2222 | 10.20.30.30:22 | SSH du bastion (cc-vm-cicd) |
| 80 | 10.20.10.10:80 | Nginx |
| 15672 | 10.20.10.14:15672 | RabbitMQ management |
| 8080 | 10.20.30.31:8080 | Dozzle |
| 9001 | 10.20.20.20:9001 | console RustFS (data lake) |
| 5432 | 10.20.20.20:5432 | PostgreSQL datamart |

Les ports non standard sont declares en alias de type Port(s) : `BASTION_SSH` (2222), `RABBITMQ_UI` (15672), `DOZZLE` (8080), `RUSTFS_CONSOLE` (9001), `POSTGRES` (5432), `MQTT` (1883).

## Acces SSH

```
ssh -p 2222 sirius@172.31.250.211                          # bastion cc-vm-cicd
ssh -J sirius@172.31.250.211:2222 sirius@10.20.30.14       # saut direct vers une VM (ici vm-bus)
```

Depuis cc-vm-cicd, une cle SSH donne acces aux autres VM par leur IP ADMIN (10.20.30.x).
