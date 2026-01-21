# Package Python app with Nuitka to single .exe file
# Usage: .\scripts\package-nuitka.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$frontendDir = Join-Path $projectRoot "frontend"
$distDir = Join-Path $frontendDir "dist"
$outputDir = Join-Path $projectRoot "dist"

Write-Host "L4D2 VPK Manager - Nuitka Build Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if frontend dist exists
if (-not (Test-Path $distDir)) {
    Write-Host "Frontend dist directory not found. Building frontend first..." -ForegroundColor Yellow
    & (Join-Path $scriptPath "build-frontend.ps1")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Frontend build failed!" -ForegroundColor Red
        exit 1
    }
}

# Create output directory
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

Write-Host "Building Python application with Nuitka..." -ForegroundColor Green
Write-Host "Main script: main.py" -ForegroundColor Cyan
Write-Host "Output directory: $outputDir" -ForegroundColor Cyan
Write-Host "Frontend resources: $distDir" -ForegroundColor Cyan
Write-Host ""

Push-Location $projectRoot

# Nuitka compilation to single executable
# --onefile: Create single executable
# --windows-console-mode: Hide console window in production
# --include-data-dir: Include frontend resources
python -m nuitka `
    --onefile `
    --windows-console-mode=gui `
    --include-data-dir=frontend/dist=frontend/dist `
    --output-dir=$outputDir `
    --remove-output `
    --follow-imports `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Nuitka compilation successful!" -ForegroundColor Green
    $exePath = Join-Path $outputDir "main.exe"
    if (Test-Path $exePath) {
        Write-Host "Executable created: $exePath" -ForegroundColor Green
        $fileSize = (Get-Item $exePath).Length / 1MB
        Write-Host "File size: $([Math]::Round($fileSize, 2)) MB" -ForegroundColor Green
    }
} else {
    Write-Host "Nuitka compilation failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
