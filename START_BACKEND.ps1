# Start Backend Server
Write-Host "Starting BorderEye Backend Server..." -ForegroundColor Cyan
Write-Host ""

Set-Location "d:\IVBAP\sih_border_surveillance"

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Set working directory to backend
Set-Location backend

# Start the server
Write-Host "Backend server starting on http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
