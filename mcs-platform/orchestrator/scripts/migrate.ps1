# MCS Orchestrator 数据库迁移脚本 (PowerShell)
# 
# 使用方法：
#   .\scripts\migrate.ps1 [upgrade|downgrade|current|history] [-Target main|listener|masterdata|all]
#   默认执行 upgrade head，Target 默认 all（先 main，再 listener，再 masterdata）
#
# Target:
#   main      - 编排库 (ORCHESTRATION_DB_DSN / DB_DSN)，alembic.ini
#   listener  - 监听库 (LISTENER_DB_DSN)，message_records 表，alembic_listener.ini
#   masterdata - 主数据库 (MASTERDATA_DB_DSN)，internal 表 customers/contacts/companys/products/masterdata_versions，alembic_masterdata.ini
#   all       - 先 main，再 listener，再 masterdata

param(
    [string]$Action = "upgrade",
    [string]$Revision = "head",
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"

# 切换到脚本所在目录的父目录（项目根目录）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "MCS Orchestrator Database Migration" -ForegroundColor Cyan
Write-Host "Working directory: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# 加载 .env 文件（如果存在）
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Write-Host "Loading environment variables from .env file: $EnvFile" -ForegroundColor Yellow
    $content = Get-Content $EnvFile -Encoding UTF8
    $content | ForEach-Object {
        $line = $_.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) {
            return
        }
        if ($line -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            if ($value.StartsWith("'") -and $value.EndsWith("'")) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} else {
    Write-Host "Warning: .env file not found at $EnvFile" -ForegroundColor Yellow
}

# 设置 PYTHONPATH 以包含 src 目录
$SrcPath = Join-Path $ProjectRoot "src"
$currentPath = $env:PYTHONPATH
if ($currentPath) {
    $env:PYTHONPATH = "$currentPath;$SrcPath"
} else {
    $env:PYTHONPATH = $SrcPath
}

# 设置 Python 编码为 UTF-8
$env:PYTHONIOENCODING = "utf-8"

$runMain = ($Target -eq "all" -or $Target -eq "main")
$runListener = ($Target -eq "all" -or $Target -eq "listener")
$runMasterdata = ($Target -eq "all" -or $Target -eq "masterdata")

if ($runMain -and -not $env:DB_DSN -and -not $env:ORCHESTRATION_DB_DSN) {
    Write-Host "Error: DB_DSN or ORCHESTRATION_DB_DSN not set (required for main)" -ForegroundColor Red
    Write-Host "Please set in .env file" -ForegroundColor Yellow
    exit 1
}
if ($runListener -and -not $env:LISTENER_DB_DSN -and -not $env:listener_db_dsn) {
    Write-Host "Error: LISTENER_DB_DSN (or listener_db_dsn) not set for listener migrations" -ForegroundColor Red
    Write-Host "Please set LISTENER_DB_DSN in .env file" -ForegroundColor Yellow
    exit 1
}
if ($runMasterdata -and -not $env:MASTERDATA_DB_DSN -and -not $env:masterdata_db_dsn) {
    Write-Host "Error: MASTERDATA_DB_DSN (or masterdata_db_dsn) not set for masterdata migrations" -ForegroundColor Red
    Write-Host "Please set MASTERDATA_DB_DSN in .env file" -ForegroundColor Yellow
    exit 1
}

function Run-Alembic {
    param([string]$Config, [string]$Label)
    Write-Host "Running migration ($Label): $Action $Revision" -ForegroundColor Yellow
    $alembicArgs = @("-c", $Config)
    switch ($Action.ToLower()) {
        "upgrade"   { python -m alembic @alembicArgs upgrade $Revision }
        "downgrade" {
            if ($Revision -eq "head") {
                Write-Host "Error: downgrade requires a specific revision" -ForegroundColor Red
                exit 1
            }
            python -m alembic @alembicArgs downgrade $Revision
        }
        "current"    { python -m alembic @alembicArgs current }
        "history"    { python -m alembic @alembicArgs history }
        "revision"   {
            if ($Revision -eq "head") {
                Write-Host "Error: revision requires a message (e.g., -m 'description')" -ForegroundColor Red
                exit 1
            }
            python -m alembic @alembicArgs revision -m $Revision
        }
        default {
            Write-Host "Unknown action: $Action" -ForegroundColor Red
            exit 1
        }
    }
}

$failed = $false
if ($runMain) {
    Run-Alembic -Config "alembic.ini" -Label "main DB"
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}
if ($runListener -and -not $failed) {
    if ($runMain) { Write-Host "" }
    Run-Alembic -Config "alembic_listener.ini" -Label "listener DB (message_records)"
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}
if ($runMasterdata -and -not $failed) {
    if ($runMain -or $runListener) { Write-Host "" }
    Run-Alembic -Config "alembic_masterdata.ini" -Label "masterdata DB (internal: customers, contacts, companys, products, masterdata_versions)"
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if ($failed) {
    Write-Host ""
    Write-Host "Migration failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Migration completed successfully!" -ForegroundColor Green
