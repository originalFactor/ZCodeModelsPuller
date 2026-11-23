# 注入「⚡️ 自动拉取模型」能力到 ZCode（Windows）
# 用法：右键“使用 PowerShell 运行”，或在终端执行  .\install.ps1
#      额外参数原样透传，例如  .\install.ps1 --asar "D:\Program Files\ZCode\resources\app.asar"
# MIT License — Copyright (c) 2026 zcode-model-puller contributors；上游 HHQ-666 见仓库 LICENSE。
$ErrorActionPreference = "Stop"

# 让 Python 的 UTF-8 输出在本控制台正确显示
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-Host "✗ 未检测到 Python，请先安装 Python 3.9+ 并加入 PATH。" -ForegroundColor Red
    exit 1
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "提示：ZCode 通常安装在 Program Files 下，写入 app.asar 需要管理员权限；若下一步报权限错误，请以管理员身份重开终端再运行。" -ForegroundColor Yellow
}

Write-Host "请确保已完全退出 ZCode（含系统托盘）..."
& $python "$PSScriptRoot\inject_windows.py" @args
exit $LASTEXITCODE
