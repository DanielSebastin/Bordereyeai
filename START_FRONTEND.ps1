# Start Frontend Server
Write-Host "Starting BorderEye Frontend..." -ForegroundColor Cyan
Write-Host ""

Set-Location "d:\IVBAP\sih_border_surveillance\frontend"

Write-Host "Frontend starting on http://localhost:3000" -ForegroundColor Green
Write-Host "Live Monitoring: http://localhost:3000/live-monitoring" -ForegroundColor Green
Write-Host "AI Search: http://localhost:3000/ai-search" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

npm run dev
