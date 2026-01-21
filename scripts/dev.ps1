# Development environment startup script
# Starts frontend dev server and backend Python app in parallel
# Usage: .\scripts\dev.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$frontendDir = Join-Path $projectRoot "frontend"

Write-Host "L4D2 VPK Manager - Development Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if conda environment is activated
$condaEnv = $env:CONDA_DEFAULT_ENV
if (-not $condaEnv) {
    Write-Host "WARNING: No Conda environment activated!" -ForegroundColor Yellow
    Write-Host "Run: conda activate hpf-vpk-manager-pywebview" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Starting development environment..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Install frontend dependencies if needed
if (-not (Test-Path "$frontendDir/node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
    Write-Host ""
}

# Start frontend dev server in background
Write-Host "Starting Vite dev server (http://localhost:5173)..." -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "npm" `
    -ArgumentList "run dev" `
    -WorkingDirectory $frontendDir `
    -PassThru `
    -NoNewWindow

Write-Host "Starting Python backend (PyWebView)..." -ForegroundColor Cyan

# Start backend
Push-Location $projectRoot
$env:PYWEBVIEW_DEV = "true"
python main.py
Pop-Location

# Clean up processes on exit
Write-Host "Stopping services..." -ForegroundColor Yellow
if ($frontendProcess -and -not $frontendProcess.HasExited) {
    Stop-Process -InputObject $frontendProcess -Force
}

Write-Host "Development environment stopped." -ForegroundColor Green
