#!/usr/bin/env python3
"""
OSM路网数据下载工具

使用OSMnx下载北京地区的道路网络数据
"""

import osmnx as ox
import geopandas as gpd
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from config.config import EXTERNAL_DATA_DIR

# 确保外部数据目录存在
EXTERNAL_DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_osm_network(place_name="Beijing, China", network_type="all"):
    """
    下载OSM路网数据

    参数:
        place_name: 地点名称
        network_type: 路网类型
            - 'all': 所有道路
            - 'drive': 可行车道路
            - 'walk': 步行道路
            - 'bike': 自行车道
    """
    print(f"下载OSM路网数据...")
    print(f"地点: {place_name}")
    print(f"路网类型: {network_type}")

    # 配置OSMnx使用缓存（新版本API）
    ox.settings.use_cache = True
    ox.settings.log_console = True

    # 下载路网
    print("正在从OpenStreetMap下载数据...")
    G = ox.graph_from_place(place_name, network_type=network_type)

    # 转换为GeoDataFrame
    print("转换为GeoDataFrame...")
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)

    print(f"\n路网统计:")
    print(f"  节点数: {len(gdf_nodes)}")
    print(f"  边数: {len(gdf_edges)}")

    # 保存
    output_edges = EXTERNAL_DATA_DIR / f"osm_{network_type}_edges.shp"
    output_nodes = EXTERNAL_DATA_DIR / f"osm_{network_type}_nodes.shp"

    print(f"\n保存路网数据...")
    gdf_edges.to_file(output_edges, encoding='utf-8')
    gdf_nodes.to_file(output_nodes, encoding='utf-8')

    print(f"边(道路)已保存: {output_edges}")
    print(f"节点(交叉口)已保存: {output_nodes}")

    # 返回边数据（主要使用道路）
    return gdf_edges


def download_osm_network_bbox(north, south, east, west, network_type="drive"):
    """
    按边界框下载OSM路网数据

    参数:
        north, south, east, west: 边界坐标
        network_type: 路网类型
    """
    print(f"下载OSM路网数据（边界框）...")
    print(f"边界: {north}, {south}, {east}, {west}")

    ox.settings.use_cache = True
    ox.settings.log_console = True

    # 下载路网
    G = ox.graph_from_bbox(north, south, east, west, network_type=network_type)

    # 转换
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)

    print(f"\n路网统计:")
    print(f"  节点数: {len(gdf_nodes)}")
    print(f"  边数: {len(gdf_edges)}")

    # 保存
    output_edges = EXTERNAL_DATA_DIR / f"osm_{network_type}_bbox_edges.shp"
    output_nodes = EXTERNAL_DATA_DIR / f"osm_{network_type}_bbox_nodes.shp"

    gdf_edges.to_file(output_edges, encoding='utf-8')
    gdf_nodes.to_file(output_nodes, encoding='utf-8')

    print(f"已保存: {output_edges}, {output_nodes}")

    return gdf_edges


def download_beijing_highways():
    """
    下载北京高速公路和主干道
    """
    print("下载北京高速公路和主干道...")

    # 北京市区边界（大致范围）
    north = 40.2
    south = 39.7
    east = 116.9
    west = 116.0

    ox.settings.use_cache = True
    ox.settings.log_console = True

    # 下载可行驶道路
    G = ox.graph_from_bbox(bbox=(north, south, east, west), network_type='drive')

    # 简化路网（保留主要道路）
    print("简化路网（保留主要道路）...")
    G = ox.simplify_graph(G, tolerance=50)

    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)

    # 筛选高速公路和主干道
    # OSM highway标签: motorway, trunk, primary, secondary等
    if 'highway' in gdf_edges.columns:
        main_roads = gdf_edges[gdf_edges['highway'].isin([
            'motorway', 'motorway_link',
            'trunk', 'trunk_link',
            'primary', 'primary_link'
        ])]

        print(f"\n主要道路统计:")
        print(f"  总道路数: {len(gdf_edges)}")
        print(f"  主要道路数: {len(main_roads)}")

        output = EXTERNAL_DATA_DIR / "beijing_main_roads.shp"
        main_roads.to_file(output, encoding='utf-8')
        print(f"已保存: {output}")

        return main_roads
    else:
        print("警告: 数据中没有highway字段")
        return gdf_edges


def create_study_area_bbox():
    """
    创建研究区域的边界框（基于InSAR数据范围）
    """
    # 从Month2项目已知的研究区域
    # 北京西南部: 114.06°E ~ 115.47°E, 38.92°N ~ 40.58°N
    # 但实际处理区域更小，使用北京地区常用范围

    beijing_bbox = {
        'north': 40.2,
        'south': 39.7,
        'east': 116.9,
        'west': 116.0
    }

    return beijing_bbox


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='下载OSM路网数据')
    parser.add_argument('--mode', choices=['place', 'bbox', 'highways'],
                        default='highways',
                        help='下载模式')
    parser.add_argument('--place', default='Beijing, China',
                        help='地点名称（place模式）')
    parser.add_argument('--network', default='drive',
                        help='路网类型（drive/walk/bike/all）')

    args = parser.parse_args()

    if args.mode == 'place':
        download_osm_network(args.place, args.network)
    elif args.mode == 'bbox':
        bbox = create_study_area_bbox()
        download_osm_network_bbox(
            bbox['north'], bbox['south'],
            bbox['east'], bbox['west'],
            args.network
        )
    else:  # highways
        download_beijing_highways()


if __name__ == '__main__':
    main()
