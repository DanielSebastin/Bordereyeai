#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# BorderEye AI Surveillance Platform - Docker Orchestration Helper (Linux/macOS)
# ─────────────────────────────────────────────────────────────────────────────

ACTION="${1:-up}"

echo "=========================================================="
echo "  BorderEye AI Surveillance Platform - Docker Control"
echo "=========================================================="

case "$ACTION" in
  up)
    echo "[*] Launching BorderEye container stack with GPU passthrough..."
    docker compose up -d
    echo ""
    echo "[+] Services active:"
    echo "  - Operations UI:     http://localhost:3000"
    echo "  - AI Backend API:    http://localhost:8000"
    echo "  - Interactive Docs:  http://localhost:8000/docs"
    ;;
  down)
    echo "[*] Stopping containers..."
    docker compose down
    ;;
  build)
    echo "[*] Building local Docker images with CUDA support..."
    docker compose build
    ;;
  pull)
    echo "[*] Pulling latest production images from GHCR..."
    docker compose pull
    ;;
  logs)
    docker compose logs -f
    ;;
  gpu-test)
    echo "[*] Testing NVIDIA GPU container runtime..."
    docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
    ;;
  *)
    echo "Usage: ./run-docker.sh [up|down|build|pull|logs|gpu-test]"
    exit 1
    ;;
esac
