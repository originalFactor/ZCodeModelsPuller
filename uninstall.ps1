# 还原 ZCode 官方原版（卸载注入）
# 用法：右键“使用 PowerShell 运行”，或在终端执行  .\uninstall.ps1
#      额外参数原样透传，例如  .\uninstall.ps1 --asar "D:\Program Files\ZCode\resources\app.asar"
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
    Write-Host "提示：还原需要写入 ZCode 安装目录，遇到权限错误请以管理员身份重开终端再运行。" -ForegroundColor Yellow
}

Write-Host "请确保已完全退出 ZCode（含系统托盘）..."
& $python "$PSScriptRoot\inject_windows.py" --restore @args
exit $LASTEXITCODE
