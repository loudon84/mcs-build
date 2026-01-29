# MCS Listener 独立部署安装脚本 (PowerShell)
# 用于在 conda mcs-platform 环境中安装 mcs-listener 及其依赖

param(
    [string]$ProjectRoot = "e:\git-ai\mcs-agent\mcs-platform"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MCS Listener 独立部署安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 conda 环境
Write-Host "[1/4] 检查 conda 环境..." -ForegroundColor Yellow
try {
    $condaEnv = conda info --envs | Select-String "mcs-platform"
    if (-not $condaEnv) {
        Write-Host "错误: 未找到 conda 环境 'mcs-platform'" -ForegroundColor Red
        Write-Host "请先创建并激活 conda 环境:" -ForegroundColor Yellow
        Write-Host "  conda create -n mcs-platform python=3.12" -ForegroundColor White
        Write-Host "  conda activate mcs-platform" -ForegroundColor White
        exit 1
    }
    Write-Host "✓ conda 环境 'mcs-platform' 已找到" -ForegroundColor Green
} catch {
    Write-Host "错误: 无法检查 conda 环境" -ForegroundColor Red
    exit 1
}

# 激活 conda 环境
Write-Host ""
Write-Host "[2/4] 激活 conda 环境..." -ForegroundColor Yellow
conda activate mcs-platform
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 无法激活 conda 环境 'mcs-platform'" -ForegroundColor Red
    exit 1
}
Write-Host "✓ conda 环境已激活" -ForegroundColor Green

# 检查项目路径
$ContractsPath = Join-Path $ProjectRoot "libs\contracts"
$ListenerPath = Join-Path $ProjectRoot "services\mcs-listener"

if (-not (Test-Path $ContractsPath)) {
    Write-Host "错误: 未找到 mcs-contracts 路径: $ContractsPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ListenerPath)) {
    Write-Host "错误: 未找到 mcs-listener 路径: $ListenerPath" -ForegroundColor Red
    exit 1
}

# 安装 mcs-contracts
Write-Host ""
Write-Host "[3/4] 安装 mcs-contracts..." -ForegroundColor Yellow
Push-Location $ContractsPath
try {
    pip install -e . 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ mcs-contracts 安装成功" -ForegroundColor Green
    } else {
        Write-Host "错误: mcs-contracts 安装失败" -ForegroundColor Red
        Pop-Location
        exit 1
    }
} catch {
    Write-Host "错误: 安装 mcs-contracts 时发生异常: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

# 安装 mcs-listener
Write-Host ""
Write-Host "[4/4] 安装 mcs-listener..." -ForegroundColor Yellow
Push-Location $ListenerPath
try {
    pip install -e . 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ mcs-listener 安装成功" -ForegroundColor Green
    } else {
        Write-Host "错误: mcs-listener 安装失败" -ForegroundColor Red
        Pop-Location
        exit 1
    }
} catch {
    Write-Host "错误: 安装 mcs-listener 时发生异常: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

# 验证安装
Write-Host ""
Write-Host "验证安装..." -ForegroundColor Yellow
try {
    $result = python -c "import mcs_contracts; from mcs_contracts import EmailEvent; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ mcs-contracts 导入测试通过" -ForegroundColor Green
    } else {
        Write-Host "警告: mcs-contracts 导入测试失败" -ForegroundColor Yellow
        Write-Host $result
    }
} catch {
    Write-Host "警告: mcs-contracts 导入测试异常: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "1. 配置 .env 文件（如果尚未配置）" -ForegroundColor White
Write-Host "2. 运行数据库迁移: alembic upgrade head" -ForegroundColor White
Write-Host "3. 启动服务: python -m uvicorn api.main:app --host 0.0.0.0 --port 8001" -ForegroundColor White
Write-Host "   或使用启动脚本: .\scripts\start.ps1" -ForegroundColor White
Write-Host ""
