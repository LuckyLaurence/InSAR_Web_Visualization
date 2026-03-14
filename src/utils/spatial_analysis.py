#!/usr/bin/env python3
"""
空间分析工具 - InSAR点与路网的空间连接分析

功能:
1. 空间连接：识别InSAR点附近的路网
2. 风险评估：计算路网穿越沉降区的风险
3. 统计分析：按道路类型统计受影响程度
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 可选导入 GeoPandas
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    gpd = None

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from config.config import PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR, VELOCITY_THRESHOLDS


def spatial_join_points_to_roads(insar_gdf, roads_gdf, buffer_distance=0.002):
    """
    将InSAR点与道路进行空间连接

    参数:
        insar_gdf: InSAR点GeoDataFrame
        roads_gdf: 道路GeoDataFrame
        buffer_distance: 缓冲距离（度），默认0.002度约200米

    返回:
        包含空间连接结果的GeoDataFrame
    """
    print(f"执行空间连接分析...")
    print(f"  InSAR点数: {len(insar_gdf)}")
    print(f"  道路数: {len(roads_gdf)}")

    # 确保使用相同的坐标系
    insar_gdf = insar_gdf.to_crs(epsg=4326)
    roads_gdf = roads_gdf.to_crs(epsg=4326)

    # 创建道路缓冲区
    roads_buffered = roads_gdf.copy()
    roads_buffered['geometry'] = roads_buffered.geometry.buffer(buffer_distance)

    # 空间连接
    print("执行空间连接（这可能需要几分钟）...")
    joined = gpd.sjoin(insar_gdf, roads_buffered[['geometry', 'name', 'highway']],
                        how="inner", predicate="intersects")

    print(f"  连接结果: {len(joined)} 条记录")

    return joined


def calculate_road_risk(insar_gdf, roads_gdf, velocity_col='velocity_mean'):
    """
    计算每条道路的沉降风险

    参数:
        insar_gdf: InSAR点数据
        roads_gdf: 道路数据
        velocity_col: 速度列名

    返回:
        包含风险信息的道路GeoDataFrame
    """
    print("计算道路风险...")

    try:
        # 空间连接
        joined = spatial_join_points_to_roads(insar_gdf, roads_gdf)

        if len(joined) == 0:
            print("警告: 没有找到连接的道路，返回原始道路数据")
            # 为原始道路添加默认风险等级
            result = roads_gdf.copy()
            result['risk_level'] = 'unknown'
            result['point_count'] = 0
            result['velocity_mean'] = 0.0
            return result

        # 按道路聚合统计
        road_stats = joined.groupby('name').agg({
            velocity_col: ['count', 'mean', 'min', 'max', 'std']
        }).reset_index()

        # 重命名列
        road_stats.columns = ['name', 'point_count', 'velocity_mean', 'velocity_min',
                              'velocity_max', 'velocity_std']

        # 风险分级 - 使用mm/year阈值
        def get_risk_level(row):
            """根据平均速度确定风险等级 (单位: mm/year)"""
            vel = row['velocity_mean']
            if vel < -200:  # 严重沉降 (>200 mm/yr)
                return 'high'
            elif vel < -50:  # 明显沉降 (50-200 mm/yr)
                return 'medium'
            else:
                return 'low'

        road_stats['risk_level'] = road_stats.apply(get_risk_level, axis=1)

        # 合并回道路几何信息
        roads_with_risk = roads_gdf.merge(road_stats, on='name', how='left')

        # 填充NaN值（没有InSAR点的道路）
        roads_with_risk['point_count'] = roads_with_risk['point_count'].fillna(0)
        roads_with_risk['risk_level'] = roads_with_risk['risk_level'].fillna('unknown')
        roads_with_risk['velocity_mean'] = roads_with_risk['velocity_mean'].fillna(0.0)

        # 风险统计
        print(f"\n道路风险统计:")
        print(f"  高风险道路: {len(roads_with_risk[roads_with_risk['risk_level'] == 'high'])}")
        print(f"  中风险道路: {len(roads_with_risk[roads_with_risk['risk_level'] == 'medium'])}")
        print(f"  低风险道路: {len(roads_with_risk[roads_with_risk['risk_level'] == 'low'])}")

        return roads_with_risk

    except Exception as e:
        print(f"空间分析失败: {e}")
        # 返回默认数据
        result = roads_gdf.copy()
        result['risk_level'] = 'unknown'
        result['point_count'] = 0
        result['velocity_mean'] = 0.0
        return result


def find_high_risk_infrastructure(insar_gdf, roads_gdf, velocity_col='velocity_mean'):
    """
    识别高风险基础设施（穿越严重沉降区的道路）

    返回:
        高风险道路列表
    """
    print("识别高风险基础设施...")

    roads_with_risk = calculate_road_risk(insar_gdf, roads_gdf, velocity_col)

    # 筛选高风险
    high_risk = roads_with_risk[roads_with_risk['risk_level'] == 'high'].copy()

    print(f"\n找到 {len(high_risk)} 条高风险道路:")

    for idx, row in high_risk.iterrows():
        print(f"  - {row['name']}: 平均速度 {row['velocity_mean']:.2f} mm/yr, "
              f"{int(row['point_count'])} 个监测点")

    return high_risk


def create_risk_map_data(insar_gdf, roads_gdf, velocity_col='velocity_mean'):
    """
    创建用于地图展示的风险数据

    返回:
        (insar_df, roads_df) 用于PyDeck的DataFrame
    """
    print("准备地图数据...")

    # 确定速度列名
    if velocity_col not in insar_gdf.columns:
        velocity_col = 'velocity' if 'velocity' in insar_gdf.columns else list(insar_gdf.columns)[2]

    # InSAR点数据
    insar_df = pd.DataFrame({
        'lon': insar_gdf['longitude'].values,
        'lat': insar_gdf['latitude'].values,
        'velocity': insar_gdf[velocity_col].values
    })

    # 道路风险分析
    roads_with_risk = calculate_road_risk(insar_gdf, roads_gdf, velocity_col)

    # 道路数据 - 转换为PyDeck格式
    road_data = []
    for idx, row in roads_with_risk.iterrows():
        coords = list(row.geometry.coords)
        road_data.append({
            'path': coords,
            'name': row['name'],
            'type': row.get('highway', 'unknown'),
            'risk': row.get('risk_level', 'unknown'),
            'avg_velocity': row.get('velocity_mean', 0),
            'point_count': int(row.get('point_count', 0))
        })

    roads_df = pd.DataFrame(road_data)

    # 风险颜色映射
    risk_colors = {
        'high': [255, 0, 0, 200],      # 红色
        'medium': [255, 165, 0, 200],  # 橙色
        'low': [0, 255, 0, 200],      # 绿色
        'unknown': [150, 150, 150, 150]  # 灰色
    }

    roads_df['color'] = roads_df['risk'].map(risk_colors)

    print(f"  InSAR点: {len(insar_df)}")
    print(f"  道路: {len(roads_df)}")

    return insar_df, roads_df


def main():
    """测试空间分析功能"""
    import sys

    # 加载数据
    velocity_file = PROCESSED_DATA_DIR / "beijing_velocity_aggregated.shp"
    road_file = EXTERNAL_DATA_DIR / "beijing_mock_roads.shp"

    print("加载数据...")
    insar_gdf = gpd.read_file(velocity_file)
    roads_gdf = gpd.read_file(road_file)

    # 修复列名
    if 'velocity_m' in insar_gdf.columns:
        insar_gdf['velocity_mean'] = insar_gdf['velocity_m']

    # 执行分析
    high_risk = find_high_risk_infrastructure(insar_gdf, roads_gdf)

    # 保存结果
    output_file = EXTERNAL_DATA_DIR / "beijing_roads_with_risk.shp"
    roads_with_risk = calculate_road_risk(insar_gdf, roads_gdf)
    roads_with_risk.to_file(output_file)
    print(f"\n风险道路数据已保存: {output_file}")


if __name__ == '__main__':
    main()
