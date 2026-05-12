# Audit & Analyse des Métriques — Comparaison des 3 Environnements

> Données collectées en conditions réelles via Prometheus (moyenne sur 5 minutes).
> Date : 2026-05-12

---

## Table des matières

1. [Résumé exécutif](#1-résumé-exécutif)
2. [Comparaison CPU](#2-comparaison-cpu)
3. [Comparaison RAM](#3-comparaison-ram)
4. [Comparaison Disque](#4-comparaison-disque)
5. [Comparaison Réseau](#5-comparaison-réseau)
6. [Comparaison Applicative (FastAPI)](#6-comparaison-applicative-fastapi)
7. [Analyse de l'overhead par technologie](#7-analyse-de-loverhead-par-technologie)
8. [Tableau de score global](#8-tableau-de-score-global)
9. [Conclusion & Recommandations](#9-conclusion--recommandations)

---

## 1. Résumé exécutif

| Métrique | VM1 Windows (NSSM) | VM2 Docker | VM3 k3s | Gagnant |
|---|---|---|---|---|
| CPU | 6.3 % | 15.9 % | 37.9 % | **VM1** |
| RAM utilisée | 722 MB (35.3 %) | 567 MB (28.8 %) | 1098 MB (55.8 %) | **VM2** |
| Disque utilisé | 12.9 GB / 30 GB | 5.2 GB / 9.9 GB | 5.8 GB / 9.9 GB | **VM2** |
| Réseau RX | 0.11 KB/s | 1.29 KB/s | 8.21 KB/s | **VM1** |
| Réseau TX | 2.78 KB/s | 1.56 KB/s | 6.72 KB/s | **VM2** |
| Overhead technologie | Faible | Faible | Très élevé | **VM1/VM2** |

**Vainqueur global : VM2 Docker** — meilleur équilibre RAM / CPU / disque / simplicité opérationnelle.

---

## 2. Comparaison CPU

### Données mesurées

| Environnement | CPU moyen (5 min) | Détail |
|---|---|---|
| VM1 Windows (NSSM) | **6.3 %** | Process uvicorn uniquement + Windows background tasks |
| VM2 Docker | **15.9 %** | Docker daemon + containerd + container uvicorn |
| VM3 k3s | **37.9 %** | k3s + kubelet + traefik + coredns + metrics-server + pod uvicorn |

### Visualisation

```
VM1 Windows ████░░░░░░░░░░░░░░░░  6.3 %
VM2 Docker  ████████░░░░░░░░░░░░ 15.9 %
VM3 k3s     ███████████████████░ 37.9 %
            0%                  40%
```

### Analyse

**VM1 Windows — 6.3 %** ✓ Le plus léger
- L'application tourne directement comme un processus Windows via NSSM
- Pas de couche de virtualisation supplémentaire
- Faible nombre de processus système actifs liés à l'app
- Le CPU Windows de base tourne à ~5-7 % au repos

**VM2 Docker — 15.9 %** ✓ Acceptable
- Surcoût du daemon Docker (~1-3 %) et containerd
- Le container ajoute une légère abstraction réseau (iptables, namespaces)
- Reste raisonnable et prévisible

**VM3 k3s — 37.9 %** ✗ Le plus coûteux
- k3s doit faire tourner l'ensemble du plan de contrôle Kubernetes :
  - `kubelet` : gestion des pods (~5-8 % CPU)
  - `traefik` : ingress controller (~3-5 %)
  - `coredns` : résolution DNS interne (~2-3 %)
  - `metrics-server` : collecte des métriques k8s (~2-3 %)
  - `local-path-provisioner` : gestion stockage (~1-2 %)
- Ces composants systèmes sont **incompressibles** et tournent même si l'application est au repos

> **Cause principale du CPU élevé sur k3s** : les composants système Kubernetes ne s'arrêtent jamais. Sur une VM avec 1 seul CPU, cette contention est très visible.

---

## 3. Comparaison RAM

### Données mesurées

| Environnement | RAM Totale | RAM Utilisée | RAM Libre | % Utilisé |
|---|---|---|---|---|
| VM1 Windows (NSSM) | 2048 MB | **723 MB** | 1325 MB | **35.3 %** |
| VM2 Docker | 1968 MB | **567 MB** | 1401 MB | **28.8 %** |
| VM3 k3s | 1968 MB | **1098 MB** | 870 MB | **55.8 %** |

### Visualisation

```
VM1 Windows [███████████░░░░░░░░░░░░░░░░░░░░] 35.3 %  (723 MB)
VM2 Docker  [█████████░░░░░░░░░░░░░░░░░░░░░░] 28.8 %  (567 MB)
VM3 k3s     [████████████████████░░░░░░░░░░░] 55.8 % (1098 MB)
             0%                              100%
```

### Décomposition estimée de la RAM par composant

**VM1 Windows — 723 MB**
```
Système Windows (services core)   ~400 MB
uvicorn / FastAPI                  ~80 MB
NSSM + monitoring                  ~20 MB
Cache système                     ~220 MB
```

**VM2 Docker — 567 MB** ← le plus efficace
```
Ubuntu OS (minimal)               ~200 MB
Docker daemon + containerd        ~150 MB
Container uvicorn / FastAPI        ~80 MB
Cache système                     ~137 MB
```

**VM3 k3s — 1098 MB**
```
Ubuntu OS                         ~200 MB
k3s (kubelet + API server)        ~350 MB
traefik                            ~80 MB
coredns                            ~60 MB
metrics-server                     ~50 MB
local-path-provisioner             ~40 MB
Pod uvicorn / FastAPI              ~80 MB
Cache système                     ~238 MB
```

### Analyse

**VM2 Docker — 567 MB** est le grand gagnant RAM.
- Linux est nativement plus léger que Windows
- Docker ajoute ~150 MB de surcoût (daemon + containerd)
- L'application dans le container est isolée mais partage le kernel hôte

**VM1 Windows — 723 MB** malgré sa gestion directe des processus, Windows OS consomme plus de RAM de base que Linux (~400 MB vs ~200 MB).

**VM3 k3s — 1098 MB** est clairement défavorisé sur une VM de 2 GB :
- Le plan de contrôle Kubernetes consomme ~580 MB juste pour faire fonctionner le cluster
- Il reste seulement ~870 MB pour l'application et le cache
- Sur une VM 2 GB, k3s est en situation de **memory pressure**

> **Règle pratique** : k3s nécessite minimum 2 GB de RAM pour le control-plane seul. Pour production, prévoir 4 GB minimum.

---

## 4. Comparaison Disque

### Données mesurées

| Environnement | Total | Utilisé | Libre | % Utilisé |
|---|---|---|---|---|
| VM1 Windows | 30.1 GB | 12.9 GB | 17.2 GB | **43.0 %** |
| VM2 Docker | 9.9 GB | 5.2 GB | 4.7 GB | **52.3 %** |
| VM3 k3s | 9.9 GB | 5.8 GB | 4.1 GB | **58.4 %** |

### Visualisation

```
VM1 Windows [█████████████░░░░░░░░░░░░░░░░░] 43.0 % de 30 GB  → 12.9 GB
VM2 Docker  [████████████████░░░░░░░░░░░░░░] 52.3 % de  9.9 GB →  5.2 GB
VM3 k3s     [██████████████████░░░░░░░░░░░░] 58.4 % de  9.9 GB →  5.8 GB
```

### Analyse

**En valeur absolue** : VM2 Docker utilise le moins d'espace (5.2 GB).

**En pourcentage** : VM1 Windows utilise le moins (43 %) mais sur un disque 3x plus grand.

**VM3 k3s — 5.8 GB** (le plus élevé des deux Linux) :
- L'image Docker importée dans containerd occupe ~180 MB supplémentaires (le format OCI de containerd diffère du Docker layer cache)
- Les logs k3s et les données etcd s'accumulent dans `/var/lib/rancher/k3s/`
- Traefik et les autres images système occupent ~500 MB supplémentaires

**VM2 Docker — 5.2 GB** :
- Les layers Docker sont déduplicables entre containers
- Pas de composants système supplémentaires liés à k3s

> **Point d'attention** : les deux VMs Linux ont seulement 4-4.7 GB libres. Les logs applicatifs et les images Docker/containerd peuvent remplir rapidement le disque. Prévoir un volume disque plus grand en production (minimum 20 GB).

---

## 5. Comparaison Réseau

### Données mesurées (KB/s, moyenne 5 min)

| Environnement | Réception (RX) | Émission (TX) | Total |
|---|---|---|---|
| VM1 Windows | 0.11 KB/s | 2.78 KB/s | **2.89 KB/s** |
| VM2 Docker | 1.29 KB/s | 1.56 KB/s | **2.85 KB/s** |
| VM3 k3s | 8.21 KB/s | 6.72 KB/s | **14.93 KB/s** |

### Visualisation

```
VM1 Windows RX ░ 0.11    TX ██ 2.78   Total:  2.89 KB/s
VM2 Docker  RX █ 1.29    TX █ 1.56    Total:  2.85 KB/s
VM3 k3s     RX ████ 8.21 TX ████ 6.72 Total: 14.93 KB/s
```

### Analyse

**VM1 et VM2** ont un trafic réseau équivalent (~3 KB/s), constitué principalement des scrapes Prometheus (toutes les 15s).

**VM3 k3s — 14.93 KB/s** génère 5× plus de trafic réseau :
- Communication interne entre les composants k3s (kubelet ↔ API server ↔ etcd)
- Health checks des pods par kubelet (toutes les 10s par défaut)
- Gossip protocol et synchronisation d'état du cluster
- Métriques internes metrics-server → API server

Ce trafic réseau interne est **invisible depuis l'extérieur** mais consomme de la bande passante sur l'interface host-only.

> **En production** sur un cluster multi-nœuds, ce trafic east-west (entre nœuds) peut représenter des dizaines de MB/s supplémentaires.

---

## 6. Comparaison Applicative (FastAPI)

### Données mesurées

| Métrique | VM1 Windows | VM2 Docker | VM3 k3s |
|---|---|---|---|
| Requêtes/s | 0.067 | 0.067 | 0.200 |
| Latence p50 | ~50 ms* | ~50 ms* | ~50 ms* |
| Latence p99 | ~99 ms* | ~99 ms* | ~99 ms* |

> *Les valeurs de latence reflètent les buckets de l'histogramme Prometheus par défaut en l'absence de charge réelle. Les vraies latences en idle sont <5 ms. Pour des mesures précises, il faudrait un benchmark de charge (ex: k6, wrk, locust).

### Requêtes reçues

- **VM1 et VM2** : 0.067 req/s → uniquement le scrape Prometheus toutes les 15s
- **VM3 k3s** : 0.200 req/s → scrape Prometheus + health checks kubelet (liveness/readiness probes toutes les 10s)

### Ce que les health checks k3s ajoutent

k3s effectue automatiquement des vérifications sur chaque pod :
```yaml
livenessProbe:   # toutes les 30s → kubelet vérifie GET /health
readinessProbe:  # toutes les 10s → kubelet vérifie GET /health
```
Ces requêtes automatiques n'existent pas sur VM1 et VM2 — elles sont propres à Kubernetes.

### Impact de la couche réseau

| Couche réseau | VM1 | VM2 | VM3 |
|---|---|---|---|
| Accès direct | ✓ Port 8001 | Via iptables NAT (8002→8003) | Via kube-proxy (NodePort 30003→8003) |
| Surcoût réseau | Aucun | Minime (~0.1 ms) | Modéré (kube-proxy + iptables) |
| Équilibrage de charge | ❌ Manuel | ❌ Manuel | ✓ Automatique (round-robin si >1 replica) |

---

## 7. Analyse de l'overhead par technologie

### Qu'est-ce que l'overhead ?

L'overhead est la consommation de ressources **due à la technologie de déploiement elle-même**, pas à l'application.

### Calcul de l'overhead estimé

En considérant qu'une application Python/uvicorn au repos consomme environ :
- **CPU** : ~1-2 %
- **RAM** : ~80 MB

```
┌─────────────────────────────────────────────────────────┐
│ VM1 Windows — Overhead NSSM                             │
│                                                         │
│ CPU total    : 6.3 %                                    │
│ CPU app      : ~1.5 %                                   │
│ CPU overhead : ~4.8 % (Windows OS, services, NSSM)      │
│                                                         │
│ RAM totale   : 723 MB                                   │
│ RAM app      : ~80 MB                                   │
│ RAM overhead : ~643 MB (OS Windows + cache)             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ VM2 Docker — Overhead Docker                            │
│                                                         │
│ CPU total    : 15.9 %                                   │
│ CPU app      : ~1.5 %                                   │
│ CPU overhead : ~14.4 % (Ubuntu + Docker daemon)         │
│                                                         │
│ RAM totale   : 567 MB                                   │
│ RAM app      : ~80 MB                                   │
│ RAM overhead : ~487 MB (OS Linux + Docker + containerd) │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ VM3 k3s — Overhead Kubernetes                           │
│                                                         │
│ CPU total    : 37.9 %                                   │
│ CPU app      : ~1.5 %                                   │
│ CPU overhead : ~36.4 % (Ubuntu + k3s control-plane)     │
│                                                         │
│ RAM totale   : 1098 MB                                  │
│ RAM app      : ~80 MB                                   │
│ RAM overhead : ~1018 MB (OS + k3s + pods système)       │
└─────────────────────────────────────────────────────────┘
```

### Pourquoi k3s est si coûteux sur une petite VM ?

k3s est conçu pour être **léger** comparé à Kubernetes complet — mais il reste un orchestrateur complet. Sur une VM à 2 GB RAM avec 1 CPU :

```
Pods système obligatoires k3s :
  coredns              → 60 MB RAM,  2-3 % CPU
  traefik              → 80 MB RAM,  3-5 % CPU
  metrics-server       → 50 MB RAM,  2-3 % CPU
  local-path-prov.     → 40 MB RAM,  1-2 % CPU
  svclb-traefik        → 20 MB RAM,  <1 % CPU
  kubelet (k3s)        → 350 MB RAM, 5-8 % CPU
                       ────────────────────────
  TOTAL overhead k3s   → 600 MB RAM, 14-22 % CPU
```

**k3s est rentable seulement quand :**
- Tu déploies **plusieurs applications** sur le même cluster (partage de l'overhead)
- Tu as besoin de **haute disponibilité** (redémarrage auto, rolling updates)
- Tu as une infrastructure avec **plusieurs nœuds** (le control-plane est amorti)

---

## 8. Tableau de score global

Notation de 1 (mauvais) à 5 (excellent) par critère.

| Critère | Poids | VM1 Windows | VM2 Docker | VM3 k3s |
|---|---|---|---|---|
| CPU idle | 20% | ⭐⭐⭐⭐⭐ 5 | ⭐⭐⭐⭐ 4 | ⭐⭐ 2 |
| RAM idle | 20% | ⭐⭐⭐⭐ 4 | ⭐⭐⭐⭐⭐ 5 | ⭐⭐ 2 |
| Disque | 10% | ⭐⭐⭐⭐ 4 | ⭐⭐⭐⭐⭐ 5 | ⭐⭐⭐ 3 |
| Réseau overhead | 10% | ⭐⭐⭐⭐⭐ 5 | ⭐⭐⭐⭐ 4 | ⭐⭐ 2 |
| Simplicité déploiement | 15% | ⭐⭐⭐ 3 | ⭐⭐⭐⭐ 4 | ⭐⭐ 2 |
| Scalabilité | 10% | ⭐ 1 | ⭐⭐⭐ 3 | ⭐⭐⭐⭐⭐ 5 |
| Haute disponibilité | 10% | ⭐ 1 | ⭐⭐ 2 | ⭐⭐⭐⭐⭐ 5 |
| Portabilité | 5% | ⭐ 1 | ⭐⭐⭐⭐⭐ 5 | ⭐⭐⭐⭐ 4 |

### Score pondéré

```
VM1 Windows : (5×0.20)+(4×0.20)+(4×0.10)+(5×0.10)+(3×0.15)+(1×0.10)+(1×0.10)+(1×0.05)
            = 1.00 + 0.80 + 0.40 + 0.50 + 0.45 + 0.10 + 0.10 + 0.05
            = 3.40 / 5

VM2 Docker  : (4×0.20)+(5×0.20)+(5×0.10)+(4×0.10)+(4×0.15)+(3×0.10)+(2×0.10)+(5×0.05)
            = 0.80 + 1.00 + 0.50 + 0.40 + 0.60 + 0.30 + 0.20 + 0.25
            = 4.05 / 5  ← GAGNANT

VM3 k3s     : (2×0.20)+(2×0.20)+(3×0.10)+(2×0.10)+(2×0.15)+(5×0.10)+(5×0.10)+(4×0.05)
            = 0.40 + 0.40 + 0.30 + 0.20 + 0.30 + 0.50 + 0.50 + 0.20
            = 2.80 / 5
```

| Environnement | Score global |
|---|---|
| **VM2 Docker** | **4.05 / 5** 🥇 |
| VM1 Windows | 3.40 / 5 🥈 |
| VM3 k3s | 2.80 / 5 🥉 |

---

## 9. Conclusion & Recommandations

### Verdict par cas d'usage

#### ✅ Choisir VM2 Docker si :
- Application unique ou petit nombre de services
- Équipe qui maîtrise Docker mais pas Kubernetes
- Ressources limitées (RAM < 4 GB par app)
- Déploiement simple et reproductible
- **C'est le meilleur rapport ressources/fonctionnalités pour ce projet**

#### ✅ Choisir VM1 Windows si :
- L'application dépend de l'écosystème Windows (.NET, COM, etc.)
- Environnement legacy déjà sur Windows Server
- CPU est la ressource la plus contrainte
- Pas besoin de portabilité entre OS

#### ✅ Choisir VM3 k3s si :
- Tu déploies **10+ microservices** sur le même cluster (l'overhead se dilue)
- Tu as besoin de rolling updates sans downtime
- Tu veux du scaling automatique (HPA)
- Tu as des VMs avec minimum 4 GB RAM
- Tu prépares une migration vers un cloud Kubernetes managé (EKS, GKE, AKS)

### Recommandations d'optimisation

**VM3 k3s — réduire la consommation :**
```bash
# Désactiver traefik si pas besoin d'ingress
# Ajouter au démarrage k3s :
--disable traefik --disable metrics-server --disable local-storage
# Économie estimée : 150-200 MB RAM, 8-12 % CPU
```

**VM2 Docker — optimiser l'image :**
```dockerfile
# Passer de python:3.11-slim (59 MB) à python:3.11-alpine (~25 MB)
FROM python:3.11-alpine
# Économie disque : ~35 MB par image
```

**VM1 Windows — gestion des logs :**
```powershell
# Rotation des logs (NSSM ne le fait pas automatiquement)
# Ajouter une tâche planifiée pour archiver app.log
```

### Tableau récapitulatif final

```
┌────────────────────┬──────────────┬──────────────┬──────────────┐
│ Ressource          │ VM1 Windows  │ VM2 Docker   │ VM3 k3s      │
├────────────────────┼──────────────┼──────────────┼──────────────┤
│ CPU idle           │ 6.3 %   ✓✓  │ 15.9 %  ✓   │ 37.9 %  ✗   │
│ RAM utilisée       │ 723 MB  ✓   │ 567 MB  ✓✓  │ 1098 MB ✗✗  │
│ Disque             │ 12.9 GB ✓   │ 5.2 GB  ✓✓  │ 5.8 GB  ✓   │
│ Réseau overhead    │ 2.9 KB/s ✓✓ │ 2.9 KB/s ✓✓ │ 14.9 KB/s ✗ │
├────────────────────┼──────────────┼──────────────┼──────────────┤
│ Score global       │ 3.40 / 5    │ 4.05 / 5 🏆 │ 2.80 / 5    │
├────────────────────┼──────────────┼──────────────┼──────────────┤
│ Idéal pour         │ Legacy Win   │ 1-10 apps    │ 10+ services │
└────────────────────┴──────────────┴──────────────┴──────────────┘

✓✓ Excellent   ✓ Bon   ✗ Insuffisant   ✗✗ Critique
```

---

*Métriques collectées via Prometheus — PromQL queries disponibles dans `monitoring/prometheus.yml`*
*Infrastructure documentée dans `INFRASTRUCTURE.md`*
