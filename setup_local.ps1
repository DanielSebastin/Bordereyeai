# Local Setup Script for SIH Border Surveillance System
# Run this script to set up both backend and frontend

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  SIH Border Surveillance - Local Setup" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "d:\IVBAP\sih_border_survelliance"
Set-Location $projectRoot

# ============================================================
# STEP 1: Backend Setup
# ============================================================
Write-Host "[1/5] Setting up Python Backend..." -ForegroundColor Yellow

# Create virtual environment if it doesn't exist
if (!(Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Green
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Gray
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip --quiet

# Install Python dependencies
Write-Host "Installing Python dependencies (this may take a few minutes)..." -ForegroundColor Green
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing Python packages. Trying CPU-specific PyTorch installation..." -ForegroundColor Red
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --quiet
    pip install -r requirements.txt --quiet
}

Write-Host "✓ Backend dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# ============================================================
# STEP 2: Initialize Database
# ============================================================
Write-Host "[2/5] Initializing Database..." -ForegroundColor Yellow

# Check if database exists
if (Test-Path "surveillance.db") {
    Write-Host "Database already exists. Skipping initialization." -ForegroundColor Gray
} else {
    Write-Host "Creating surveillance database..." -ForegroundColor Green
    $initScript = "from backend.app.database.db_session import init_db; init_db(); print('Database initialized')"
    python -c $initScript
}

Write-Host "✓ Database ready!" -ForegroundColor Green
Write-Host ""

# ============================================================
# STEP 3: Frontend Setup
# ============================================================
Write-Host "[3/5] Setting up Next.js Frontend..." -ForegroundColor Yellow

Set-Location "$projectRoot\frontend"

# Check if node_modules exists
if (!(Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies (this may take a few minutes)..." -ForegroundColor Green
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error installing Node packages. Retrying with clean cache..." -ForegroundColor Red
        npm cache clean --force
        npm install
    }
} else {
    Write-Host "Node modules already installed." -ForegroundColor Gray
}

Write-Host "✓ Frontend dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# ============================================================
# STEP 4: Verify Setup
# ============================================================
Write-Host "[4/5] Verifying Setup..." -ForegroundColor Yellow

Set-Location $projectRoot

# Check if video files exist
$videos = @("cam1.mp4", "cam2.mp4", "cam3.mp4", "cam4.mp4", "cam5.mp4")
$allVideosPresent = $true
foreach ($video in $videos) {
    if (Test-Path $video) {
        $size = (Get-Item $video).Length / 1MB
        Write-Host "✓ $video present ($('{0:N1}' -f $size) MB)" -ForegroundColor Green
    } else {
        Write-Host "✗ $video missing!" -ForegroundColor Red
        $allVideosPresent = $false
    }
}

# Check .env file
if (Test-Path ".env") {
    Write-Host "✓ .env configuration found" -ForegroundColor Green
} else {
    Write-Host "✗ .env file missing! Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ .env created from template" -ForegroundColor Green
    }
}

Write-Host "✓ Setup verification complete!" -ForegroundColor Green
Write-Host ""

# ============================================================
# STEP 5: Instructions
# ============================================================
Write-Host "[5/5] Setup Complete!" -ForegroundColor Yellow
Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  🚀 Ready to Launch!" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "To start the system, run these commands in SEPARATE terminals:" -ForegroundColor White
Write-Host ""

Write-Host "Terminal 1 - Backend:" -ForegroundColor Yellow
Write-Host "  cd `"$projectRoot`"" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  cd backend" -ForegroundColor Gray
Write-Host "  python -m app.main" -ForegroundColor Green
Write-Host "  OR: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host ""

Write-Host "Terminal 2 - Frontend:" -ForegroundColor Yellow
Write-Host "  cd `"$projectRoot\frontend`"" -ForegroundColor Gray
Write-Host "  npm run dev" -ForegroundColor Green
Write-Host ""

Write-Host "Access Points:" -ForegroundColor White
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Live Cams:   http://localhost:3000/live-monitoring" -ForegroundColor Cyan
Write-Host "  AI Search:   http://localhost:3000/ai-search" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Health:      http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""

Write-Host "Features Available:" -ForegroundColor White
Write-Host "  ✓ Real-time Human Detection (YOLO11)" -ForegroundColor Green
Write-Host "  ✓ Vehicle ANPR (License Plates)" -ForegroundColor Green
Write-Host "  ✓ Virtual Fence Intrusion Detection" -ForegroundColor Green
Write-Host "  ✓ Cross-Camera Person Re-ID" -ForegroundColor Green
Write-Host "  ✓ Natural Language Query (Groq LLM)" -ForegroundColor Green
Write-Host "  ✓ Facial Recognition (Webcam)" -ForegroundColor Green
Write-Host "  ✓ Audio Intelligence" -ForegroundColor Green
Write-Host ""

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "For detailed instructions, see: SETUP_LOCAL.md" -ForegroundColor Gray
Write-Host "=================================================" -ForegroundColor Cyan
