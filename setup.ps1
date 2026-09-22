# Simple Setup Script for SIH Border Surveillance
Write-Host "Setting up SIH Border Surveillance System..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Create virtual environment
Write-Host "[1/4] Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Step 2: Activate and install dependencies
Write-Host "[2/4] Installing Python dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Setup frontend
Write-Host "[3/4] Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

# Step 4: Verify
Write-Host "[4/4] Verifying setup..." -ForegroundColor Yellow
if (Test-Path "cam1.mp4") { Write-Host "✓ Video files present" -ForegroundColor Green }
if (Test-Path ".env") { Write-Host "✓ .env configured" -ForegroundColor Green }
if (Test-Path "venv") { Write-Host "✓ Python venv created" -ForegroundColor Green }
if (Test-Path "frontend\node_modules") { Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green }

Write-Host ""
Write-Host "Setup Complete! See SETUP_LOCAL.md for next steps" -ForegroundColor Green
