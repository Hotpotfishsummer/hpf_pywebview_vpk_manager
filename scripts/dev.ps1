# 开发环境启动脚本
# 同时并行启动前端开发服务器和后端 Python 应用
# 使用方法: .\scripts\dev.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$frontendDir = Join-Path $projectRoot "frontend"

Write-Host "L4D2 VPK 管理器 - 开发环境" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 确保使用正确的 Conda 环境
$targetEnv = "hpf-vpk-manager-pywebview"
if ($env:CONDA_DEFAULT_ENV -ne $targetEnv) {
    Write-Host "正在尝试激活 Conda 环境: $targetEnv..." -ForegroundColor Yellow
    
    # 尝试直接激活
    try {
        conda activate $targetEnv
    } catch {
        # 如果失败，尝试初始化 Conda 钩子再激活
        try {
            conda shell.powershell hook | Out-String | Invoke-Expression
            conda activate $targetEnv
        } catch {
            Write-Host "自动激活失败，请手动运行 'conda activate $targetEnv' 后再执行脚本。" -ForegroundColor Red
            exit 1
        }
    }
    
    if ($env:CONDA_DEFAULT_ENV -ne $targetEnv) {
        Write-Host "无法切换到环境 $targetEnv，请检查该环境是否存在。" -ForegroundColor Red
        exit 1
    }
    Write-Host "环境已成功激活!" -ForegroundColor Green
}

Write-Host "正在启动开发环境..." -ForegroundColor Green
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
Write-Host ""

# 如果有需要，安装前端依赖
if (-not (Test-Path "$frontendDir/node_modules")) {
    Write-Host "正在安装前端依赖..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "前端依赖安装失败!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host ""
}

# 在后台启动前端开发服务器
Write-Host "正在启动 Vite 开发服务器 (http://localhost:5173)..." -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "npm" `
    -ArgumentList "run dev" `
    -WorkingDirectory $frontendDir `
    -PassThru `
    -NoNewWindow

Write-Host "正在启动 Python 后端 (PyWebView)..." -ForegroundColor Cyan

# 启动后端
Push-Location $projectRoot
$env:PYWEBVIEW_DEV = "true"
python main.py
Pop-Location

# 退出时清理进程
Write-Host "正在停止服务..." -ForegroundColor Yellow
if ($frontendProcess -and -not $frontendProcess.HasExited) {
    Stop-Process -InputObject $frontendProcess -Force
}

Write-Host "开发环境已停止。" -ForegroundColor Green
