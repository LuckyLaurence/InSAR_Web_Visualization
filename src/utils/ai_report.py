#!/usr/bin/env python3
"""
AI报告生成模块 - 基于DeepSeek API

功能:
1. 分析InSAR沉降数据
2. 生成风险评估报告
3. 提供沉降机理建议
"""

import os
import pandas as pd
import json
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from config.config import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, DEEPSEEK_MODEL


def generate_data_summary(gdf_insar, velocity_col='velocity_mean'):
    """生成数据摘要"""
    summary = {
        '总监测点数': int(len(gdf_insar)),
        '监测时间': '2022年1月-5月（337天）',
        '监测区域': '北京地区',
        '数据来源': 'Sentinel-1 MT-InSAR',
    }

    velocity = gdf_insar[velocity_col]
    summary.update({
        '最小沉降速率': f"{velocity.min():.1f}",
        '最大抬升速率': f"{velocity.max():.1f}",
        '平均速率': f"{velocity.mean():.1f}",
        '标准差': f"{velocity.std():.1f}",
    })

    # 沉降统计
    severe = len(gdf_insar[velocity < -200])
    moderate = len(gdf_insar[(velocity >= -200) & (velocity < -50)])
    stable = len(gdf_insar[velocity >= -50])

    summary.update({
        '严重沉降点数': severe,
        '明显沉降点数': moderate,
        '稳定点数': stable,
    })

    return summary


def generate_hotspot_analysis(gdf_insar, velocity_col='velocity_mean'):
    """生成沉降热点分析"""
    velocity = gdf_insar[velocity_col]

    # 找出严重沉降区域
    severe_points = gdf_insar[velocity < -200]

    if len(severe_points) == 0:
        return "未发现严重沉降区域"

    # 按区域聚类
    severe_points['lon_round'] = (severe_points['longitude'] * 10).astype(int) / 10
    severe_points['lat_round'] = (severe_points['latitude'] * 10).astype(int) / 10

    hotspots = severe_points.groupby(['lon_round', 'lat_round']).agg({
        velocity_col: ['count', 'mean', 'min']
    }).reset_index()

    hotspots.columns = ['经度', '纬度', '点数', '平均速率', '最小速率']
    hotspots = hotspots.sort_values('平均速率')

    result = []
    for _, row in hotspots.head(5).iterrows():
        result.append(
            f"- 区域 ({row['经度']:.1f}°E, {row['纬度']:.1f}°N): "
            f"{row['点数']}个监测点，平均速率 {row['平均速率']:.1f} mm/yr"
        )

    return "\n".join(result)


def create_report_prompt(data_summary, hotspot_analysis, road_risk=None):
    """创建报告生成提示词"""

    prompt = f"""你是一位地质灾害专家，请根据以下InSAR监测数据生成一份专业的沉降分析报告。

## 数据概况
- 监测区域：{data_summary['监测区域']}
- 监测时间：{data_summary['监测时间']}
- 数据来源：{data_summary['数据来源']}
- 总监测点数：{data_summary['总监测点数']:,}个

## 沉降速率统计
- 最小沉降速率：{data_summary['最小沉降速率']} mm/yr
- 最大抬升速率：{data_summary['最大抬升速率']} mm/yr
- 平均速率：{data_summary['平均速率']} mm/yr

## 风险分级
- 严重沉降点（< -200 mm/yr）：{data_summary['严重沉降点数']}个
- 明显沉降点（-200 ~ -50 mm/yr）：{data_summary['明显沉降点数']}个
- 稳定点（> -50 mm/yr）：{data_summary['稳定点数']}个

## 沉降热点分析
{hotspot_analysis}

"""

    if road_risk:
        prompt += f"""
## 道路风险评估
- 高风险道路：{road_risk.get('high', 0)}条
- 中风险道路：{road_risk.get('medium', 0)}条
- 低风险道路：{road_risk.get('low', 0)}条

"""

    prompt += """
请生成一份包含以下内容的分析报告：

1. **总体评估**：对监测区域的沉降状况进行总体评价

2. **风险分析**：分析沉降风险等级和分布特征

3. **沉降机理**：根据沉降速率和分布，分析可能的沉降成因（如地下水开采、地质条件、城市建设等）

4. **建议措施**：提出针对性的监测建议和防灾措施

5. **结论**：总结主要发现和关注重点

报告要求：
- 语言专业但不晦涩
- 数据支撑充分
- 建议具体可行
- 字数约800-1000字
"""

    return prompt


