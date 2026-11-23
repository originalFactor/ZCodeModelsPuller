# -*- coding: utf-8 -*-
"""injector.asar — Electron ASAR 包解包、打包与备份管理。"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
from pathlib import Path
from .config import MARKER_HTML, MARKER_IPC
from .utils import die, hash_file, info, scan_bytes, warn


def asar_runner() -> str | None:
    """返回可用的 `@electron/asar` 调用前缀：npx 优先，缺 npx 时回退 pnpm dlx。"""
    if shutil.which("npx") or shutil.which("npx.cmd"):
        return "npx --yes @electron/asar"
    if shutil.which("pnpm") or shutil.which("pnpm.cmd"):
        return "pnpm dlx @electron/asar"
    return None


def run_npx(sub: str, *args: str) -> tuple[int, str, str]:
    """调用 @electron/asar <sub> <args…>。"""
    runner = asar_runner()
    if not runner:
        die("未检测到 npx 或 pnpm，无法调用 @electron/asar。请自行安装 Node.js（含 npm）。")
    quoted = " ".join(f'"{a}"' for a in args)
    cmd = f"{runner} {sub} {quoted}".strip()
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        die("执行超时（>15 分钟），请重试或检查 Node/pnpm 是否正常。")
    return res.returncode, res.stdout, res.stderr


def read_unpacked_paths(asar_path: Path) -> list[str]:
    """从原版 asar 的 header 读出所有标记为 unpacked 的条目（相对路径，正斜杠）。

    Electron 的 asar 会把原生模块（.node / .dll / .exe）放在同名 `.unpacked` 目录而非包内，
    重新打包时必须原样保留这些标记，否则原生模块被塞进包内将无法加载。
    """
    try:
        with open(asar_path, "rb") as f:
            _, _, _, json_len = struct.unpack("<IIII", f.read(16))
            if json_len <= 0 or json_len > 64 << 20:
                return []
            header = json.loads(f.read(json_len).decode("utf-8", errors="replace"))
    except (OSError, struct.error, ValueError):
        return []

    paths: list[str] = []

    def walk(node: dict, prefix: str) -> None:
        for name, child in (node.get("files") or {}).items():
            p = f"{prefix}/{name}" if prefix else name
            if "files" in child:
                walk(child, p)
            elif child.get("unpacked"):
                # 只收文件级条目：asar 只会给文件打 unpacked 标记，目录节点不作为比对基准
                paths.append(p)

    walk(header, "")
    return paths


def pack_asar(work: Path, out: Path, unpack: list[str]) -> tuple[int, str, str]:
    """把 work 目录打包为 out，并保持 unpack 列表里的条目为外置（unpacked）。

    注意：@electron/asar 的 --unpack glob 是对「绝对路径」做匹配的，因此每条相对路径都要
    加上 `**/` 前缀才命中；且只接受一个 glob，多条用花括号展开一次性传入。
    """
    args = [str(work), str(out)]
    if unpack:
        args += ["--unpack", "{" + ",".join(f"**/{p}" for p in unpack) + "}"]
    return run_npx("pack", *args)


def sync_unpacked(new_asar: Path, target_dir: Path) -> int:
    """把重新打包生成的 `<asar>.unpacked` 目录内容合并进安装目录的 app.asar.unpacked。"""
    src = new_asar.with_name(new_asar.name + ".unpacked")
    if not src.is_dir():
        return 0
    count = 0
    try:
        for item in src.rglob("*"):
            if not item.is_file():
                continue
            dst = target_dir / item.relative_to(src)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst)
            count += 1
    finally:
        shutil.rmtree(src, ignore_errors=True)
    return count


def backup_asar(asar: Path, bak: Path, dry_run: bool) -> None:
    """备份官方原版 app.asar，检测到升级后自动刷新原版备份。"""
    if not bak.exists():
        if dry_run:
            info(f"(dry-run) 将创建原版备份 → {bak}")
            return
        shutil.copy2(asar, bak)
        info(f"已创建原版备份（仅首次执行）→ {bak}")
        return
    if hash_file(asar) == hash_file(bak):
        info(f"备份与当前 app.asar 一致，复用已有备份 → {bak}")
        return
    # 备份与当前 asar 不同：判断是不是 ZCode 升级后的新原版
    cur = scan_bytes(asar, [MARKER_IPC, MARKER_HTML])
    if cur[MARKER_IPC] == 0 and cur[MARKER_HTML] == 0:
        if dry_run:
            info("(dry-run) 当前 asar 为新的官方原版（无注入标记），将刷新备份。")
            return
        shutil.copy2(asar, bak)
        info("检测到 ZCode 已升级（当前 asar 为新的官方原版），备份已刷新 → 还原将回到这一版。")
    else:
        warn("当前 asar 已含注入标记且与备份内容不同：保留旧版原包备份（还原将回到旧版）。")
