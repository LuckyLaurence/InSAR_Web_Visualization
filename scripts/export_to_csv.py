#!/usr/bin/env python3
"""
从Month2的HDF5数据导出CSV文件
用于Web应用导入测试
"""

import h5py
import numpy as np
import pandas as pd
from pathlib import Path

# M2项目路径
month2_project = Path("F:/InSAR_WorkSpace/02_Projects/Project_Beijing")
h5_file = month2_project / "mintpy/geo/geo_velocity.h5"

print("=" * 60)
print("从Month2 HDF5数据导出CSV")
print("=" * 60)

print(f"\n读取文件: {h5_file}")

with h5py.File(h5_file, 'r') as f:
    # 读取velocity数据
    velocity_m_per_yr = f['velocity'][:]

    # 获取地理信息
    x_first = float(f.attrs['X_FIRST'])
    y_first = float(f.attrs['Y_FIRST'])
    x_step = float(f.attrs['X_STEP'])
    y_step = float(f.attrs['Y_STEP'])

    length, width = velocity_m_per_yr.shape

    print(f"数据尺寸: {length} x {width}")
    print(f"原始速度范围: {np.nanmin(velocity_m_per_yr):.3f} ~ {np.nanmax(velocity_m_per_yr):.3f} m/year")

    # 单位转换
    velocity_mm_per_yr = velocity_m_per_yr * 1000
    print(f"转换后范围: {np.nanmin(velocity_mm_per_yr):.1f} ~ {np.nanmax(velocity_mm_per_yr):.1f} mm/year")

    # 生成坐标
    lon = np.arange(width) * x_step + x_first
    lat = np.arange(length) * y_step + y_first

    # 采样（不采样，直接取所有有效点）
    print("\n正在提取有效数据点...")

    valid_data = []
    for i in range(length):
        for j in range(width):
            vel = velocity_mm_per_yr[i, j]
            if not np.isnan(vel):
                valid_data.append({
                    'longitude': lon[j],
                    'latitude': lat[i],
                    'velocity': vel
                })

    print(f"有效点数: {len(valid_data):,}")

    # 转换为DataFrame
    df = pd.DataFrame(valid_data)

    # 保存为CSV
    output_dir = Path("F:/InSAR_WorkSpace/03_Projects/InSAR_Web_Visualization/data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "month2_data_full.csv"
    df.to_csv(output_file, index=False)

    print(f"\n✅ CSV文件已保存: {output_file}")
    print(f"   文件大小: {output_file.stat().st_size / 1024 / 1024:.1f} MB")

    # 显示前几行
    print("\n数据预览:")
    print(df.head(10))

    # 同时创建一个采样版本（更小，用于快速测试）
    print("\n创建采样版本（每100个点取1个）...")
    df_sample = df.iloc[::100, :]
    sample_file = output_dir / "month2_data_sample.csv"
    df_sample.to_csv(sample_file, index=False)
    print(f"✅ 采样文件已保存: {sample_file}")
    print(f"   采样点数: {len(df_sample):,}")

print("\n" + "=" * 60)
print("导出完成！")
print("=" * 60)
print("\n现在可以在Web应用中上传这些CSV文件了：")
print(f"1. {output_file.name} - 完整数据")
print(f"2. {sample_file.name} - 采样数据（推荐用于测试）")
