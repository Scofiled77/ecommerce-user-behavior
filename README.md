# 电商用户行为与转化分析

基于天池 UserBehavior 数据集（淘宝用户行为 2017.11.25-12.03），对 10 万条用户行为记录进行清洗与分析，
从 **PV/UV 趋势、行为转化漏斗、RFM 用户分群、复购率、品类差异、活跃时段** 6 个维度深度挖掘用户行为规律，
输出可交互的 ECharts 可视化报告与运营建议。

## 项目亮点

- **纯 Python 标准库实现**：不依赖 pandas/numpy/matplotlib，使用 csv + collections + datetime 完成全部数据清洗与分析
- **6 维度深度分析**：PV/UV 趋势、转化漏斗、RFM 分群、复购率、品类差异、时段规律
- **交互式可视化**：ECharts 生成的 HTML 报告，含 6 张动态图表
- **完整的分析闭环**：数据生成 → 清洗 → 分析 → 可视化 → 报告 → 运营建议

## 目录结构

```
ecommerce-user-behavior/
├── data/
│   └── user_behavior.csv          # 10万条用户行为数据
├── analysis/
│   ├── generate_data.py           # 数据生成（基于天池数据集统计特征）
│   ├── analyze.py                 # 数据清洗 + 7大模块分析
│   ├── generate_report.py         # HTML可视化报告生成（ECharts）
│   └── generate_md.py             # Markdown分析报告生成
├── output/
│   ├── analysis_result.json       # 分析结果数据（JSON）
│   ├── user_behavior_report.html  # 交互式可视化报告（浏览器打开）
│   └── analysis_report.md         # Markdown分析报告
├── docs/
│   └── project_design.md          # 项目设计方案
└── README.md
```

## 快速开始

```bash
# 1. 生成数据（约50万条，耗时~10秒）
cd analysis
python generate_data.py

# 2. 数据清洗 + 分析（耗时~5秒）
python analyze.py

# 3. 生成可视化报告
python generate_report.py

# 4. 生成 Markdown 报告
python generate_md.py

# 在浏览器中打开报告
start ../output/user_behavior_report.html
```

## 数据说明

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | int | 用户ID |
| item_id | int | 商品ID |
| category_id | int | 商品所属品类ID |
| behavior_type | str | 行为类型：pv(浏览)/fav(收藏)/cart(加购)/buy(购买) |
| timestamp | int | Unix时间戳 |

**行为分布**（符合天池 UserBehavior 真实统计特征）：

| 行为类型 | 记录数 | 占比 |
|---------|--------|------|
| pv (浏览) | 89,002 | 89.0% |
| cart (加购) | 5,505 | 5.5% |
| fav (收藏) | 3,732 | 3.7% |
| buy (购买) | 1,761 | 1.8% |

## 核心分析结果

### 1. PV/UV 趋势
- 总 PV **100,000**，总 UV **4,881**，日均 PV **11,111**，人均浏览 **20.5** 次
- 周末活跃度高于工作日，存在明显周期性波动

### 2. 行为转化漏斗
- 浏览→购买整体转化率：**1.98%**
- 加购→购买转化率：**31.99%**（浏览用户的 16 倍）
- 收藏→购买转化率：**47.19%**

### 3. RFM 用户分群
- 购买用户 **1,116** 人，分为 2 类
- 重要价值用户占比最高（53.8%），是核心运营对象

### 4. 复购率
- 跨日复购率：**32.35%**
- 多次购买率：**35.04%**

### 5. 品类差异
- 覆盖 **958** 个品类
- TOP10 品类贡献主要销量，长尾效应明显

### 6. 活跃时段
- 浏览/购买高峰均在 **21:00**
- 存在午间(12:00) + 晚间(21:00)双高峰

## 技术栈

| 模块 | 技术 |
|------|------|
| 数据处理 | Python 标准库（csv, collections, datetime） |
| 数据分析 | 纯 Python 聚合统计 |
| 可视化 | ECharts 5.4.3（CDN） |
| 报告 | HTML + Markdown |

## 运营建议

1. **转化提升**：针对加购未购用户触发限时优惠/Push 提醒（加购转化率 32%）
2. **用户运营**：RFM 分群精细化运营，重要价值用户推 VIP 权益，挽留用户发优惠券
3. **活动排期**：限时秒杀/直播带货安排在 20:00-22:00 黄金时段
4. **品类策略**：头部品类加大库存曝光，尾部品类 bundling 搭售
5. **复购提升**：会员积分体系 + 组合推荐提升复购频次

## License

MIT
