#!/usr/bin/env python3
"""
GIS工具 - 将InSAR数据转换为Shapefile点数据

功能:
1. 从HDF5文件提取速度场数据
2. 转换单位: m/year -> mm/year
3. 转换为GeoDataFrame
4. 导出为Shapefile格式
"""

import h5py
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.config import MONTH2_VELOCITY_FILE, PROCESSED_DATA_DIR


def get_geo_info(geo_file):
    """从地理编码HDF5文件中获取坐标信息"""
    with h5py.File(geo_file, 'r') as f:
        x_first = float(f.attrs['X_FIRST'])
        y_first = float(f.attrs['Y_FIRST'])
        x_step = float(f.attrs['X_STEP'])
        y_step = float(f.attrs['Y_STEP'])
        width = int(f.attrs['WIDTH'])
        length = int(f.attrs['LENGTH'])
    return {
        'lon_min': x_first,
        'lat_max': y_first,
        'lon_max': x_first + width * x_step,
        'lat_min': y_first + length * y_step,
        'width': width,
        'length': length,
        'x_step': x_step,
        'y_step': y_step
    }


def hdf5_to_shapefile(velocity_file, output_shp, sample_step=1, min_velocity=None):
    """
    将HDF5速度场转换为Shapefile点数据

    注意: 原始数据单位为 m/year，输出时转换为 mm/year

    参数:
        velocity_file: HDF5速度场文件路径
        output_shp: 输出Shapefile路径
        sample_step: 采样步长（默认1，即全部像素）
        min_velocity: 最小速度阈值（mm/year，用于筛选）
    """
    print(f"读取速度场文件: {velocity_file}")

    with h5py.File(velocity_file, 'r') as f:
        # 读取速度数据 (单位: m/year)
        velocity_m_per_yr = f['velocity'][:]

        # 获取单位信息
        unit = f.attrs.get('UNIT', 'm/year')
        print(f"原始数据单位: {unit}")

        # 获取地理信息
        x_first = float(f.attrs['X_FIRST'])
        y_first = float(f.attrs['Y_FIRST'])
        x_step = float(f.attrs['X_STEP'])
        y_step = float(f.attrs['Y_STEP'])
        width = velocity_m_per_yr.shape[1]
        length = velocity_m_per_yr.shape[0]

    # 单位转换: m/year -> mm/year
    velocity_mm_per_yr = velocity_m_per_yr * 1000

    print(f"数据尺寸: {length} x {width}")
    print(f"原始速度范围: {np.nanmin(velocity_m_per_yr):.3f} ~ {np.nanmax(velocity_m_per_yr):.3f} m/year")
    print(f"转换后范围: {np.nanmin(velocity_mm_per_yr):.1f} ~ {np.nanmax(velocity_mm_per_yr):.1f} mm/year")

    # 生成坐标网格
    lon = np.arange(width) * x_step + x_first
    lat = np.arange(length) * y_step + y_first

    # 创建点数据列表
    points_data = []

    # 采样（如果数据量太大）
    for i in range(0, length, sample_step):
        for j in range(0, width, sample_step):
            vel = velocity_mm_per_yr[i, j]

            # 跳过NaN值
            if np.isnan(vel):
                continue

            # 应用最小速度阈值 (mm/year)
            if min_velocity is not None and vel > min_velocity:
                continue

            points_data.append({
                'longitude': lon[j],
                'latitude': lat[i],
                'velocity': vel,  # mm/year
                'row': i,
                'col': j
            })

    print(f"有效点数: {len(points_data)}")

    # 转换为GeoDataFrame
    df = pd.DataFrame(points_data)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"  # WGS84
    )

    # 保存为Shapefile
    gdf.to_file(output_shp, encoding='utf-8')
    print(f"Shapefile已保存: {output_shp}")

    return gdf


