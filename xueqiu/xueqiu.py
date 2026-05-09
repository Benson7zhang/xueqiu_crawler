#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容入口。

项目主程序在根目录 main.py。保留这个文件是为了避免 IDE 运行配置还指向
xueqiu/xueqiu.py 时执行到旧逻辑。
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import main


if __name__ == '__main__':
    sys.exit(main())
