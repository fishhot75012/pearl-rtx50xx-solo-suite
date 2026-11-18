# Pearl Solo Mining Suite — RTX 50xx (Blackwell `sm120`) + WSL2 + Grafana

Configuration complète pour le minage solo sur le réseau **Pearl (PRL)** avec les cartes **NVIDIA GeForce RTX 50xx (`sm120`)** sous **Windows / WSL2**.

![Aperçu du tableau de bord Grafana Pearl Solo Mining](docs/Dashboard_Pearl.png)

## Prérequis & Fonctionnalités
- **Réseau WSL2 (`wslconfig.example`)** et nœud local `pearld` synchronisé.
- **Port P2P `44108`** ouvert (TCP) et port RPC `9105` sécurisé.
- **Supervision** via Prometheus, Grafana, exportateur GPU (`nvidia-smi`) et alertes SMTP.

## Crédits & Contributions
- **Auteur & Mainteneur :** [@fishhot75012](https://github.com)
- **Co-conception & Assistance technique :** IA développée par Google
