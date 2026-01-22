# 使用 Vite 构建前端
# 使用方法: .\scripts\build-frontend.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$frontendDir = Join-Path $projectRoot "frontend"
$distDir = Join-Path $frontendDir "dist"

Write-Host "正在构建前端..." -ForegroundColor Green
Write-Host "前端目录: $frontendDir"
Write-Host "输出目录: $distDir"

Push-Location $frontendDir

# 如果 node_modules 不存在则安装依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "正在安装 npm 依赖..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装依赖失败" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}

# 构建前端
Write-Host "正在运行 Vite 构建..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host "前端构建成功!" -ForegroundColor Green
    Write-Host "输出目录: $distDir"
} else {
    Write-Host "前端构建失败!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
