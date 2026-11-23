#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inject_windows.py — 把「⚡️ 自动拉取模型」能力注入 ZCode 客户端（Windows 版）。

命令行入口脚本，核心实现见 `injector/` 模块。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 兼容隔离模式 Python（-I / PYTHONSAFEPATH）：不依赖 sys.path[0]，显式把脚本目录加入搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from injector.cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已中断。")
        sys.exit(130)
