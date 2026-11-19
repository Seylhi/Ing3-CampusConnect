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

Une VM garde le meme dernier octet dans tous ses VLAN. Les IP sont fixees par netplan (`netplan/`, copie de `/etc/netplan/60-sirius.yaml`).

| VM | ens192 | ens224 | ens256 |
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

La carte 1 (ens160) de chaque VM est encore sur le reseau de l'ecole, en DHCP : elle sert de passerelle en attendant le passage par OPNsense.

### Réseau de l'école (LAN)

Chaque VM possède une première interface réseau `ens160`, connectée au LAN de l'école. Son adresse IP est attribuée automatiquement par DHCP. Ces adresses permettent notamment l'accès aux VM depuis le VPN de l'école.

| VM | Interface | Adresse IP (LAN école) |
|---|---|---|
| `cc-vm-rp` | `ens160` | `172.31.252.201` |
| `cc-vm-sec` | `ens160` | `172.31.253.82` |
| `cc-vm-app` | `ens160` | `172.31.253.19` |
| `cc-vm-db` | `ens160` | `172.31.249.168` |
| `cc-vm-bus` | `ens160` | `172.31.252.23` |
| `cc-vm-data` | `ens160` | `172.31.250.254` |
| `cc-vm-cicd` | `ens160` | `172.31.252.214` |
| `cc-vm-logs` | `ens160` | `172.31.252.93` |
| `cc-vm-mocks` | `ens160` | `172.31.252.56` |

La VM `cc-vm-fw` (OPNsense) dispose également d'une interface WAN sur le LAN de l'école. Elle reçoit l'adresse `172.31.250.211` par DHCP.

Les adresses du LAN de l'école sont attribuées par DHCP et peuvent donc évoluer selon les baux délivrés par le serveur DHCP.


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
| ADMIN | ADMIN net | any | any | Pass |
| APP | APP net | any | any | Pass |
| DONNEES | DONNEES net | any | any | Pass |
| MOCKS | MOCKS net | any | any | Pass |

Sur le WAN, "Block private networks" et "Block bogon networks" sont decoches (le reseau de l'ecole est en adresses privees). NAT sortant automatique.
