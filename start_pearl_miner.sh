#!/usr/bin/env bash
set -euo pipefail

# --- CONFIGURATION ---
CONTAINER_NAME="pearl-miner"
IMAGE_NAME="vllm_miner:v1.5.7-sm120"
MODEL_NAME="pearl-ai/Llama-3.1-8B-Instruct-pearl"
WORKERS=16

# Identifiants RPC et adresse de minage (pensez à renouveler le mot de passe dans pearld)
PEARLD_RPC_URL="http://127.0.0.1:44107"
PEARLD_RPC_USER="${PEARLD_RPC_USER:-votre_rpc_user}"
PEARLD_RPC_PASSWORD="${PEARLD_RPC_PASSWORD:-votre_rpc_password}"
PEARLD_MINING_ADDRESS="${PEARLD_MINING_ADDRESS:-prl1_votre_adresse_taproot}"

# Nettoyage propre à l'arrêt du script (Ctrl+C)
cleanup() {
    echo ""
    echo "[INFO] Arrêt de la boucle de minage et du conteneur Docker..."
    kill $(jobs -p) 2>/dev/null || true
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    echo "[INFO] Mineur arrêté proprement."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Supprimer un éventuel conteneur résiduel
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "[1/3] Démarrage du conteneur Docker ($CONTAINER_NAME)..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --gpus all \
  --network host \
  --ipc=host \
  --shm-size 8g \
  -e CUDA_MODULE_LOADING=EAGER \
  -e VLLM_USE_FLASHINFER_SAMPLER=0 \
  -e VLLM_USE_DEEP_GEMM=0 \
  -e PEARLD_RPC_URL="$PEARLD_RPC_URL" \
  -e PEARLD_RPC_USER="${PEARLD_RPC_USER:-votre_rpc_user}" \
  -e PEARLD_RPC_PASSWORD="${PEARLD_RPC_PASSWORD:-votre_rpc_password}" \
  -e PEARLD_MINING_ADDRESS="${PEARLD_MINING_ADDRESS:-prl1_votre_adresse_taproot}" \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v ~/.cache/vllm:/root/.cache/vllm -v ~/.triton:/root/.triton \
  "$IMAGE_NAME" \
    "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype bfloat16 \
    --max-model-len 1024 \
    --gpu-memory-utilization 0.75 \
	--enforce-eager \
    -cc.custom_ops='["-quant_fp8"]' >/dev/null

echo "[2/3] Attente du chargement du modèle en VRAM (peut prendre 4 à 6 min sur CPU)..."
until curl -sf http://localhost:8000/v1/models >/dev/null; do
    if ! docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo "[ERREUR] Le conteneur s'est arrêté de manière inattendue. Logs :"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    sleep 5
done

echo "[3/3] Serveur vLLM prêt ! Démarrage des $WORKERS flux parallèles de minage..."
echo "      (Appuyez sur Ctrl+C pour tout arrêter proprement)"
echo "      (Pour voir les logs complets dans un autre terminal : docker logs -f $CONTAINER_NAME)"

python3 -c "
import urllib.request, json, concurrent.futures, uuid, time

url = 'http://localhost:8000/v1/chat/completions'

def worker(_):
    while True:
        try:
            payload = json.dumps({
                'model': '$MODEL_NAME',
                'messages': [{'role': 'user', 'content': f'Request {uuid.uuid4()}: Write a comprehensive technical analysis on distributed consensus, cryptographic hash functions, and zero-knowledge proof systems.'}],
                'max_tokens': 512,
                'temperature': 0.8,
                'stream': True
            }).encode()
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as r:
                for _ in r:
                    pass
        except Exception:
            time.sleep(1)

with concurrent.futures.ThreadPoolExecutor(max_workers=$WORKERS) as ex:
    ex.map(worker, range($WORKERS))
" &


# Afficher en direct uniquement les blocs acceptés/rejetés et les statistiques de débit vLLM
docker logs -f "$CONTAINER_NAME" 2>&1 | grep --line-buffered -E "accepted|rejected|Submitting|Avg generation throughput|height"

# Mesurer le débit de tokens sur 10 secondes 
T1=$(curl -s http://localhost:8000/metrics | awk '/^vllm:generation_tokens_total/ {print $2}'); sleep 10; T2=$(curl -s http://localhost:8000/metrics | awk '/^vllm:generation_tokens_total/ {print $2}'); echo "Vitesse : $(echo "scale=2; ($T2 - $T1) / 10" | bc) tokens/s"
# afficher le nombre de tokens générés
curl -s http://localhost:8000/metrics | grep -E "num_requests_running|generation_tokens_total"