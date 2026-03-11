#!/usr/bin/env python3
"""
简化版GIS工具 - 快速测试用
"""

import h5py
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path

# 配置
VELOCITY_FILE = Path("F:/InSAR_WorkSpace/02_Projects/Project_Beijing/mintpy/geo/geo_velocity.h5")
OUTPUT_DIR = Path("F:/InSAR_WorkSpace/03_Projects/InSAR_Web_Visualization/data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("开始快速转换（稀疏采样）...")

with h5py.File(VELOCITY_FILE, 'r') as f:
    velocity = f['velocity'][:]
    x_first = float(f.attrs['X_FIRST'])
    y_first = float(f.attrs['Y_FIRST'])
    x_step = float(f.attrs['X_STEP'])
    y_step = float(f.attrs['Y_STEP'])

length, width = velocity.shape
print(f"原始数据: {length} x {width} = {length * width} 像素")

# 稀疏采样（每50个像素取1个）
sample_step = 50
points_data = []

for i in range(0, length, sample_step):
    for j in range(0, width, sample_step):
        vel = velocity[i, j]
        if not np.isnan(vel):
            lon = x_first + j * x_step
            lat = y_first + i * y_step
            points_data.append({
                'longitude': lon,
                'latitude': lat,
                'velocity': vel
            })

print(f"采样点数: {len(points_data)}")

# 创建GeoDataFrame
df = pd.DataFrame(points_data)
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.longitude, df.latitude),
    crs="EPSG:4326"
)

# 保存
output_file = OUTPUT_DIR / "beijing_velocity_sample.shp"
gdf.to_file(output_file)
print(f"已保存: {output_file}")
print(f"速度范围: {gdf['velocity'].min():.1f} ~ {gdf['velocity'].max():.1f} mm/yr")
