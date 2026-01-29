# MCS Listener Service 启动脚本 (PowerShell)
# 
# 使用方法：
#   .\scripts\start.ps1
#   或者
#   conda activate mcs-platform
#   .\scripts\start.ps1

$ErrorActionPreference = "Stop"

# 切换到脚本所在目录的父目录（项目根目录）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "Starting MCS Listener Service..." -ForegroundColor Green
Write-Host "Working directory: $ProjectRoot" -ForegroundColor Gray

# 加载 .env 文件（如果存在）
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Write-Host "Loading environment variables from .env file: $EnvFile" -ForegroundColor Yellow
    # 使用 UTF-8 编码读取 .env 文件，避免中文注释导致的编码问题
    $content = Get-Content $EnvFile -Encoding UTF8
    $content | ForEach-Object {
        # 跳过注释和空行
        $line = $_.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) {
            return
        }
        # 解析 KEY=VALUE 格式
        if ($line -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            # 移除值中可能的引号
            if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            if ($value.StartsWith("'") -and $value.EndsWith("'")) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            # 确保环境变量值使用 UTF-8 编码
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} else {
    Write-Host "Warning: .env file not found at $EnvFile" -ForegroundColor Yellow
}

# 检查环境变量
if (-not $env:DB_DSN) {
    Write-Host "Error: DB_DSN environment variable is not set" -ForegroundColor Red
    Write-Host "Please set DB_DSN in .env file or as an environment variable" -ForegroundColor Yellow
    Write-Host "Expected .env file location: $EnvFile" -ForegroundColor Yellow
    exit 1
}

# 设置 PYTHONPATH 以包含 src 目录
$SrcPath = Join-Path $ProjectRoot "src"
$currentPath = $env:PYTHONPATH
if ($currentPath) {
    $env:PYTHONPATH = "$currentPath;$SrcPath"
} else {
    $env:PYTHONPATH = $SrcPath
}

# 设置 Python 编码为 UTF-8，避免编码问题
$env:PYTHONIOENCODING = "utf-8"

# 运行数据库迁移
Write-Host "Running database migrations..." -ForegroundColor Yellow
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Failed to run migrations, continuing..." -ForegroundColor Yellow
}

# 启动服务
Write-Host "Starting service..." -ForegroundColor Green
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
