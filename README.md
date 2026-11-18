# Pearl Solo Mining Suite — RTX 50xx (Blackwell `sm120`) + WSL2 + Grafana

Configuration complète et automatisée pour le minage solo sur le réseau **Pearl (PRL)** avec les cartes graphiques **NVIDIA GeForce RTX 50xx (`sm120`)** sous **Windows / WSL2**, incluant la supervision temps réel et les alertes de bloc trouvé.

## Fonctionnalités incluses
- **Support NVIDIA Blackwell (`sm120`) :** Adaptation du mineur vLLM (`v1.5.7-sm120`) et optimisation mémoire (`--gpu-memory-utilization 0.80`) pour GPU 16 Go (RTX 5070 Ti).
- **Démarrage automatisé (`start_pearl_miner.sh`) :** Lancement du conteneur Docker, attente du chargement du modèle en VRAM et boucle parallèle de génération.
- **Supervision complète (Prometheus + Grafana) :**
  - Métriques natives `pearld` 1.5.7 (`localhost:9105`) : hauteur de bloc, synchro, pairs P2P, appels RPC.
  - Métriques vLLM (`localhost:8000`) : débit en `tokens/s`, saturation du batch GPU.
  - Exportateur GPU léger basé sur `nvidia-smi` (`gpu_exporter.py` sur port `9400`) : contournement fiable de DCGM sous WSL2 (Température, Watts, VRAM).
  - Exportateur Solo & Probabilités (`solo_exporter.py` sur port `9401`) : comptage des blocs solo trouvés, requêtes de session et calcul dynamique du Temps Moyen Estimé (TTF).
- **Alertes Email (SMTP Grafana) :** Notification instantanée dès qu'un bloc solo est validé (`increase(pearl_solo_blocks_found[5m]) > 0`).

## Démarrage rapide
1. Copiez `.env.example` vers `.env` et renseignez vos identifiants RPC, votre adresse PRL et vos paramètres SMTP.
2. Lancez la pile de supervision :
   ```bash
   cd monitoring && docker compose --env-file ../.env up -d
   ```
3. Importez `monitoring/pearl-dashboard.json` dans Grafana (`http://localhost:3000`).
4. Démarrez le mineur :
   ```bash
   set -a && source .env && set +a
   ./start_pearl_miner.sh
   ```
