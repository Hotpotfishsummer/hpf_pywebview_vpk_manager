# 使用 Nuitka 将 Python 应用打包为单文件 .exe
# 使用方法: .\scripts\package-nuitka.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$frontendDir = Join-Path $projectRoot "frontend"
$distDir = Join-Path $frontendDir "dist"
$outputDir = Join-Path $projectRoot "dist"

Write-Host "L4D2 VPK 管理器 - Nuitka 打包脚本" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
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
        # 不直接失败:下方会回退为直接定位环境内 python.exe(无头/自动化场景)
        Write-Host "无法在当前会话激活 $targetEnv，将尝试直接定位环境 python.exe..." -ForegroundColor Yellow
    } else {
        Write-Host "环境已成功激活!" -ForegroundColor Green
    }
}

# 确定要使用的 python:优先已激活环境;否则直接定位环境内的 python.exe(无头/自动化场景)
$pythonExe = "python"
if ($env:CONDA_DEFAULT_ENV -ne $targetEnv) {
    $condaBase = (& conda info --base 2>$null)
    if ($LASTEXITCODE -eq 0 -and $condaBase) {
        $envPython = Join-Path $condaBase "envs\$targetEnv\python.exe"
        if (Test-Path $envPython) {
            $pythonExe = $envPython
            Write-Host "未激活 Conda 环境,直接使用: $pythonExe" -ForegroundColor Yellow
        } else {
            Write-Host "错误: 找不到环境 $targetEnv 的 python.exe" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "错误: 找不到 conda,无法定位环境 $targetEnv" -ForegroundColor Red
        exit 1
    }
}

# 检查是否安装了 Nuitka
Write-Host "正在检查环境 $targetEnv 中的 Nuitka..." -ForegroundColor Cyan
& $pythonExe -c "import nuitka" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 当前环境中未找到 Nuitka!" -ForegroundColor Red
    Write-Host "请确保已安装所有依赖:" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 检查前端构建资源是否存在
if (-not (Test-Path (Join-Path $distDir "index.html"))) {
    Write-Host "未找到前端构建产物(frontend/dist/index.html)。正在先构建前端..." -ForegroundColor Yellow
    & (Join-Path $scriptPath "build-frontend.ps1")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "前端构建失败!" -ForegroundColor Red
        exit 1
    }
}

# 检查打包引用的图标资源是否存在
$iconPath = Join-Path $projectRoot "assets/app_icon.ico"
if (-not (Test-Path $iconPath)) {
    Write-Host "错误: 未找到图标文件 $iconPath (Nuitka --windows-icon-from-ico 引用)。" -ForegroundColor Red
    exit 1
}

# 创建输出目录
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

Write-Host "正在使用 Nuitka 构建 Python 应用程序..." -ForegroundColor Green
Write-Host "主脚本: main.py" -ForegroundColor Cyan
Write-Host "输出目录: $outputDir" -ForegroundColor Cyan
Write-Host "前端资源: $distDir" -ForegroundColor Cyan
Write-Host ""

Push-Location $projectRoot

# Nuitka 编译为单执行文件
# --onefile: 创建单个可执行文件
# --windows-console-mode: 
#   - disable: 隐藏控制台 (生产模式)
#   - force: 强制显示控制台 (调试打包问题时非常有用)
# --output-filename: 指定生成的 EXE 文件名
# --windows-icon-from-ico: 指定图标文件
& $pythonExe -m nuitka `
    --onefile `
    --windows-console-mode=disable `
    --include-data-dir=frontend/dist=frontend/dist `
    --include-data-dir=assets=assets `
    --windows-icon-from-ico=assets/app_icon.ico `
    --output-dir=$outputDir `
    --output-filename="L4D2-VPK-Manager.exe" `
    --remove-output `
    --follow-imports `
    --lto=yes `
    --assume-yes-for-downloads `
    --windows-file-version="1.0.0" `
    --windows-product-name="L4D2 VPK Manager" `
    --windows-company-name="hpf" `
    --windows-file-description="L4D2 VPK 管理器 - 现代化 Vue3 + PyWebView 桌面应用" `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Nuitka 编译成功!" -ForegroundColor Green
    $exePath = Join-Path $outputDir "L4D2-VPK-Manager.exe"
    if (Test-Path $exePath) {
        Write-Host "可执行文件已创建: $exePath" -ForegroundColor Green
        $fileSize = (Get-Item $exePath).Length / 1MB
        Write-Host "文件大小: $([Math]::Round($fileSize, 2)) MB" -ForegroundColor Green
    } else {
        Write-Host "错误: 编译报告成功但未找到产物 $exePath !" -ForegroundColor Red
        Pop-Location
        exit 1
    }
} else {
    Write-Host "Nuitka 编译失败!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
