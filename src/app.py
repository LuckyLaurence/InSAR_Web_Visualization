#!/usr/bin/env python3
"""
InSAR沉降监测Web可视化平台 - 主应用（优化版）

基于Streamlit的交互式Web应用，展示InSAR形变数据和路网叠加
包含道路风险分级系统和优化的交互体验
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from config.config import (
    PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR,
    PAGE_TITLE, PAGE_ICON, LAYOUT, MAP_VIEW_STATE,
    VELOCITY_THRESHOLDS, RISK_COLORS
)

# 可选导入 GeoPandas（用于空间分析）
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    gpd = None

# 根据GeoPandas可用性导入功能
from src.utils.ai_report import generate_insar_report
from src.utils.data_import import (
    process_uploaded_file,
    get_file_template_info,
    create_sample_csv
)
if HAS_GEOPANDAS:
    from src.utils.spatial_analysis import calculate_road_risk

# ==================== 页面配置 ====================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# ==================== 初始化Session State ====================
def calculate_view_state(gdf):
    """根据数据范围计算合适的视图状态"""
    lon_min, lon_max = gdf.longitude.min(), gdf.longitude.max()
    lat_min, lat_max = gdf.latitude.min(), gdf.latitude.max()

    center_lon = (lon_min + lon_max) / 2
    center_lat = (lat_min + lat_max) / 2

    # 根据数据范围估算缩放级别
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min
    max_range = max(lon_range, lat_range)

    # 简单的缩放级别估算
    if max_range > 2:
        zoom = 7
    elif max_range > 1:
        zoom = 8
    elif max_range > 0.5:
        zoom = 9
    elif max_range > 0.2:
        zoom = 10
    else:
        zoom = 11

    return pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=45,
        bearing=0
    )

if 'view_state' not in st.session_state:
    st.session_state.view_state = pdk.ViewState(
        latitude=MAP_VIEW_STATE["latitude"],
        longitude=MAP_VIEW_STATE["longitude"],
        zoom=MAP_VIEW_STATE["zoom"],
        pitch=MAP_VIEW_STATE["pitch"],
        bearing=MAP_VIEW_STATE["bearing"]
    )

# 添加session state for uploaded data
if 'uploaded_gdf' not in st.session_state:
    st.session_state.uploaded_gdf = None

# ==================== 自定义CSS ====================
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stDataFrame {
        font-size: 14px;
    }
    .road-table {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 标题 ====================
st.markdown('<h1 class="main-title">🌍 InSAR沉降监测可视化平台</h1>', unsafe_allow_html=True)
st.markdown("---")

# ==================== 侧边栏 - 数据加载控制 ====================
st.sidebar.header("📊 数据控制")

# 选择数据源
data_source = st.sidebar.selectbox(
    "选择数据源",
    ["默认数据（北京）", "上传数据"],
    index=0,
    key="data_source_select"
)

# 上传数据处理
uploaded_file = None
gdf_insar = None
gdf_roads = None

if data_source == "默认数据（北京）":
    # 检查是否有 GeoPandas 和数据文件
    has_local_data = HAS_GEOPANDAS and PROCESSED_DATA_DIR.exists() and (PROCESSED_DATA_DIR / "beijing_velocity_aggregated.shp").exists()

    if has_local_data:
        # 加载真实数据
        velocity_file = PROCESSED_DATA_DIR / "beijing_velocity_aggregated.shp"
        road_file = EXTERNAL_DATA_DIR / "beijing_mock_roads.shp"

        @st.cache_data
        def load_insar_data(file_path):
            """加载InSAR速度场数据"""
            try:
                gdf = gpd.read_file(file_path)
                if 'velocity' in gdf.columns:
                    gdf['velocity_mean'] = gdf['velocity']
                return gdf
            except Exception as e:
                st.error(f"数据加载失败: {e}")
                return None

        @st.cache_data
        def load_road_data(file_path):
            """加载路网数据"""
            try:
                return gpd.read_file(file_path)
            except Exception as e:
                st.error(f"路网加载失败: {e}")
                return None

        with st.spinner("正在加载数据..."):
            gdf_insar = load_insar_data(velocity_file)
            if road_file.exists():
                gdf_roads = load_road_data(road_file)

        st.success(f"✅ InSAR数据: {len(gdf_insar):,} 点")
        if gdf_roads is not None:
            st.success(f"✅ 路网数据: {len(gdf_roads)} 条")

    else:
        # 使用模拟数据（演示模式）
        with st.spinner("正在生成演示数据..."):
            # 模拟 InSAR 点数据
            np.random.seed(42)
            n_points = 1000

            # 生成北京区域的随机点
            data = {
                'longitude': np.random.uniform(116.2, 116.6, n_points),
                'latitude': np.random.uniform(39.8, 40.0, n_points),
                'velocity': np.random.normal(-20, 50, n_points),  # 模拟沉降速率
                'velocity_mean': np.random.normal(-20, 50, n_points)
            }
            gdf_insar = pd.DataFrame(data)

            # 模拟路网数据（简化版，不用 GeoPandas）
            roads_data = []
            for i in range(5):
                # 生成简单的道路线段
                start_lon = np.random.uniform(116.3, 116.5)
                start_lat = np.random.uniform(39.85, 39.95)
                roads_data.append({
                    'name': f'演示道路{i+1}',
                    'path': [[start_lon, start_lat], [start_lon + 0.01, start_lat + 0.01]],
                    'type': 'primary'
                })
            gdf_roads = pd.DataFrame(roads_data)

        st.success(f"✅ 演示数据: {len(gdf_insar)} 点")
        if not HAS_GEOPANDAS:
            st.info("💡 演示模式（空间分析功能需要本地环境）")
        else:
            st.info("💡 演示模式（数据文件不在云端，请联系开发者添加）")

else:  # 上传数据
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 上传数据文件")

    # 支持的格式提示（简洁版）
    st.sidebar.caption("💡 支持: CSV, GeoJSON, Excel, Shapefile(ZIP)")

    # 文件上传
    uploaded_file = st.sidebar.file_uploader(
        "选择数据文件",
        type=['csv', 'geojson', 'json', 'xlsx', 'xls', 'zip'],
        help="支持CSV, GeoJSON, Excel, Shapefile(ZIP)",
        key="file_uploader"
    )

    # 数据处理（只验证，不加载）
    if uploaded_file is not None:
        with st.sidebar.spinner("正在验证文件..."):
            success, data, error_msg, summary = process_uploaded_file(uploaded_file)

            if success:
                st.sidebar.success(f"✅ 文件验证通过")
                # 保存到session state
                st.session_state.uploaded_gdf = data
                st.session_state.uploaded_summary = summary

                # 简洁显示点数
                st.sidebar.caption(f"📊 {summary['点数']:,} 个数据点")

                # 确认使用数据按钮
                if st.sidebar.button("🚀 加载此数据", type="primary", key="load_data_btn"):
                    st.session_state.uploaded_gdf = data  # 保存数据
                    st.session_state.uploaded_summary = summary
                    st.sidebar.success("✅ 数据已加载，正在刷新...")
                    st.rerun()
            else:
                st.sidebar.error(f"❌ {error_msg}")

                # 显示示例格式
                if uploaded_file.name.endswith('.csv'):
                    if st.sidebar.checkbox("显示格式示例"):
                        sample = create_sample_csv().head(3)
                        st.sidebar.dataframe(sample, use_container_width=True)

    # 如果session state中有上传的数据，则加载
    if st.session_state.get('uploaded_gdf') is not None:
        gdf_insar = st.session_state.uploaded_gdf
        st.sidebar.info(f"✅ 已加载上传的数据 ({len(gdf_insar):,} 点)")
    elif uploaded_file is None:
        st.sidebar.info("💡 请上传数据文件或切换到默认数据")

# 加载默认路网（仅当使用默认数据时）
if data_source == "默认数据（北京）" and gdf_insar is not None:
    st.sidebar.success(f"✅ InSAR数据: {len(gdf_insar):,} 点")
if data_source == "默认数据（北京）" and gdf_roads is not None:
    st.sidebar.success(f"✅ 路网数据: {len(gdf_roads)} 条")

# 主界面数据显示
if gdf_insar is not None:
    if 'velocity_mean' in gdf_insar.columns:
        velocity_col = 'velocity_mean'
    elif 'velocity' in gdf_insar.columns:
        velocity_col = 'velocity'
    else:
        velocity_col = gdf_insar.columns[2]

    # ==================== 数据统计 ====================
    st.header("📈 数据统计")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总点数", f"{len(gdf_insar):,}")
    with col2:
        min_vel = gdf_insar[velocity_col].min()
        st.metric("最小值", f"{min_vel:.0f} mm/yr")
    with col3:
        max_vel = gdf_insar[velocity_col].max()
        st.metric("最大值", f"{max_vel:.0f} mm/yr")
    with col4:
        std_vel = gdf_insar[velocity_col].std()
        st.metric("标准差", f"{std_vel:.1f} mm/yr")

    st.markdown("---")

    # ==================== 侧边栏 - 筛选控制 ====================
    st.sidebar.header("🎛️ 筛选控制")

    # 速度范围筛选
    velocity_range = st.sidebar.slider(
        "沉降速率范围 (mm/yr)",
        float(gdf_insar[velocity_col].min()),
        float(gdf_insar[velocity_col].max()),
        (float(gdf_insar[velocity_col].min()), float(gdf_insar[velocity_col].max())),
        key="velocity_range_slider"
    )

    # 应用筛选
    mask = (
        (gdf_insar[velocity_col] >= velocity_range[0]) &
        (gdf_insar[velocity_col] <= velocity_range[1])
    )
    gdf_filtered = gdf_insar[mask].copy()

    st.sidebar.info(f"筛选后: {len(gdf_filtered):,} 个点")

    # 显示图层选项
    st.sidebar.header("🗺️ 图层选项")
    show_road_network = st.sidebar.checkbox("显示路网", value=True, key="show_road")
    show_road_labels = st.sidebar.checkbox("显示道路名称", value=True, key="show_labels")
    show_risk_grading = st.sidebar.checkbox("启用风险分级", value=True, key="show_risk")
    show_subsidence_hotspots = st.sidebar.checkbox("显示沉降热点", value=True, key="show_hotspots")

    # ==================== AI报告生成配置 ====================
    st.sidebar.header("🤖 AI报告生成")
    deepseek_api_key = st.sidebar.text_input(
        "DeepSeek API Key",
        type="password",
        placeholder="sk-...",
        help="在 https://platform.deepseek.com/api_keys 获取",
        key="api_key_input"
    )
    st.sidebar.caption("💡 留空则使用模拟报告")

    # ==================== 道路风险分析 ====================
    roads_with_risk = None
    if show_road_network and gdf_roads is not None and show_risk_grading and HAS_GEOPANDAS:
        with st.spinner("正在计算道路风险..."):
            roads_with_risk = calculate_road_risk(gdf_insar, gdf_roads, velocity_col)

        if roads_with_risk is not None:
            # 道路风险统计
            st.header("🚧 道路风险分级")

            risk_counts = roads_with_risk['risk_level'].value_counts()
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                high_count = risk_counts.get('high', 0)
                st.metric("🔴 高风险", high_count)
            with col2:
                medium_count = risk_counts.get('medium', 0)
                st.metric("🟠 中风险", medium_count)
            with col3:
                low_count = risk_counts.get('low', 0)
                st.metric("🟢 低风险", low_count)
            with col4:
                unknown_count = risk_counts.get('unknown', 0)
                st.metric("⚪ 无数据", unknown_count)

            # 按道路类型统计
            with st.expander("📊 按道路类型统计"):
                if 'highway' in roads_with_risk.columns:
                    type_stats = roads_with_risk.groupby('highway').agg({
                        'risk_level': lambda x: (x == 'high').sum(),
                        'name': 'count'
                    }).rename(columns={'risk_level': '高风险数', 'name': '总数'})
                    st.dataframe(type_stats, use_container_width=True)

            st.markdown("---")

    # ==================== 地图可视化 ====================
    st.header("🗺️ 速度场分布图")

    # 准备PyDeck数据
    df_for_map = gdf_filtered[['longitude', 'latitude', velocity_col]].copy()
    df_for_map.columns = ['lon', 'lat', 'velocity']

    # 定义颜色方案 (数据范围: -579 ~ 505 mm/year)
    def get_color(value):
        if value < -200:
            return [255, 0, 0, 200]     # 红色 - 严重沉降
        elif value < -50:
            return [255, 165, 0, 200]   # 橙色 - 明显沉降
        elif value < -10:
            return [255, 255, 0, 200]   # 黄色 - 轻微沉降
        elif value < 10:
            return [100, 200, 100, 200]  # 浅绿 - 稳定
        elif value < 100:
            return [0, 150, 255, 200]    # 蓝色 - 轻微抬升
        else:
            return [0, 0, 200, 255]       # 深蓝 - 明显抬升

    df_for_map['color'] = df_for_map['velocity'].apply(get_color)

    # ==================== 图层创建 ====================
    layers = []

    # 1. 路网图层（如果启用）
    road_df_for_table = None
    if show_road_network and gdf_roads is not None:
        try:
            # 使用风险分级数据或原始数据
            source_data = roads_with_risk if (show_risk_grading and roads_with_risk is not None) else gdf_roads

            # 转换路网数据
            road_data = []
            road_table_data = []
            for idx, row in source_data.iterrows():
                # 处理GeoPandas几何对象或演示数据
                if hasattr(row, 'geometry') and hasattr(row.geometry, 'coords'):
                    # GeoPandas GeoDataFrame
                    coords = list(row.geometry.coords)
                    coords_numeric = [[float(c[0]), float(c[1])] for c in coords]
                    center_idx = len(coords) // 2
                    center_lon, center_lat = coords[center_idx]
                elif 'path' in row:
                    # 演示数据（DataFrame，已有path列）
                    coords_numeric = row['path']
                    center_lon, center_lat = coords_numeric[0]
                else:
                    # 跳过无法处理的数据
                    continue

                # 风险等级颜色
                risk_level = row.get('risk_level', 'unknown')
                if show_risk_grading and roads_with_risk is not None:
                    risk_colors = {
                        'high': [255, 0, 0, 255],      # 红色
                        'medium': [255, 165, 0, 255],  # 橙色
                        'low': [0, 200, 100, 255],     # 绿色
                        'unknown': [100, 100, 100, 200]  # 灰色
                    }
                    color = risk_colors.get(risk_level, [100, 100, 100, 200])
                else:
                    color = [50, 150, 200, 255]  # 默认青色

                road_info = {
                    'path': coords_numeric,
                    'name': str(row.get('name', f'道路{idx}')),
                    'type': str(row.get('highway', 'unknown')),
                    'color': color,
                    'center_lon': center_lon,
                    'center_lat': center_lat
                }

                # 添加风险信息
                if show_risk_grading and roads_with_risk is not None:
                    road_info['risk'] = risk_level
                    road_info['avg_velocity'] = float(row.get('velocity_mean', 0))
                    road_info['point_count'] = int(row.get('point_count', 0))

                    # 添加到表格数据
                    road_table_data.append({
                        '道路名称': road_info['name'],
                        '类型': road_info['type'],
                        '风险等级': risk_level,
                        '平均速率 (mm/yr)': f"{road_info['avg_velocity']:.1f}",
                        '监测点数': road_info['point_count']
                    })

                road_data.append(road_info)

            df_roads = pd.DataFrame(road_data)

            # 路网图层 - 使用每条道路自己的颜色
            road_layer = pdk.Layer(
                "PathLayer",
                data=df_roads,
                get_path="path",
                get_width=8,
                get_color="color",
                pickable=True,
                auto_highlight=True,
                highlight_color=[255, 255, 0, 255]
            )
            layers.append(road_layer)

            # 道路名称标签图层
            if show_road_labels:
                text_layer = pdk.Layer(
                    "TextLayer",
                    data=df_roads,
                    get_position=["center_lon", "center_lat"],
                    get_text="name",
                    get_color=[0, 0, 0, 255],
                    get_size=12,
                    get_alignment_baseline="bottom",
                    pickable=False,
                    sizeUnits="pixels"
                )
                layers.append(text_layer)

            # 保存道路数据用于表格显示
            if road_table_data:
                road_df_for_table = pd.DataFrame(road_table_data)

            st.success(f"✅ 已加载 {len(df_roads)} 条道路" +
                      (" (风险分级模式)" if show_risk_grading and roads_with_risk is not None else ""))

        except Exception as e:
            st.error(f"❌ 路网加载失败: {e}")

    # 2. InSAR点图层
    insar_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_for_map,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=150,
        pickable=True,
        auto_highlight=True,
        radius_scale=1,
    )
    layers.append(insar_layer)

    # 根据当前数据范围计算合适的视图状态（确保每次刷新都居中）
    view_state = calculate_view_state(gdf_filtered)

    # 渲染地图 - 使用event_state来捕获视图变化
    tooltip_text = {
        "html": "<b>速度</b>: {velocity} mm/yr<br/><b>纬度</b>: {lat}<br/><b>经度</b>: {lon}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

    # 如果有道路，增强tooltip
    if show_road_network and road_df_for_table is not None:
        road_tooltip = {
            "html": "<b>道路</b>: {name}<br/><b>类型</b>: {type}<br/><b>风险</b>: {risk}<br/><b>平均速率</b>: {avg_velocity} mm/yr<br/><b>监测点</b>: {point_count}",
            "style": {
                "backgroundColor": "#2E86AB",
                "color": "white"
            }
        }
    else:
        road_tooltip = None

    # 创建地图组件
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/light-v10",
        tooltip=tooltip_text
    )

    # 渲染地图
    st.pydeck_chart(deck)

    # ==================== 道路详情表格 ====================
    if road_df_for_table is not None:
        with st.expander("📋 道路详情列表", expanded=False):
            st.dataframe(road_df_for_table, use_container_width=True, height=300)

    # ==================== 沉降热点 ====================
    if show_subsidence_hotspots:
        st.header("🔴 沉降热点分析")

        # 根据调整后的阈值 (mm/year)
        severe_subsidence = gdf_filtered[gdf_filtered[velocity_col] < -200]
        moderate_subsidence = gdf_filtered[
            (gdf_filtered[velocity_col] >= -200) &
            (gdf_filtered[velocity_col] < -50)
        ]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🔴 严重沉降点", len(severe_subsidence), help="< -200 mm/yr")
        with col2:
            st.metric("🟠 明显沉降点", len(moderate_subsidence), help="-200 ~ -50 mm/yr")
        with col3:
            stable_count = len(gdf_filtered) - len(severe_subsidence) - len(moderate_subsidence)
            st.metric("🟢 稳定点", stable_count, help="> -50 mm/yr")

        if len(severe_subsidence) > 0:
            st.info(f"💡 严重沉降区域平均速率: {severe_subsidence[velocity_col].mean():.1f} mm/yr")
            st.warning(f"⚠️ 发现 {len(severe_subsidence)} 个严重沉降点，建议重点关注！")

    # ==================== AI报告生成 ====================
    st.markdown("---")
    st.header("🤖 AI智能分析报告")

    col1, col2 = st.columns([3, 1])

    with col2:
        generate_report = st.button("📊 生成AI报告", type="primary", use_container_width=True)

    with col1:
        st.info("💡 点击按钮生成AI分析报告，包含沉降机理分析、风险评估和防治建议")

    if generate_report:
        with st.spinner("🔄 正在生成AI分析报告，这可能需要30秒..."):
            # 设置API key
            if deepseek_api_key:
                import os
                os.environ['DEEPSEEK_API_KEY'] = deepseek_api_key

            try:
                report, summary = generate_insar_report(gdf_insar, roads_with_risk, velocity_col)

                # 显示报告
                st.success("✅ 报告生成成功！")
                st.markdown("---")

                # 报告内容
                st.markdown(report)

                # 提供下载
                st.download_button(
                    label="📥 下载报告",
                    data=report,
                    file_name=f"InSAR分析报告_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"❌ 报告生成失败: {str(e)}")
                st.info("💡 提示：请检查DeepSeek API Key是否正确配置")

    else:
        # 显示默认提示
        st.markdown("""
        <div style='padding: 20px; background: #f0f2f6; border-radius: 10px; text-align: center;'>
            <h3>📋 点击"生成AI报告"获取智能分析</h3>
            <p style='color: #666;'>AI将基于当前数据生成包含沉降机理分析、风险评估和防治建议的专业报告</p>
        </div>
        """, unsafe_allow_html=True)

else:
    st.error("❌ 数据未加载")
    if data_source == "默认数据（北京）":
        st.info(f"💡 请检查文件是否存在: `{PROCESSED_DATA_DIR / 'beijing_velocity_aggregated.shp'}`")
    else:
        st.info("💡 请上传数据文件或切换到默认数据")

# ==================== 页脚 ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>InSAR Web可视化平台 | 基于Streamlit与PyDeck | 数据来源: Month2 MT-InSAR项目</p>
    <p><small>操作提示：鼠标拖拽平移，滚轮缩放，右键拖拽旋转视角</small></p>
</div>
""", unsafe_allow_html=True)
