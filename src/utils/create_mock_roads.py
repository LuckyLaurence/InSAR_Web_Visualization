#!/usr/bin/env python3
"""
创建模拟路网数据（用于开发测试）

生成北京地区的简化道路网络数据
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from config.config import EXTERNAL_DATA_DIR

EXTERNAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

print("创建模拟路网数据...")

# 使用InSAR数据的实际坐标范围
lon_min, lon_max = 114.0, 115.5
lat_min, lat_max = 38.9, 40.6

# 创建主要道路（经线和纬线）
roads = []

# 纬向道路（东西向）
for lat in np.linspace(lat_min, lat_max, 8):
    road = LineString([
        (lon_min, lat),
        (lon_max, lat)
    ])
    roads.append({
        'geometry': road,
        'name': f'纬向路_{lat:.2f}',
        'highway': 'primary' if np.random.rand() > 0.5 else 'secondary',
        'length_km': (lon_max - lon_min) * 111 * np.cos(np.radians(lat))
    })

# 经向道路（南北向）
for lon in np.linspace(lon_min, lon_max, 10):
    road = LineString([
        (lon, lat_min),
        (lon, lat_max)
    ])
    roads.append({
        'geometry': road,
        'name': f'经向路_{lon:.2f}',
        'highway': 'primary' if np.random.rand() > 0.5 else 'secondary',
        'length_km': (lat_max - lat_min) * 111
    })

# 添加一些对角线路（模拟环路/高速）
diagonals = [
    [(lon_min, lat_min), (lon_max, lat_max)],
    [(lon_min, lat_max), (lon_max, lat_min)],
    [(lon_min + 0.1, lat_min), (lon_max - 0.1, lat_max)],
    [(lon_min, lat_min + 0.1), (lon_max, lat_max - 0.1)]
]

for i, coords in enumerate(diagonals):
    road = LineString(coords)
    roads.append({
        'geometry': road,
        'name': f'环路_{i+1}',
        'highway': 'motorway',
        'length_km': road.length * 111
    })

print(f"生成了 {len(roads)} 条道路")

# 创建GeoDataFrame
gdf_roads = gpd.GeoDataFrame(roads, crs="EPSG:4326")

# 保存
output_file = EXTERNAL_DATA_DIR / "beijing_mock_roads.shp"
gdf_roads.to_file(output_file, encoding='utf-8')
print(f"已保存: {output_file}")

print("\n道路统计:")
print(f"  总数: {len(gdf_roads)}")
print(f"  高速公路: {len(gdf_roads[gdf_roads['highway'] == 'motorway'])}")
print(f"  主要道路: {len(gdf_roads[gdf_roads['highway'] == 'primary'])}")
print(f"  次要道路: {len(gdf_roads[gdf_roads['highway'] == 'secondary'])}")
