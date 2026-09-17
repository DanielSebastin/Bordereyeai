# ─────────────────────────────────────────────────────────────────────────────
# BorderEye AI Surveillance Platform - Docker Orchestration Helper
# ─────────────────────────────────────────────────────────────────────────────

param (
    [Parameter(Position=0)]
    [ValidateSet("up", "down", "build", "pull", "logs", "gpu-test")]
    [string]$Action = "up"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  BorderEye AI Surveillance Platform - Docker Control" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

switch ($Action) {
    "up" {
        Write-Host "[*] Starting BorderEye multi-container stack with GPU support..." -ForegroundColor Green
        docker compose up -d
        Write-Host "`n[+] Services started!" -ForegroundColor Green
        Write-Host "  - UI Dashboard:       http://localhost:3000" -ForegroundColor Yellow
        Write-Host "  - AI Backend API:     http://localhost:8000" -ForegroundColor Yellow
        Write-Host "  - Interactive Docs:   http://localhost:8000/docs" -ForegroundColor Yellow
        Write-Host "  - System Health:      http://localhost:8000/health" -ForegroundColor Yellow
    }
    "down" {
        Write-Host "[*] Stopping BorderEye containers..." -ForegroundColor Yellow
        docker compose down
    }
    "build" {
        Write-Host "[*] Building local Docker images with CUDA support..." -ForegroundColor Cyan
        docker compose build
    }
    "pull" {
        Write-Host "[*] Pulling latest published images from GHCR..." -ForegroundColor Cyan
        docker compose pull
    }
    "logs" {
        docker compose logs -f
    }
    "gpu-test" {
        Write-Host "[*] Testing NVIDIA Container Toolkit GPU detection..." -ForegroundColor Cyan
        docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
    }
}
