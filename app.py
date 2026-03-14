#!/usr/bin/env python3
"""
InSAR沉降监测Web可视化平台 - Streamlit Cloud入口点

这是Streamlit Cloud的主入口文件，负责设置正确的Python路径并启动应用。
"""

from pathlib import Path
import sys

# 获取项目根目录（当前文件的父目录）
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 导入并运行主应用
from src.app import *
