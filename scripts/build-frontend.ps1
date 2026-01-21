# Build frontend with Vite
# Usage: .\scripts\build-frontend.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$frontendDir = Join-Path $projectRoot "frontend"
$distDir = Join-Path $frontendDir "dist"

Write-Host "Building frontend..." -ForegroundColor Green
Write-Host "Frontend directory: $frontendDir"
Write-Host "Output directory: $distDir"

Push-Location $frontendDir

# Install dependencies if node_modules doesn't exist
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}

# Build frontend
Write-Host "Running Vite build..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host "Frontend build successful!" -ForegroundColor Green
    Write-Host "Output directory: $distDir"
} else {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
