# Infrastructure Guide — Health Insurance Demo

> Guide complet de l'infrastructure : architecture, configuration, networking, services, et commandes CLI.

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture réseau](#2-architecture-réseau)
3. [Hôte Linux](#3-hôte-linux)
4. [VM1 — Windows (Monolith)](#4-vm1--windows-monolith)
5. [VM2 — Docker](#5-vm2--docker)
6. [VM3 — k3s (Kubernetes)](#6-vm3--k3s-kubernetes)
7. [Monitoring : Prometheus & Grafana](#7-monitoring--prometheus--grafana)
8. [Guide CLI complet](#8-guide-cli-complet)

---

## 1. Vue d'ensemble

Ce projet déploie la même API FastAPI (`health-insurance-api`) sur trois environnements différents pour comparer les approches de déploiement :

| Environnement | Technologie | VM | IP |
|---|---|---|---|
| **Monolith** | Python + NSSM (Windows Service) | `winserv00` | `192.168.56.102` |
| **Docker** | Docker container | `docker-env` | `192.168.56.103` |
| **Kubernetes** | k3s (pod + NodePort) | `ubuntu_demo` | `192.168.56.101` |

L'hôte Linux exécute **Prometheus** (scraping) et **Grafana** (visualisation).

---

## 2. Architecture réseau

```
┌─────────────────────────────────────────────────────────────────┐
│  HÔTE LINUX                                                      │
│                                                                   │
│  Prometheus :9090 ──────────────────────────────────────────┐   │
│  Grafana    :3000                                           │   │
│                                                             │   │
│  vboxnet0 : 192.168.56.1/24  (host-only interface)          │   │
└──────────────────────────┬──────────────────────────────────┘   │
                           │ Host-only network 192.168.56.0/24     │
        ┌──────────────────┼──────────────────┐                   │
        │                  │                  │                   │
        ▼                  ▼                  ▼                   │
┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  VM1 Windows  │  │   VM2 Docker  │  │   VM3 k3s     │          │
│ 192.168.56.102│  │ 192.168.56.103│  │ 192.168.56.101│          │
│               │  │               │  │               │          │
│ :8001 FastAPI │  │ :8002 FastAPI │  │ :30003 FastAPI│          │
│ :9182 WinExp  │  │ :9100 NodeExp │  │ :9100 NodeExp │          │
└───────────────┘  └───────────────┘  └───────────────┘          │
```

### Accès SSH depuis l'hôte

| VM | Commande SSH |
|---|---|
| VM1 Windows | `ssh vboxuser@192.168.56.102` (direct, port 22) |
| VM2 Docker | `ssh -p 2223 vboxuser@127.0.0.1` (NAT forwarding) |
| VM3 k3s | `ssh -p 2222 vboxuser@127.0.0.1` (NAT forwarding) |

> **Mot de passe** : `Weyde@1973` pour tous les accès SSH.

### VirtualBox NAT Port Forwarding

| VM | Port hôte | Port guest | Service |
|---|---|---|---|
| VM2 docker-env | `127.0.0.1:2223` | `:22` | SSH |
| VM3 ubuntu_demo | `127.0.0.1:2222` | `:22` | SSH |

---

## 3. Hôte Linux

### Prometheus

- **Binaire** : `/usr/bin/prometheus`
- **Config** : `/etc/prometheus/prometheus.yml`
- **Config source** : `monitoring/prometheus.yml` (ce repo)
- **Port** : `9090`
- **UI** : `http://localhost:9090/classic/targets`
- **Service** : `systemctl status prometheus`

> Après chaque modification de `monitoring/prometheus.yml`, copier et recharger :
> ```bash
> sudo cp monitoring/prometheus.yml /etc/prometheus/prometheus.yml
> sudo systemctl reload prometheus
> ```

### Grafana

- **Binaire** : `/usr/share/grafana/bin/grafana`
- **Config** : `/etc/grafana/grafana.ini`
- **Data** : `/var/lib/grafana/`
- **Logs** : `/var/log/grafana/`
- **Port** : `3000`
- **UI** : `http://localhost:3000`
- **Credentials** : `admin` / `admin`
- **Service** : `systemctl status grafana-server`

### Dashboards Grafana

| Dashboard | UID | URL |
|---|---|---|
| VM1 Windows Ressources | `windows-vm1-resources` | `http://localhost:3000/d/windows-vm1-resources` |
| VM2 Docker Système & FastAPI | `vm2-docker-fastapi` | `http://localhost:3000/d/vm2-docker-fastapi` |
| VM3 k3s Système & FastAPI | `vm3-k3s-fastapi` | `http://localhost:3000/d/vm3-k3s-fastapi` |

---

## 4. VM1 — Windows (Monolith)

### Informations générales

| Propriété | Valeur |
|---|---|
| **Nom VirtualBox** | `winserv00` |
| **OS** | Windows Server |
| **IP** | `192.168.56.102` |
| **SSH** | `vboxuser@192.168.56.102:22` |
| **RAM** | 2 GB |

### Application — HealthInsuranceAPI

| Propriété | Valeur |
|---|---|
| **Gestionnaire** | NSSM (Non-Sucking Service Manager) |
| **Binaire NSSM** | `C:\ProgramData\chocolatey\lib\NSSM\tools\nssm.exe` |
| **Runtime** | `C:\health-insurance-demo\.venv\Scripts\python.exe` |
| **Commande** | `python -m uvicorn app.main:app --host 0.0.0.0 --port 8001` |
| **Répertoire** | `C:\health-insurance-demo` |
| **Port** | `8001` |
| **Log stdout** | `C:\health-insurance-demo\logs\app.log` |
| **Log stderr** | `C:\health-insurance-demo\logs\error.log` |
| **Démarrage** | Automatique (au boot Windows) |
| **Restart** | Automatique en cas de crash |

### Monitoring — windows_exporter

| Propriété | Valeur |
|---|---|
| **Binaire** | `C:\Program Files\windows_exporter\windows_exporter.exe` |
| **Port** | `9182` |
| **Collecteurs actifs** | `cpu, memory, logical_disk, net, os, service, process` |
| **Version** | `0.27.2` |
| **Démarrage** | Automatique |
| **Métriques clés** | `windows_cpu_time_total`, `windows_memory_available_bytes`, `windows_os_visible_memory_bytes`, `windows_logical_disk_*`, `windows_net_*`, `windows_service_state` |

> **Important** : windows_exporter v0.27.2 n'expose **pas** les métriques `windows_cs_*`. Utiliser `windows_os_visible_memory_bytes` pour la RAM totale.

### Endpoints

| Endpoint | URL |
|---|---|
| API root | `http://192.168.56.102:8001/` |
| Health check | `http://192.168.56.102:8001/health` |
| Métriques Prometheus | `http://192.168.56.102:8001/metrics` |
| Windows Exporter | `http://192.168.56.102:9182/metrics` |

---

## 5. VM2 — Docker

### Informations générales

| Propriété | Valeur |
|---|---|
| **Nom VirtualBox** | `docker-env` |
| **OS** | Ubuntu 24.04 (clone de `ubuntu_demo`) |
| **IP host-only** | `192.168.56.103` (statique, définie dans netplan) |
| **IP NAT** | `10.0.2.15` |
| **SSH** | `vboxuser@127.0.0.1 -p 2223` |
| **RAM** | 2 GB |
| **Disque** | 9.9 GB |

### Configuration réseau (netplan)

Fichier : `/etc/netplan/99-hostonly.yaml`
```yaml
network:
  version: 2
  ethernets:
    enp0s8:
      dhcp4: false
      addresses:
        - 192.168.56.103/24
```

### Application — Docker container

| Propriété | Valeur |
|---|---|
| **Image** | `health-insurance-api:latest` |
| **Nom container** | `health-insurance-api` |
| **Port hôte VM** | `8002` |
| **Port container** | `8003` |
| **Restart policy** | `always` (redémarre au boot Docker) |
| **Commande de lancement** | `uvicorn app.main:app --host 0.0.0.0 --port 8003` |

### Docker

| Propriété | Valeur |
|---|---|
| **Version** | `29.4.3` |
| **Service** | `docker.service` (systemd) |
| **Socket** | `/var/run/docker.sock` |
| **Data root** | `/var/lib/docker/` |

### Monitoring — node_exporter

| Propriété | Valeur |
|---|---|
| **Package** | `prometheus-node-exporter` (apt) |
| **Port** | `9100` |
| **Service** | `prometheus-node-exporter.service` (systemd) |

### Endpoints

| Endpoint | URL |
|---|---|
| API root | `http://192.168.56.103:8002/` |
| Health check | `http://192.168.56.103:8002/health` |
| Métriques Prometheus | `http://192.168.56.103:8002/metrics` |
| Node Exporter | `http://192.168.56.103:9100/metrics` |

---

## 6. VM3 — k3s (Kubernetes)

### Informations générales

| Propriété | Valeur |
|---|---|
| **Nom VirtualBox** | `ubuntu_demo` |
| **Hostname** | `ubuntudemo` |
| **OS** | Ubuntu 24.04 |
| **IP host-only** | `192.168.56.101` (statique, netplan) |
| **IP NAT** | `10.0.2.15` |
| **SSH** | `vboxuser@127.0.0.1 -p 2222` |
| **RAM** | 2 GB |
| **Disque** | 9.9 GB |

### k3s

| Propriété | Valeur |
|---|---|
| **Version** | `v1.35.4+k3s1` |
| **Rôle** | `control-plane` (single node) |
| **Service** | `k3s.service` (systemd) |
| **Binaire** | `/usr/local/bin/k3s` |
| **Config kubectl** | `/etc/rancher/k3s/k3s.yaml` |
| **Data** | `/var/lib/rancher/k3s/` |
| **CNI** | Flannel (intégré) |
| **Ingress** | Traefik (intégré) |

### Application — Kubernetes

Fichier manifeste : `k8s/deployment.yaml`

```
Deployment : health-insurance-api
  replicas  : 1
  image     : health-insurance-api:latest (importée dans containerd)
  port      : 8003 (container)

Service : health-insurance-api
  type      : NodePort
  port      : 8003
  nodePort  : 30003   ← accessible depuis l'hôte sur 192.168.56.101:30003
```

### Pods système k3s

| Pod | Rôle |
|---|---|
| `coredns` | DNS interne cluster |
| `traefik` | Ingress controller |
| `local-path-provisioner` | Stockage persistant local |
| `metrics-server` | Métriques Kubernetes (kubectl top) |
| `svclb-traefik` | Load balancer Traefik |

### Image Docker dans containerd

L'image a été buildée sur l'hôte puis importée :
```bash
# Sur l'hôte
docker build -t health-insurance-api:latest .
docker save health-insurance-api:latest -o /tmp/health-insurance-api.tar

# Sur la VM k3s
sudo k3s ctr images import /tmp/health-insurance-api.tar
```

### Monitoring — node_exporter

| Propriété | Valeur |
|---|---|
| **Package** | `prometheus-node-exporter` (apt) |
| **Port** | `9100` |
| **Service** | `prometheus-node-exporter.service` (systemd) |

### Endpoints

| Endpoint | URL |
|---|---|
| API root | `http://192.168.56.101:30003/` |
| Health check | `http://192.168.56.101:30003/health` |
| Métriques Prometheus | `http://192.168.56.101:30003/metrics` |
| Node Exporter | `http://192.168.56.101:9100/metrics` |

---

## 7. Monitoring : Prometheus & Grafana

### Comment ça fonctionne (arrière-plan)

```
┌──────────────────────────────────────────────────────────┐
│  Toutes les 15 secondes, Prometheus "scrape" chaque cible│
│                                                          │
│  Cible → GET /metrics → texte Prometheus format          │
│                       → stocké dans TSDB (time series DB)│
│                       → /var/lib/prometheus/             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Grafana interroge Prometheus via PromQL                 │
│                                                          │
│  Panel → requête PromQL → Prometheus API /api/v1/query   │
│                        → données JSON                    │
│                        → graphique affiché               │
└──────────────────────────────────────────────────────────┘
```

### Targets Prometheus (`monitoring/prometheus.yml`)

| Job | Target | Labels |
|---|---|---|
| `vm1-windows-system` | `192.168.56.102:9182` | `env=vm1-monolith, os=windows` |
| `vm1-fastapi` | `192.168.56.102:8001` | `env=vm1-monolith, app=fastapi` |
| `vm2-docker-system` | `192.168.56.103:9100` | `env=vm2-docker, os=linux` |
| `vm2-fastapi` | `192.168.56.103:8002` | `env=vm2-docker, app=fastapi` |
| `vm3-k3s-system` | `192.168.56.101:9100` | `env=vm3-k3s, os=linux` |
| `vm3-fastapi` | `192.168.56.101:30003` | `env=vm3-k3s, app=fastapi` |

### Métriques clés par type

**FastAPI (toutes VMs)** — exposées par `prometheus-fastapi-instrumentator` :
- `http_requests_total{handler, method, status}` — compteur de requêtes
- `http_request_duration_seconds_bucket` — histogramme latences

**Linux node_exporter** (VM2 + VM3) :
- `node_cpu_seconds_total{mode}` — temps CPU par mode
- `node_memory_MemTotal_bytes / MemAvailable_bytes` — RAM
- `node_filesystem_size_bytes / avail_bytes` — disque
- `node_network_receive/transmit_bytes_total` — réseau
- `node_disk_read/written_bytes_total` — I/O disque

**Windows exporter** (VM1) :
- `windows_cpu_time_total{mode}` — CPU
- `windows_os_visible_memory_bytes` — RAM totale
- `windows_memory_available_bytes` — RAM disponible
- `windows_logical_disk_size/free_bytes` — disque
- `windows_net_bytes_received/sent_total` — réseau
- `windows_service_state` — état des services

---

## 8. Guide CLI complet

### 8.1 Gestion des VMs VirtualBox

```bash
# Lister toutes les VMs
VBoxManage list vms

# Lister les VMs en cours d'exécution
VBoxManage list runningvms

# Démarrer une VM
VBoxManage startvm "docker-env" --type headless
VBoxManage startvm "ubuntu_demo" --type headless
VBoxManage startvm "winserv00" --type headless

# Arrêter une VM proprement
VBoxManage controlvm "docker-env" acpipowerbutton
VBoxManage controlvm "ubuntu_demo" acpipowerbutton
VBoxManage controlvm "winserv00" acpipowerbutton

# Forcer l'arrêt
VBoxManage controlvm "docker-env" poweroff

# État d'une VM
VBoxManage showvminfo "docker-env" --machinereadable | grep VMState

# Snapshot
VBoxManage snapshot "ubuntu_demo" take "avant-modif"
VBoxManage snapshot "ubuntu_demo" list
VBoxManage snapshot "ubuntu_demo" restore "avant-modif"
```

### 8.2 Connexion SSH

```bash
# VM1 — Windows
ssh vboxuser@192.168.56.102
# ou avec sshpass
sshpass -p 'Weyde@1973' ssh -o StrictHostKeyChecking=no vboxuser@192.168.56.102

# VM2 — Docker
sshpass -p 'Weyde@1973' ssh -o StrictHostKeyChecking=no -p 2223 vboxuser@127.0.0.1

# VM3 — k3s
sshpass -p 'Weyde@1973' ssh -o StrictHostKeyChecking=no -p 2222 vboxuser@127.0.0.1
```

### 8.3 Vérification des services — VM1 Windows

```bash
# Se connecter à Windows
sshpass -p 'Weyde@1973' ssh -o StrictHostKeyChecking=no vboxuser@192.168.56.102

# Statut des services
sc query HealthInsuranceAPI
sc query windows_exporter

# Démarrer / Arrêter / Redémarrer
sc start HealthInsuranceAPI
sc stop HealthInsuranceAPI
net stop HealthInsuranceAPI && net start HealthInsuranceAPI

# Voir les logs (dernières 50 lignes)
powershell -Command "Get-Content C:\health-insurance-demo\logs\app.log -Tail 50"
powershell -Command "Get-Content C:\health-insurance-demo\logs\error.log -Tail 50"

# Suivre les logs en temps réel
powershell -Command "Get-Content C:\health-insurance-demo\logs\app.log -Wait -Tail 10"

# Health check
curl http://localhost:8001/health

# Métriques
curl http://localhost:8001/metrics
curl http://localhost:9182/metrics | findstr "windows_memory\|windows_cpu"
```

### 8.4 Vérification des services — VM2 Docker

```bash
# Se connecter
sshpass -p 'Weyde@1973' ssh -o StrictHostKeyChecking=no -p 2223 vboxuser@127.0.0.1

# Statut Docker
sudo systemctl status docker
sudo systemctl status prometheus-node-exporter

# Lister les containers
docker ps
docker ps -a  # inclus les stoppés

# Logs du container
docker logs health-insurance-api
docker logs -f health-insurance-api          # suivre en temps réel
docker logs --tail 50 health-insurance-api   # 50 dernières lignes

# Démarrer / Arrêter le container
docker stop health-insurance-api
docker start health-insurance-api
docker restart health-insurance-api

# Statistiques ressources du container (CPU, RAM, réseau)
docker stats health-insurance-api
docker stats --no-stream health-insurance-api  # snapshot unique

# Inspecter le container
docker inspect health-insurance-api

# Entrer dans le container
docker exec -it health-insurance-api bash

# Health check
curl http://localhost:8002/health

# Métriques
curl http://localhost:8002/metrics
curl http://localhost:9100/metrics | grep node_memory
```

### 8.5 Vérification des services — VM3 k3s

```bash
# Se connecter
sshpass -p 'Weyde@1973' ssh -o StrictHostKeyChecking=no -p 2222 vboxuser@127.0.0.1

# Statut k3s
sudo systemctl status k3s
sudo systemctl status prometheus-node-exporter

# Pods
sudo kubectl get pods -A
sudo kubectl get pods -n default
sudo kubectl get pods -n default -o wide  # avec IP et nœud

# Services
sudo kubectl get svc -n default

# Détail d'un pod
sudo kubectl describe pod -l app=health-insurance-api -n default

# Logs du pod
sudo kubectl logs -l app=health-insurance-api -n default
sudo kubectl logs -f -l app=health-insurance-api -n default  # temps réel
sudo kubectl logs --tail=50 -l app=health-insurance-api -n default

# Redémarrer le pod (suppression → recréation auto)
sudo kubectl rollout restart deployment/health-insurance-api -n default

# Statut du rollout
sudo kubectl rollout status deployment/health-insurance-api -n default

# Ressources utilisées par les pods (nécessite metrics-server)
sudo kubectl top pods -n default
sudo kubectl top nodes

# Images dans containerd
sudo k3s ctr images ls | grep health

# Health check
curl http://localhost:30003/health

# Métriques
curl http://localhost:30003/metrics
curl http://localhost:9100/metrics | grep node_memory
```

### 8.6 Mesurer les ressources depuis l'hôte

```bash
# ── CPU & RAM de toutes les VMs via Prometheus ──

# CPU % VM1 Windows
curl -s 'http://localhost:9090/api/v1/query?query=100-(avg(irate(windows_cpu_time_total{mode="idle",instance="192.168.56.102:9182"}[2m]))*100)' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('CPU VM1:', d['data']['result'][0]['value'][1], '%')"

# CPU % VM2 Docker
curl -s 'http://localhost:9090/api/v1/query?query=100-(avg(irate(node_cpu_seconds_total{mode="idle",instance="192.168.56.103:9100"}[2m]))*100)' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('CPU VM2:', d['data']['result'][0]['value'][1], '%')"

# CPU % VM3 k3s
curl -s 'http://localhost:9090/api/v1/query?query=100-(avg(irate(node_cpu_seconds_total{mode="idle",instance="192.168.56.101:9100"}[2m]))*100)' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('CPU VM3:', d['data']['result'][0]['value'][1], '%')"

# RAM disponible VM2
curl -s 'http://localhost:9090/api/v1/query?query=node_memory_MemAvailable_bytes{instance="192.168.56.103:9100"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); v=int(d['data']['result'][0]['value'][1]); print(f'RAM dispo VM2: {v/1024/1024:.0f} MB')"

# ── Statut de tous les targets Prometheus ──
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import sys, json
d = json.load(sys.stdin)
for t in sorted(d['data']['activeTargets'], key=lambda x: x['labels'].get('job','')):
    icon = '✓' if t['health'] == 'up' else '✗'
    print(f\"{icon} {t['labels'].get('job','?'):30s} {t['health']:6s}  {t['scrapeUrl']}\")
"

# ── Health checks de toutes les APIs ──
for url in \
  "http://192.168.56.102:8001/health" \
  "http://192.168.56.103:8002/health" \
  "http://192.168.56.101:30003/health"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  result=$(curl -s "$url")
  echo "$url → HTTP $status | $result"
done
```

### 8.7 Gestion du monitoring (hôte)

```bash
# Statut Prometheus et Grafana
sudo systemctl status prometheus
sudo systemctl status grafana-server

# Recharger la config Prometheus sans interruption
sudo cp monitoring/prometheus.yml /etc/prometheus/prometheus.yml
sudo systemctl reload prometheus

# Redémarrer les services
sudo systemctl restart prometheus
sudo systemctl restart grafana-server

# Voir les logs Prometheus
sudo journalctl -u prometheus -f
sudo journalctl -u prometheus -n 50

# Voir les logs Grafana
sudo journalctl -u grafana-server -f
sudo tail -f /var/log/grafana/grafana.log

# Tester une requête PromQL
curl -s 'http://localhost:9090/api/v1/query?query=up' | python3 -m json.tool

# Lister les métriques disponibles
curl -s http://localhost:9090/api/v1/label/__name__/values | python3 -c \
  "import sys,json; [print(m) for m in json.load(sys.stdin)['data'] if 'windows' in m]"
```

### 8.8 Déploiement et mise à jour de l'app

```bash
# ── Rebuilder et redéployer sur Docker (VM2) ──

# 1. Builder l'image sur l'hôte
docker build -t health-insurance-api:latest .

# 2. Sauvegarder et transférer
docker save health-insurance-api:latest -o /tmp/health-insurance-api.tar
sshpass -p 'Weyde@1973' scp -P 2223 /tmp/health-insurance-api.tar vboxuser@127.0.0.1:/tmp/

# 3. Déployer sur VM2
sshpass -p 'Weyde@1973' ssh -p 2223 vboxuser@127.0.0.1 "
  sudo docker load -i /tmp/health-insurance-api.tar
  sudo docker stop health-insurance-api
  sudo docker rm health-insurance-api
  sudo docker run -d --name health-insurance-api --restart always -p 8002:8003 health-insurance-api:latest
"

# ── Redéployer sur k3s (VM3) ──

# 1. Transférer l'image
sshpass -p 'Weyde@1973' scp -P 2222 /tmp/health-insurance-api.tar vboxuser@127.0.0.1:/tmp/

# 2. Importer dans containerd
sshpass -p 'Weyde@1973' ssh -p 2222 vboxuser@127.0.0.1 "
  echo 'Weyde@1973' | sudo -S k3s ctr images import /tmp/health-insurance-api.tar
  sudo kubectl rollout restart deployment/health-insurance-api -n default
  sudo kubectl rollout status deployment/health-insurance-api -n default
"

# ── Mise à jour Windows (VM1) ──
# Arrêter le service, mettre à jour les fichiers, redémarrer
sshpass -p 'Weyde@1973' ssh vboxuser@192.168.56.102 "
  sc stop HealthInsuranceAPI
  REM ... copier les nouveaux fichiers ...
  sc start HealthInsuranceAPI
"
```

### 8.9 Dépannage rapide

```bash
# Un target Prometheus est DOWN → vérifier la connectivité
ping 192.168.56.102
curl -v http://192.168.56.102:8001/health

# Container Docker redémarre en boucle → voir les logs
sshpass -p 'Weyde@1973' ssh -p 2223 vboxuser@127.0.0.1 "docker logs --tail 30 health-insurance-api"

# Pod k3s en CrashLoopBackOff → inspecter
sshpass -p 'Weyde@1973' ssh -p 2222 vboxuser@127.0.0.1 "
  echo 'Weyde@1973' | sudo -S kubectl describe pod -l app=health-insurance-api -n default
  sudo kubectl logs -l app=health-insurance-api -n default --previous
"

# node_exporter ne démarre pas → port déjà utilisé
sshpass -p 'Weyde@1973' ssh -p 2222 vboxuser@127.0.0.1 "
  echo 'Weyde@1973' | sudo -S ss -tlnp sport = :9100
  # Si un process orphelin occupe le port
  sudo kill <PID>
  sudo systemctl reset-failed prometheus-node-exporter
  sudo systemctl start prometheus-node-exporter
"

# Grafana ne répond plus → redémarrer
sudo systemctl restart grafana-server

# Vérifier l'espace disque sur toutes les VMs
for port in 2222 2223; do
  sshpass -p 'Weyde@1973' ssh -p $port vboxuser@127.0.0.1 "echo '=== Port $port ===' && df -h /"
done
sshpass -p 'Weyde@1973' ssh vboxuser@192.168.56.102 "dir C:\ /-c" 2>/dev/null
```

---

## Résumé des ports

| Service | VM | Port | Protocol |
|---|---|---|---|
| SSH | VM1 Windows | `192.168.56.102:22` | TCP |
| SSH | VM2 Docker | `127.0.0.1:2223` → `:22` | TCP (NAT) |
| SSH | VM3 k3s | `127.0.0.1:2222` → `:22` | TCP (NAT) |
| FastAPI | VM1 Windows | `192.168.56.102:8001` | HTTP |
| FastAPI | VM2 Docker | `192.168.56.103:8002` | HTTP |
| FastAPI | VM3 k3s | `192.168.56.101:30003` | HTTP (NodePort) |
| windows_exporter | VM1 | `192.168.56.102:9182` | HTTP |
| node_exporter | VM2 | `192.168.56.103:9100` | HTTP |
| node_exporter | VM3 | `192.168.56.101:9100` | HTTP |
| Prometheus | Hôte | `localhost:9090` | HTTP |
| Grafana | Hôte | `localhost:3000` | HTTP |
