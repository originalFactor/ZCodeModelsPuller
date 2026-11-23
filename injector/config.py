# -*- coding: utf-8 -*-
"""injector.config — 路径、通道名及注入常量配置。"""

from __future__ import annotations

import os
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PULLER_JS = ROOT_DIR / "zcode-model-puller.js"
OMP_EFFORTS_FILE = ROOT_DIR / "omp_efforts.json"
MAIN_HANDLERS_JS = ROOT_DIR / "injector" / "main_handlers.js"

MARKER_HTML = "./zcode-model-puller.js"
MARKER_IPC = "zcode:read-model-config"

CH_READ = "zcode:read-model-config"
CH_WRITE = "zcode:write-model-config"
CH_FETCH = "zcode:fetch-models-from-url"
CH_ADD = "zcode:add-models-with-metadata"
CH_ENRICH = "zcode:enrich-model-metadata"
CH_META = "zcode:model-metadata"
CH_CLICK = "zcode:simulate-mouse-click"
CH_MOVE = "zcode:simulate-mouse-move"

SCRIPT_TAG = '  <script type="module" src="./zcode-model-puller.js"></script>\n'

ASAR_REL = Path("resources") / "app.asar"


def _fallback_asar() -> Path:
    """最后兜底：ZCode 默认的 per-user 安装位置（仅用于不存在时报错提示）。"""
    local_appdata = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(local_appdata) / "Programs" / "ZCode" / "resources" / "app.asar"


def _exe_from_cmd(raw: object) -> str:
    """从 UninstallString / DisplayIcon 之类的命令串里取出可执行件完整路径。"""
    s = str(raw or "").strip()
    if not s:
        return ""
    if s.startswith('"'):
        end = s.find('"', 1)
        return s[1:end] if end > 0 else s.strip('"')
    m = re.match(r"^(.*?\.(?:exe|ico|bat|cmd))\b", s, re.IGNORECASE)
    return m.group(1) if m else s.split(" ")[0]


def _install_dirs_from_registry() -> list[Path]:
    """读取卸载表里 ZCode 的安装位置（用户可能装在任意盘符，如 D:\\Program Files）。"""
    if os.name != "nt":
        return []
    try:
        import winreg
    except ImportError:
        return []
    dirs: list[Path] = []
    sub = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        views = (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY) if hive == winreg.HKEY_LOCAL_MACHINE else (0,)
        for view in views:
            try:
                root = winreg.OpenKey(hive, sub, 0, winreg.KEY_READ | view)
            except OSError:
                continue
            with root:
                idx = 0
                while True:
                    try:
                        name = winreg.EnumKey(root, idx)
                    except OSError:
                        break
                    idx += 1
                    try:
                        with winreg.OpenKey(root, name) as item:
                            try:
                                display = str(winreg.QueryValueEx(item, "DisplayName")[0])
                            except OSError:
                                continue
                            if "zcode" not in display.lower():
                                continue
                            for value in ("InstallLocation", "DisplayIcon", "UninstallString"):
                                try:
                                    target = _exe_from_cmd(winreg.QueryValueEx(item, value)[0])
                                except OSError:
                                    continue
                                if target:
                                    p = Path(target)
                                    dirs.append(p if p.is_dir() else p.parent)
                    except OSError:
                        continue
    return dirs


def _common_install_dirs() -> list[Path]:
    """常见安装位置：%LOCALAPPDATA%\\Programs\\ZCode 及各盘 Program Files\\ZCode。"""
    dirs: list[Path] = []
    for var in ("LOCALAPPDATA", "ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        base = os.environ.get(var)
        if base:
            dirs.append(Path(base) / "Programs" / "ZCode")
            dirs.append(Path(base) / "ZCode")
    try:
        drives = [Path(d) for d in os.listdrives()]
    except (AttributeError, OSError):
        drives = [Path(f"{c}:\\") for c in "CDEFGH"]
    for d in drives:
        dirs.append(d / "Program Files" / "ZCode")
        dirs.append(d / "Program Files (x86)" / "ZCode")
        dirs.append(d / "Programs" / "ZCode")
    return dirs


def _candidate_asars() -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for d in _install_dirs_from_registry() + _common_install_dirs():
        p = d / ASAR_REL
        key = str(p).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def default_asar() -> Path:
    """自动探测 ZCode 的 app.asar：环境变量 → 注册表安装记录 → 常见安装目录。"""
    explicit = os.environ.get("ZCODE_ASAR")
    if explicit:
        return Path(explicit)
    for p in _candidate_asars():
        if p.exists():
            return p
    return _fallback_asar()
