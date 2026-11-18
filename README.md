# Pearl Solo Mining Suite — RTX 50xx (Blackwell `sm120`) + WSL2 + Grafana

Suite complète de minage solo pour le réseau **Pearl (PRL)** sur GPU **NVIDIA RTX 50xx (`sm120`)** sous **WSL2**, intégrant le nœud local, la supervision (Prometheus/Grafana) et les alertes.

![Aperçu du tableau de bord Grafana Pearl Solo Mining](docs/Dashboard_Pearl.png)

## Prérequis indispensables
1. **Réseau WSL2 :** Configurez `networkingMode=mirrored` dans `C:\Users\<VotreNom>\.wslconfig` et relancez `wsl --shutdown`.
2. **Nœud `pearld` :** Exécutez le nœud v1.5.7+ sur stockage `ext4` avec `pearld.conf` configuré (identifiants RPC et IP externe), puis attendez la synchronisation complète (`pearld_chain_is_current = 1`).
3. **Port P2P `44108` & Pare-feu :** Ouvrez le port 44108 (TCP) en redirection NAT et exécutez dans PowerShell (Administrateur) :
   ```powershell
   New-NetFirewallRule -DisplayName "Pearl Node P2P" -Direction Inbound -LocalPort 44108 -Protocol TCP -Profile Any -Action Allow
   Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow
   ```
   *(Gardez le port RPC `44107` fermé vers l'extérieur).*

## Fonctionnalités & Démarrage rapide
- Support NVIDIA Blackwell (`sm120`), automatisation du mineur (`start_pearl_miner.sh`), métriques Prometheus/Grafana (exportateurs GPU `9400` et Solo `9401`), et alertes SMTP.
- **Lancement :** Configurez votre fichier `.env` via `cp .env.example .env`, démarrez la supervision avec `cd monitoring && docker compose --env-file ../.env up -d`, importez le tableau de bord Grafana, puis lancez `./start_pearl_miner.sh`.

## Crédits & Licence
- **Auteur :** [@fishhot75012](https://github.com) assisté par Google.
- **Licence :** Distribué sous licence **ISC** (voir [LICENSE](LICENSE)).
