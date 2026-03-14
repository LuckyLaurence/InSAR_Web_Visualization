"""
配置文件 - InSAR Web可视化平台
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# Month2项目数据路径（仅本地环境可用）
try:
    # 尝试使用本地路径（Windows开发环境）
    MONTH2_PROJECT = Path("F:/InSAR_WorkSpace/02_Projects/Project_Beijing")
    MONTH2_VELOCITY_FILE = MONTH2_PROJECT / "mintpy" / "geo" / "geo_velocity.h5"
    MONTH2_GEO_FILE = MONTH2_PROJECT / "mintpy" / "geo" / "geo_geometryRadar.h5"
except:
    # 云端环境或路径不存在时设置为None
    MONTH2_PROJECT = None
    MONTH2_VELOCITY_FILE = None
    MONTH2_GEO_FILE = None

# 输出目录
OUTPUT_DIR = BASE_DIR / "output"

# 页面配置
PAGE_TITLE = "InSAR沉降监测可视化平台"
PAGE_ICON = "🌍"
LAYOUT = "wide"

# 地图配置
MAP_VIEW_STATE = {
    "latitude": 39.9,
    "longitude": 116.4,
    "zoom": 10,
    "pitch": 45,
    "bearing": 0
}

# 沉降速率阈值（mm/year）- 数据范围: -579 ~ 505 mm/year
VELOCITY_THRESHOLDS = {
    "severe": -200,     # 严重沉降 (>200 mm/yr)
    "high": -50,        # 明显沉降 (50-200 mm/yr)
    "moderate": -10,    # 轻微沉降 (10-50 mm/yr)
    "stable": 10        # 稳定范围 (-10 to 10 mm/yr)
}

# 风险等级颜色
RISK_COLORS = {
    "high": "#FF0000",      # 红色 - 高风险
    "medium": "#FFA500",    # 橙色 - 中风险
    "low": "#00FF00"        # 绿色 - 低风险
}

# API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

# Streamlit配置
STREAMLIT_CONFIG = {
    "theme.primaryColor": "#FF6B6B",
    "theme.backgroundColor": "#FFFFFF",
    "theme.secondaryBackgroundColor": "#F0F2F6",
    "theme.textColor": "#262730",
    "theme.font": "sans serif"
}
