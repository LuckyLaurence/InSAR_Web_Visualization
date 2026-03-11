#!/usr/bin/env python3
"""
数据导入模块 - 支持多种格式的InSAR数据导入

功能:
1. 文件上传处理
2. 数据格式转换
3. 数据验证
4. 错误提示
"""

import pandas as pd
import geopandas as gpd
import json
from io import BytesIO
from pathlib import Path
import tempfile
import os
import zipfile


def validate_insar_data(df, required_cols=None):
    """
    验证InSAR数据格式

    返回: (is_valid, error_message, summary)
    """
    if required_cols is None:
        required_cols = ['longitude', 'latitude', 'velocity']

    # 检查必需列
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"缺少必需列: {', '.join(missing_cols)}", None

    # 检查数据范围
    try:
        lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
        lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
        vel_min, vel_max = df['velocity'].min(), df['velocity'].max()

        # 坐标范围检查
        if not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
            return False, "经度超出合理范围 (-180 ~ 180)", None
        if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
            return False, "纬度超出合理范围 (-90 ~ 90)", None

        # 检查NaN值
        nan_count = df['velocity'].isna().sum()
        if nan_count > len(df) * 0.5:
            return False, f"速度值中NaN过多: {nan_count}/{len(df)}", None

        # 生成摘要
        summary = {
            '点数': len(df),
            '经度范围': f"{lon_min:.2f}° ~ {lon_max:.2f}°",
            '纬度范围': f"{lat_min:.2f}° ~ {lat_max:.2f}°",
            '速度最小值': f"{vel_min:.1f} mm/yr",
            '速度最大值': f"{vel_max:.1f} mm/yr",
            '缺失值': nan_count
        }

        return True, "数据验证通过", summary

    except Exception as e:
        return False, f"数据验证失败: {str(e)}", None


def load_csv_file(file_content):
    """加载CSV文件"""
    try:
        df = pd.read_csv(file_content)

        # 标准化列名（支持多种命名方式）
        col_mapping = {
            'lon': 'longitude',
            'lng': 'longitude',
            'long': 'longitude',
            'lat': 'latitude',
            'vel': 'velocity',
            'rate': 'velocity',
            'subsidence': 'velocity'
        }

        # 列名小写化
        df.columns = df.columns.str.lower().str.strip()

        # 应用映射
        df = df.rename(columns=col_mapping)

        return df
    except Exception as e:
        raise Exception(f"CSV解析失败: {str(e)}")


def load_geojson_file(file_content):
    """加载GeoJSON文件"""
    try:
        gdf = gpd.read_file(file_content)

        # 提取坐标
        if gdf.geometry.geom_type.iloc[0] == 'Point':
            gdf['longitude'] = gdf.geometry.x
            gdf['latitude'] = gdf.geometry.y
        else:
            raise Exception("GeoJSON必须包含Point类型的几何")

        # 标准化列名
        col_mapping = {
            'lon': 'longitude',
            'vel': 'velocity',
            'rate': 'velocity'
        }
        gdf.columns = gdf.columns.str.lower().str.strip()
        gdf = gdf.rename(columns=col_mapping)

        # 确保有velocity列
        if 'velocity' not in gdf.columns:
            # 尝试找到数值列作为velocity
            numeric_cols = gdf.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                gdf['velocity'] = gdf[numeric_cols[0]]

        return gdf
    except Exception as e:
        raise Exception(f"GeoJSON解析失败: {str(e)}")


def load_excel_file(file_content):
    """加载Excel文件"""
    try:
        df = pd.read_excel(file_content)

        # 标准化列名（同CSV）
        col_mapping = {
            'lon': 'longitude',
            'lng': 'longitude',
            'long': 'longitude',
            'lat': 'latitude',
            'vel': 'velocity',
            'rate': 'velocity',
            'subsidence': 'velocity'
        }

        df.columns = df.columns.str.lower().str.strip()
        df = df.rename(columns=col_mapping)

        return df
    except Exception as e:
        raise Exception(f"Excel解析失败: {str(e)}")


