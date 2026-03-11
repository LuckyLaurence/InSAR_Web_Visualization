# InSAR Web可视化平台

基于Streamlit的InSAR沉降监测数据Web可视化平台，支持交互式地图浏览、空间分析和AI报告生成。

---

## 项目概述

本项目将Month1（并行处理）和Month2（MT-InSAR时序分析）的成果通过Web平台进行可视化展示，实现：
- InSAR形变数据的3D地图可视化
- 与城市路网/管线的空间叠加分析
- 沉降风险评估与分级
- AI自动生成分析报告

---

## 技术栈

- **前端框架**: Streamlit
- **地图组件**: PyDeck (3D可视化)
- **空间分析**: GeoPandas, Shapely
- **外部数据**: OpenStreetMap API
- **AI集成**: DeepSeek API
- **数据可视化**: Matplotlib, Plotly
- **部署**: Streamlit Cloud

---

## 项目结构

```
InSAR_Web_Visualization/
├── data/
│   ├── raw/              # 原始数据（从Month2复制）
│   ├── processed/        # 处理后的数据（Shapefile等）
│   └── external/         # 外部数据（OSM路网等）
├── src/
│   ├── app.py           # Streamlit主应用
│   ├── components/      # UI组件
│   ├── utils/           # 工具函数
│   └── api/             # AI API调用
├── config/
│   └── config.py        # 配置文件
├── docs/
│   └── README.md        # 项目文档
├── output/
│   └── demo_video.mp4   # 演示视频
└── requirements.txt     # Python依赖
```

---

## 开发计划

| Day | 任务 | 预计耗时 | 状态 |
|-----|------|----------|------|
| 01 | GIS数据转换（QGIS） | 4h | ⏳ 进行中 |
| 02 | 下载OSM路网数据 | 4h | ⏸️ 待开始 |
| 03-04 | Web基础+数据加载 | 6h | ⏸️ 待开始 |
| 05-06 | 路网加载+交互筛选 | 11h | ⏸️ 待开始 |
| 07-08 | 空间连接+风险分级 | 10h | ⏸️ 待开始 |
| 09-12 | AI集成（API+Prompt） | 20h | ⏸️ 待开始 |
| 13-14 | 美化+部署 | 9h | ⏸️ 待开始 |
| 15 | 演示视频 | 6h | ⏸️ 待开始 |

---

## 快速开始

```bash
# 创建虚拟环境
cd InSAR_Web_Visualization
conda create -n insar_web python=3.10
conda activate insar_web

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run src/app.py
```

---

## 数据来源

- **InSAR数据**: 来自Month2项目（北京地区地表形变监测）
- **路网数据**: OpenStreetMap (https://www.openstreetmap.org/)
- **API服务**: DeepSeek (https://platform.deepseek.com/)

---

**项目开始时间**: 2026-02-24
**预计完成时间**: 2026-03-20
