# MCS Listener Service 启动脚本 (PowerShell)
# 
# 使用方法：
#   .\scripts\start.ps1
#   或者
#   conda activate mcs-platform
#   .\scripts\start.ps1

$ErrorActionPreference = "Stop"

Write-Host "Starting MCS Listener Service..." -ForegroundColor Green

# 加载 .env 文件（如果存在）
if (Test-Path .env) {
    Write-Host "Loading environment variables from .env file..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# 检查环境变量
if (-not $env:DB_DSN) {
    Write-Host "Error: DB_DSN environment variable is not set" -ForegroundColor Red
    Write-Host "Please set DB_DSN in .env file or as an environment variable" -ForegroundColor Yellow
    exit 1
}

# 设置 PYTHONPATH 以包含 src 目录
$currentPath = $env:PYTHONPATH
if ($currentPath) {
    $env:PYTHONPATH = "$currentPath;$PWD\src"
} else {
    $env:PYTHONPATH = "$PWD\src"
}

# 运行数据库迁移
Write-Host "Running database migrations..." -ForegroundColor Yellow
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Failed to run migrations, continuing..." -ForegroundColor Yellow
}

# 启动服务
Write-Host "Starting service..." -ForegroundColor Green
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