def load_shapefile_zip(zip_file_content):
    """加载Shapefile（ZIP格式）"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 解压ZIP文件
            with zipfile.ZipFile(zip_file_content) as zip_ref:
                zip_ref.extractall(temp_dir)

            # 查找.shp文件
            shp_files = list(Path(temp_dir).glob("*.shp"))

            if not shp_files:
                raise Exception("ZIP文件中未找到.shp文件")

            # 读取第一个.shp文件
            gdf = gpd.read_file(shp_files[0])

            # 提取坐标
            if gdf.geometry.geom_type.iloc[0] == 'Point':
                gdf['longitude'] = gdf.geometry.x
                gdf['latitude'] = gdf.geometry.y
            else:
                raise Exception("Shapefile必须包含Point类型的几何")

            # 标准化列名
            col_mapping = {
                'lon': 'longitude',
                'vel': 'velocity',
                'rate': 'velocity'
            }
            gdf.columns = gdf.columns.str.lower().str.strip()
            gdf = gdf.rename(columns=col_mapping)

            return gdf

    except Exception as e:
        raise Exception(f"Shapefile解析失败: {str(e)}")


def process_uploaded_file(uploaded_file):
    """
    处理上传的文件

    返回: (success, data/geodataframe, error_message, summary)
    """
    if uploaded_file is None:
        return False, None, "未上传文件", None

    file_name = uploaded_file.name.lower()
    file_content = BytesIO(uploaded_file.getvalue())

    try:
        # 根据文件扩展名选择加载方式
        if file_name.endswith('.csv'):
            df = load_csv_file(file_content)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df.longitude, df.latitude),
                crs="EPSG:4326"
            )

        elif file_name.endswith('.geojson') or file_name.endswith('.json'):
            gdf = load_geojson_file(file_content)

        elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            df = load_excel_file(file_content)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df.longitude, df.latitude),
                crs="EPSG:4326"
            )

        elif file_name.endswith('.zip'):
            gdf = load_shapefile_zip(file_content)

        else:
            return False, None, f"不支持的文件格式: {file_name}", None

        # 验证数据
        is_valid, error_msg, summary = validate_insar_data(gdf)

        if not is_valid:
            return False, None, error_msg, None

        return True, gdf, "数据加载成功", summary

    except Exception as e:
        return False, None, f"文件处理失败: {str(e)}", None


def create_sample_csv():
    """创建示例CSV数据"""
    import numpy as np

    np.random.seed(42)
    n = 1000

    data = {
        'longitude': np.random.uniform(116.0, 116.5, n),
        'latitude': np.random.uniform(39.8, 40.0, n),
        'velocity': np.random.normal(-50, 100, n)
    }

    df = pd.DataFrame(data)
    return df


def create_sample_geojson():
    """创建示例GeoJSON数据"""
    df = create_sample_csv()

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )

    return gdf


def get_file_template_info():
    """返回文件格式模板信息"""
    return {
        'csv': {
            'name': 'CSV',
            'extension': '.csv',
            'required_columns': ['longitude', 'latitude', 'velocity'],
            'example': """longitude,latitude,velocity
116.4074,39.9042,-25.3
116.4081,39.9050,-12.8
116.4090,39.9060,-5.2""",
            'description': 'Excel可导出'
        },
        'geojson': {
            'name': 'GeoJSON',
            'extension': '.geojson',
            'required_columns': ['coordinates', 'properties.velocity'],
            'description': 'Web标准格式'
        },
        'excel': {
            'name': 'Excel',
            'extension': '.xlsx',
            'required_columns': ['longitude', 'latitude', 'velocity'],
            'description': 'xlsx/xls格式'
        },
        'shapefile': {
            'name': 'Shapefile',
            'extension': '.zip',
            'required_columns': ['longitude', 'latitude', 'velocity'],
            'description': '打包为ZIP'
        }
    }
