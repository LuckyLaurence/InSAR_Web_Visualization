# Day 13-14: Web数据导入功能

## 阶段目标
实现Web界面的数据导入功能，用户无需技术背景即可上传自己的InSAR数据进行可视化。

## 完成内容

### 1. 数据导入模块
**文件**: `src/utils/data_import.py`

#### 支持的文件格式
| 格式 | 扩展名 | 说明 |
|------|--------|------|
| CSV | .csv | 最通用，Excel可导出 |
| GeoJSON | .geojson, .json | Web标准 |
| Excel | .xlsx, .xls | 用户友好 |
| Shapefile | .zip | 专业GIS格式 |

#### 核心功能
```python
# 文件处理
process_uploaded_file(uploaded_file)
├── 格式识别
├── 数据解析
├── 列名标准化
└── 坐标提取

# 数据验证
validate_insar_data(df)
├── 必需列检查
├── 坐标范围验证
├── NaN值检查
└── 数据摘要生成
```

### 2. Web界面集成

#### 侧边栏上传组件
```python
# 数据源选择
data_source = st.sidebar.selectbox(
    "选择数据源",
    ["默认数据（北京）", "上传数据"]
)

# 文件上传
uploaded_file = st.sidebar.file_uploader(
    "选择数据文件",
    type=['csv', 'geojson', 'json', 'xlsx', 'xls', 'zip']
)
```

#### 数据预览
- 上传后立即显示数据摘要
- 点数、坐标范围、速度范围
- 缺失值统计

### 3. 用户体验优化

#### 列名兼容
支持多种命名方式：
- 经度: `lon`, `lng`, `long` → `longitude`
- 纬度: `lat` → `latitude`
- 速度: `vel`, `rate`, `subsidence` → `velocity`

#### 错误提示
- 详细的错误信息
- 格式示例展示
- 下载模板功能

#### 数据验证
- 坐标范围检查 (-180~180, -90~90)
- NaN值比例检查
- 必需字段检查

## 数据格式要求

### CSV格式示例
```csv
longitude,latitude,velocity
116.4074,39.9042,-25.3
116.4081,39.9050,-12.8
116.4090,39.9060,-5.2
```

### GeoJSON格式
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [116.4074, 39.9042]
      },
      "properties": {
        "velocity": -25.3
      }
    }
  ]
}
```

## 技术要点

### 文件处理
```python
# 使用BytesIO处理上传文件
file_content = BytesIO(uploaded_file.getvalue())
df = pd.read_csv(file_content)
```

### GeoDataFrame转换
```python
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.longitude, df.latitude),
    crs="EPSG:4326"
)
```

### 列名标准化
```python
col_mapping = {
    'lon': 'longitude',
    'lat': 'latitude',
    'vel': 'velocity'
}
df = df.rename(columns=col_mapping)
```

## 使用流程

1. **选择数据源**：侧边栏选择"上传数据"
2. **上传文件**：点击"Browse files"选择文件
3. **数据验证**：自动验证并显示摘要
4. **确认使用**：点击"使用此数据"按钮
5. **查看可视化**：自动生成地图和分析

## 产品价值

| 特性 | 价值 |
|------|------|
| 无需技术背景 | 客户自主使用 |
| 多格式支持 | 兼容各种数据源 |
| 即时反馈 | 快速验证数据 |
| 友好错误提示 | 降低使用门槛 |

## 后续优化

- [ ] 添加数据下载模板功能
- [ ] 支持拖拽上传
- [ ] 大文件分块处理
- [ ] 历史记录功能

## 下一步计划
- Month3项目总结
- 简历更新
- 项目展示准备