def create_aggregated_points(velocity_file, output_shp, grid_size=0.01):
    """
    创建聚合点数据（减少数据量，提高Web加载速度）

    注意: 原始数据单位为 m/year，输出时转换为 mm/year

    参数:
        velocity_file: HDF5速度场文件路径
        output_shp: 输出Shapefile路径
        grid_size: 网格大小（度），默认0.01度约1km
    """
    print(f"读取速度场文件: {velocity_file}")

    with h5py.File(velocity_file, 'r') as f:
        # 读取速度数据 (单位: m/year)
        velocity_m_per_yr = f['velocity'][:]
        unit = f.attrs.get('UNIT', 'm/year')
        print(f"原始数据单位: {unit}")

        x_first = float(f.attrs['X_FIRST'])
        y_first = float(f.attrs['Y_FIRST'])
        x_step = float(f.attrs['X_STEP'])
        y_step = float(f.attrs['Y_STEP'])

    # 单位转换: m/year -> mm/year
    velocity_mm_per_yr = velocity_m_per_yr * 1000

    length, width = velocity_mm_per_yr.shape

    print(f"数据尺寸: {length} x {width}")
    print(f"原始速度范围: {np.nanmin(velocity_m_per_yr):.3f} ~ {np.nanmax(velocity_m_per_yr):.3f} m/year")
    print(f"转换后范围: {np.nanmin(velocity_mm_per_yr):.1f} ~ {np.nanmax(velocity_mm_per_yr):.1f} mm/year")

    # 计算网格索引
    lon_grid = np.arange(width) * x_step + x_first
    lat_grid = np.arange(length) * y_step + y_first

    # 创建网格字典
    grid_dict = {}

    for i in range(length):
        for j in range(width):
            vel = velocity_mm_per_yr[i, j]
            if np.isnan(vel):
                continue

            lon = lon_grid[j]
            lat = lat_grid[i]

            # 计算网格键
            grid_key = (int(lon / grid_size), int(lat / grid_size))

            if grid_key not in grid_dict:
                grid_dict[grid_key] = {
                    'lon_center': (int(lon / grid_size) + 0.5) * grid_size,
                    'lat_center': (int(lat / grid_size) + 0.5) * grid_size,
                    'velocities': [],
                    'count': 0
                }

            grid_dict[grid_key]['velocities'].append(vel)
            grid_dict[grid_key]['count'] += 1

    # 聚合数据
    aggregated_data = []
    for key, data in grid_dict.items():
        velocities = np.array(data['velocities'])
        aggregated_data.append({
            'longitude': data['lon_center'],
            'latitude': data['lat_center'],
            'velocity': np.mean(velocities),  # mm/year
            'velocity_std': np.std(velocities),
            'velocity_min': np.min(velocities),
            'velocity_max': np.max(velocities),
            'point_count': data['count']
        })

    print(f"聚合点数: {len(aggregated_data)}")

    # 转换为GeoDataFrame
    df = pd.DataFrame(aggregated_data)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )

    # 保存
    gdf.to_file(output_shp, encoding='utf-8')
    print(f"聚合Shapefile已保存: {output_shp}")

    return gdf


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='转换InSAR数据为Shapefile')
    parser.add_argument('--mode', choices=['full', 'sample', 'aggregate'],
                        default='aggregate',
                        help='转换模式: full(全部), sample(采样), aggregate(聚合)')
    parser.add_argument('--sample-step', type=int, default=10,
                        help='采样步长（sample模式）')
    parser.add_argument('--grid-size', type=float, default=0.005,
                        help='网格大小度数（aggregate模式）')
    parser.add_argument('--output', default='insar_velocity_points.shp',
                        help='输出文件名')

    args = parser.parse_args()

    # 确保输出目录存在
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DATA_DIR / args.output

    # 执行转换
    if args.mode == 'aggregate':
        gdf = create_aggregated_points(
            MONTH2_VELOCITY_FILE,
            output_path,
            grid_size=args.grid_size
        )
    else:
        gdf = hdf5_to_shapefile(
            MONTH2_VELOCITY_FILE,
            output_path,
            sample_step=args.sample_step
        )

    print("\n转换完成!")
    print(f"数据统计:")
    print(f"  点数: {len(gdf)}")
    if 'velocity' in gdf.columns:
        print(f"  速度范围: {gdf['velocity'].min():.1f} ~ {gdf['velocity'].max():.1f} mm/year")
    if args.mode == 'aggregate' and 'point_count' in gdf.columns:
        print(f"  平均点数/网格: {gdf['point_count'].mean():.0f}")


if __name__ == '__main__':
    main()
