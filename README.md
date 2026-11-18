# Pearl Solo Mining Suite — RTX 50xx (Blackwell `sm120`) + WSL2 + Grafana

Configuration complète et automatisée pour le minage solo sur le réseau **Pearl (PRL)** avec les cartes graphiques **NVIDIA GeForce RTX 50xx (`sm120`)** sous **Windows / WSL2**, incluant la supervision temps réel et les alertes de bloc trouvé.

## Prérequis indispensables avant démarrage
1. **Configuration réseau WSL2 (`wslconfig.example`) :**
   - Copiez `wslconfig.example` vers `C:\Users\<VotreNom>\.wslconfig` sous Windows et exécutez `wsl --shutdown` dans PowerShell pour appliquer `networkingMode=mirrored`.
2. **Nœud `pearld` local sur la même instance WSL2 (`pearld.conf.example`) :**
   - Le nœud `pearld` (v1.5.7+) doit tourner dans **le même environnement WSL2** (sur stockage `ext4`).
   - Copiez `pearld.conf.example` vers `~/.pearld/pearld.conf` et renseignez vos identifiants RPC ainsi que votre IPv4 publique (`externalip`).
   - **Blockchain synchronisée :** Attendez que le nœud soit à 100 % synchronisé (`pearld_chain_is_current = 1`) avant de lancer le mineur.
3. **Ouverture du port P2P `44108` :**
   - Ouvrez le port **44108 (TCP)** sur votre box Internet (redirection NAT vers le PC) et dans le pare-feu Windows/Hyper-V afin d'accepter les pairs entrants (`inbound`).
   - *(Sécurité)* Gardez le port RPC **`44107`** strictement fermé vers l'extérieur (`127.0.0.1`).

## Fonctionnalités incluses
- **Support NVIDIA Blackwell (`sm120`) :** Adaptation du mineur vLLM (`v1.5.7-sm120`) et optimisation mémoire (`--gpu-memory-utilization 0.80`) pour GPU 16 Go (RTX 5070 Ti).
- **Démarrage automatisé (`start_pearl_miner.sh`) :** Lancement du conteneur Docker, attente du chargement du modèle en VRAM et boucle parallèle de génération.
- **Supervision complète (Prometheus + Grafana) :**
  - Métriques natives `pearld` 1.5.7 (`localhost:9105`) : hauteur de bloc, synchro, pairs P2P (`inbound`/`outbound`), appels RPC.
  - Métriques vLLM (`localhost:8000`) : débit en `tokens/s`, saturation du batch GPU.
  - Exportateur GPU léger basé sur `nvidia-smi` (`gpu_exporter.py` sur port `9400`) : contournement fiable de DCGM sous WSL2 (Température, Watts, VRAM).
  - Exportateur Solo & Probabilités (`solo_exporter.py` sur port `9401`) : comptage des blocs solo trouvés, requêtes de session et calcul dynamique du Temps Moyen Estimé (TTF).
- **Alertes Email (SMTP Grafana) :** Notification instantanée dès qu'un bloc solo est validé (`increase(pearl_solo_blocks_found[5m]) > 0`).

## Démarrage rapide
1. Vérifiez que votre nœud `pearld` tourne dans WSL2 et est synchronisé.
2. Copiez `.env.example` vers `.env` et renseignez vos identifiants RPC, votre adresse PRL et vos paramètres SMTP :
   ```bash
   cp .env.example .env
   ```
3. Lancez la pile de supervision :
   ```bash
   cd monitoring && docker compose --env-file ../.env up -d
   ```
4. Importez `monitoring/pearl-dashboard.json` dans Grafana (`http://localhost:3000`).
5. Démarrez le mineur :
   ```bash
   cd ..
   set -a && source .env && set +a
   ./start_pearl_miner.sh
   ```
