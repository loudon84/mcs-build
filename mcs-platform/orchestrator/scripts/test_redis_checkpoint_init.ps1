# RedisCheckpointStore 初始化测试脚本 (PowerShell)
# 
# 使用方法：
#   .\scripts\test_redis_checkpoint_init.ps1
#   或
#   cd scripts; .\test_redis_checkpoint_init.ps1

$ErrorActionPreference = "Stop"

# 切换到脚本所在目录的父目录（项目根目录）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "RedisCheckpointStore 初始化测试" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "工作目录: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# 检查 conda 环境
$condaEnv = "mcs-platform"
Write-Host "检查 conda 环境: $condaEnv" -ForegroundColor Yellow
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未找到 conda 命令" -ForegroundColor Red
    exit 1
}

# 检查 Redis 连接
Write-Host "检查 Redis 连接..." -ForegroundColor Yellow
try {
    $redisTest = redis-cli ping 2>&1
    if ($redisTest -eq "PONG") {
        Write-Host "  [OK] Redis 服务器连接正常" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Redis 服务器可能未运行或无法连接" -ForegroundColor Yellow
        Write-Host "  请确保 Redis 服务器正在运行，否则测试可能失败" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [WARN] 未找到 redis-cli 命令，跳过 Redis 连接检查" -ForegroundColor Yellow
}
Write-Host ""

# 激活 conda 环境并运行测试
Write-Host "激活 conda 环境并运行测试..." -ForegroundColor Yellow
Write-Host ""

$pythonScript = Join-Path $ScriptDir "test_redis_checkpoint_init.py"

# 使用 conda run 在指定环境中运行脚本
conda run -n $condaEnv python $pythonScript

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "测试失败，退出码: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "测试完成！" -ForegroundColor Green