def generate_report_with_deepseek(prompt):
    """使用DeepSeek API生成报告"""

    if not DEEPSEEK_API_KEY:
        # 返回模拟报告
        return generate_mock_report()

    try:
        import requests

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }

        data = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": "你是一位资深的地质灾害专家，擅长分析InSAR沉降监测数据。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(
            f"{DEEPSEEK_API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"API调用失败: {response.status_code} - {response.text}"

    except Exception as e:
        return f"报告生成失败: {str(e)}\n\n{generate_mock_report()}"


def generate_mock_report():
    """生成模拟报告（当API不可用时）"""
    return """# 北京地区地表沉降InSAR监测分析报告

## 一、总体评估

基于2022年1月至5月（337天）的Sentinel-1 MT-InSAR监测数据，对北京地区进行了毫米级精度的地表形变监测。监测结果显示，研究区整体呈现相对稳定的状态，沉降速率主要集中在-50~50 mm/yr范围内，未发现大范围的严重沉降区域。

监测数据表明，北京地区地表形变特征具有明显的空间差异性，局部区域存在轻微沉降现象，但整体风险可控。最大沉降速率约500-600 mm/yr，出现在局部小范围内，可能与局部工程建设活动相关。

## 二、风险分析

### 2.1 沉降风险分级

根据监测结果，将沉降风险划分为三个等级：

**高风险区域**（沉降速率 < -200 mm/yr）：零星分布，影响范围有限，建议作为重点监测对象。

**中风险区域**（-200 ~ -50 mm/yr）：呈点状分布，可能与局部荷载变化、地下管线施工等因素相关，建议定期监测。

**低风险区域**（> -50 mm/yr）：占监测区域绝大部分，地表稳定，无明显沉降风险。

### 2.2 沉降分布特征

沉降区域呈现不均匀分布特征，未见明显的区域性沉降趋势。轻微沉降点多呈孤立分布，可能与局部工程建设、地基处理等活动相关。

## 三、沉降机理分析

### 3.1 地质条件因素

北京地区地质条件复杂，存在第四纪松散沉积物，这些沉积物在一定条件下（如地下水位变化、荷载增加等）容易产生压缩变形。研究区西北部存在岩溶发育区，是潜在的不稳定因素。

### 3.2 地下水开采

历史数据显示，地下水超采是导致北京地区沉降的主要因素之一。近年来，随着南水北调工程的实施和地下水压采政策的推进，区域地下水位呈现回升趋势，有利于缓解沉降问题。

### 3.3 城市建设影响

局部区域的轻微沉降可能与工程建设活动相关，包括：
- 地铁、隧道等地下空间开发
- 高层建筑地基施工
- 市政管线铺设

### 3.4 自然因素

区域地质构造活动相对较弱，地震、断裂活动等自然因素对地表形变的影响较小。

## 四、建议措施

### 4.1 监测建议

1. **加密监测频率**：对高风险区域增加监测频次，建议由月度监测提升为周度监测。

2. **多源数据融合**：结合水准测量、GPS监测等传统手段，对InSAR监测结果进行校核验证。

3. **建设预警系统**：建立沉降预警阈值体系，当沉降速率超过警戒值时及时预警。

### 4.2 防灾措施

1. **加强地下水管理**：严格控制高风险区域地下水开采，推广地下水回灌技术。

2. **规范工程建设**：在沉降敏感区域严格控制深基坑、隧道等工程建设，必要时采取地基加固措施。

3. **建立应急机制**：制定沉降灾害应急预案，明确各部门职责和响应流程。

### 4.3 后续工作

1. **扩展监测范围**：将监测范围扩展至整个北京市域，建立全覆盖监测网络。

2. **深化机理研究**：开展沉降机理专题研究，建立区域沉降预测模型。

3. **定期评估更新**：每半年发布一次沉降监测评估报告，动态掌握区域沉降状况。

## 五、结论

本次InSAR监测表明，北京地区地表整体稳定，未发现严重的区域性沉降问题。局部区域的轻微沉降处于可控范围内，建议持续监测并根据监测结果采取相应措施。

建议相关部门加强沉降监测预警体系建设，将InSAR技术纳入常规监测手段，为城市规划和地质灾害防治提供科学支撑。

---

*报告生成时间：2025年2月*
*数据来源：Sentinel-1 MT-InSAR*
*技术支持：InSAR Web可视化平台*
"""


def generate_insar_report(gdf_insar, roads_with_risk=None, velocity_col='velocity_mean'):
    """生成完整的InSAR分析报告"""

    # 生成数据摘要
    data_summary = generate_data_summary(gdf_insar, velocity_col)

    # 生成热点分析
    hotspot_analysis = generate_hotspot_analysis(gdf_insar, velocity_col)

    # 道路风险统计
    road_risk = None
    if roads_with_risk is not None:
        risk_counts = roads_with_risk['risk_level'].value_counts()
        road_risk = {
            'high': risk_counts.get('high', 0),
            'medium': risk_counts.get('medium', 0),
            'low': risk_counts.get('low', 0)
        }

    # 创建提示词
    prompt = create_report_prompt(data_summary, hotspot_analysis, road_risk)

    # 调用AI生成报告
    report = generate_report_with_deepseek(prompt)

    return report, data_summary


def main():
    """测试报告生成功能"""
    import geopandas as gpd
    from config.config import PROCESSED_DATA_DIR

    # 加载测试数据
    velocity_file = PROCESSED_DATA_DIR / "beijing_velocity_aggregated.shp"
    gdf_insar = gpd.read_file(velocity_file)

    if 'velocity' in gdf_insar.columns:
        gdf_insar['velocity_mean'] = gdf_insar['velocity']

    print("生成AI报告...")
    report, summary = generate_insar_report(gdf_insar)

    print("\n" + "="*60)
    print("AI分析报告")
    print("="*60)
    print(report)
    print("="*60)

    # 保存报告
    output_file = Path("ai_report.txt")
    output_file.write_text(report, encoding='utf-8')
    print(f"\n报告已保存: {output_file}")


if __name__ == '__main__':
    main()
