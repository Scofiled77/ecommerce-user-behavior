# -*- coding: utf-8 -*-
"""生成 HTML 可视化分析报告（ECharts CDN）。

读取 analyze.py 输出的 JSON 结果，生成包含 7 张图表的交互式 HTML 报告。
"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")
RESULT_FILE = os.path.join(OUTPUT_DIR, "analysis_result.json")
REPORT_FILE = os.path.join(OUTPUT_DIR, "user_behavior_report.html")


def generate_html(result):
    meta = result["meta"]
    pv_uv = result["pv_uv"]
    funnel = result["funnel"]
    rfm = result["rfm"]
    repurchase = result["repurchase"]
    category = result["category"]
    hourly = result["hourly_pattern"]

    # 提取数据
    daily_dates = [d["date"] for d in pv_uv["daily"]]
    daily_pv = [d["pv"] for d in pv_uv["daily"]]
    daily_uv = [d["uv"] for d in pv_uv["daily"]]

    funnel_stages = [f["stage"] for f in funnel["funnel"]]
    funnel_users = [f["users"] for f in funnel["funnel"]]
    funnel_rates = [f["rate"] for f in funnel["funnel"]]

    rfm_segments = [s["segment"] for s in rfm["segments"] if s["count"] > 0]
    rfm_counts = [s["count"] for s in rfm["segments"] if s["count"] > 0]

    buy_dist_ranges = [b["range"] for b in repurchase["buy_dist"]]
    buy_dist_users = [b["users"] for b in repurchase["buy_dist"]]

    cat_labels = [f"品类{c['category_id']}" for c in category["top10_by_buy"]]
    cat_buy = [c["buy"] for c in category["top10_by_buy"]]
    cat_pv = [c["pv"] for c in category["top10_by_buy"]]

    hours = [h["hour"] for h in hourly["hourly"]]
    hourly_pv = [h["pv"] for h in hourly["hourly"]]
    hourly_cart = [h["cart"] for h in hourly["hourly"]]
    hourly_buy = [h["buy"] for h in hourly["hourly"]]

    # RFM 饼图数据（提前构建为 JSON 字符串，避免 f-string 中嵌套 dict）
    rfm_pie_data = json.dumps(
        [{"value": s["count"], "name": s["segment"]} for s in rfm["segments"] if s["count"] > 0],
        ensure_ascii=False
    )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>电商用户行为分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f5f6fa; color: #333; }}
  .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff;
             padding: 40px 30px; text-align: center; }}
  .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
  .header .subtitle {{ font-size: 14px; opacity: 0.85; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px; }}

  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                   gap: 15px; margin-bottom: 30px; }}
  .summary-card {{ background: #fff; border-radius: 10px; padding: 20px; text-align: center;
                   box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .summary-card .value {{ font-size: 28px; font-weight: 700; color: #667eea; }}
  .summary-card .label {{ font-size: 13px; color: #888; margin-top: 5px; }}

  .section {{ background: #fff; border-radius: 10px; padding: 25px; margin-bottom: 25px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .section h2 {{ font-size: 18px; color: #333; margin-bottom: 5px; padding-left: 12px;
                border-left: 4px solid #667eea; }}
  .section .desc {{ font-size: 13px; color: #888; margin: 8px 0 15px 12px; }}
  .chart {{ width: 100%; height: 380px; }}

  .insight {{ background: #f0f4ff; border-left: 4px solid #667eea; padding: 15px 20px;
              margin: 15px 0; border-radius: 0 8px 8px 0; font-size: 14px; line-height: 1.8; }}
  .insight strong {{ color: #667eea; }}
  .footer {{ text-align: center; padding: 20px; color: #aaa; font-size: 12px; }}
</style>
</head>
<body>

<div class="header">
  <h1>电商用户行为分析报告</h1>
  <div class="subtitle">数据来源：天池 UserBehavior 数据集（采样） | 时间范围：2017-11-25 ~ 2017-12-03 | 生成时间：{now_str}</div>
</div>

<div class="container">

  <!-- 核心指标卡片 -->
  <div class="summary-grid">
    <div class="summary-card"><div class="value">{meta['total_records']:,}</div><div class="label">总行为记录</div></div>
    <div class="summary-card"><div class="value">{pv_uv['total_uv']:,}</div><div class="label">活跃用户数(UV)</div></div>
    <div class="summary-card"><div class="value">{pv_uv['pv_per_user']}</div><div class="label">人均浏览次数</div></div>
    <div class="summary-card"><div class="value">{funnel['pv_to_buy_rate']}%</div><div class="label">浏览→购买转化率</div></div>
    <div class="summary-card"><div class="value">{funnel['cart_to_buy_rate']}%</div><div class="label">加购→购买转化率</div></div>
    <div class="summary-card"><div class="value">{repurchase['repurchase_rate']}%</div><div class="label">跨日复购率</div></div>
  </div>

  <!-- 1. PV/UV 趋势 -->
  <div class="section">
    <h2>1. PV/UV 每日趋势</h2>
    <div class="desc">9天内每日页面浏览量(PV)与独立访客数(UV)变化趋势</div>
    <div id="chart-pv-uv" class="chart"></div>
    <div class="insight">
      <strong>分析洞察：</strong>日均 PV {pv_uv['avg_daily_pv']:,.0f}，周末（11-25/26、12-02/03）活跃度高于工作日，
      用户浏览行为存在明显的周期性波动。建议在周末加大促销活动和广告投放力度，抓住流量高峰窗口。
    </div>
  </div>

  <!-- 2. 行为漏斗 -->
  <div class="section">
    <h2>2. 行为转化漏斗（pv → fav → cart → buy）</h2>
    <div class="desc">用户从浏览到最终购买的各阶段转化情况（按用户去重）</div>
    <div id="chart-funnel" class="chart"></div>
    <div class="insight">
      <strong>分析洞察：</strong>浏览→购买整体转化率仅 {funnel['pv_to_buy_rate']}%，但<strong>加购→购买转化率达 {funnel['cart_to_buy_rate']}%</strong>，
      收藏→购买转化率达 {funnel['fav_to_buy_rate']}%。说明加购/收藏是强烈的购买意向信号，
      应针对加购未购用户推送限时优惠或降价提醒，预计可回收大量潜在订单。
    </div>
  </div>

  <!-- 3. RFM 分群 -->
  <div class="section">
    <h2>3. RFM 用户分群</h2>
    <div class="desc">基于 Recency(最近购买时间)、Frequency(购买频次)、Monetary(购买品类数) 的8类用户分群</div>
    <div id="chart-rfm" class="chart"></div>
    <div class="insight">
      <strong>分析洞察：</strong>购买用户 {rfm['total_buyers']} 人，其中<strong>重要价值用户占比最高</strong>。
      R 中位数 {rfm['thresholds']['R_median']} 天、F 中位数 {rfm['thresholds']['F_median']} 次、M 中位数 {rfm['thresholds']['M_median']} 个品类。
      建议对重要价值用户推送 VIP 专享权益，对重要挽留用户发送召回优惠券，对一般挽留用户进行精准再营销。
    </div>
  </div>

  <!-- 4. 复购率 -->
  <div class="section">
    <h2>4. 复购率与购买次数分布</h2>
    <div class="desc">购买用户的购买次数分布及复购情况</div>
    <div id="chart-repurchase" class="chart"></div>
    <div class="insight">
      <strong>分析洞察：</strong>跨日复购率 <strong>{repurchase['repurchase_rate']}%</strong>，
      多次购买率 {repurchase['multi_buy_rate']}%。超过半数购买用户会再次购买，
      说明平台商品质量和用户体验有一定保障。建议通过会员积分、组合推荐等方式进一步提升复购频次。
    </div>
  </div>

  <!-- 5. TOP10 热销品类 -->
  <div class="section">
    <h2>5. TOP10 热销品类分析</h2>
    <div class="desc">按购买量排名的TOP10品类，展示浏览量与购买量对比</div>
    <div id="chart-category" class="chart"></div>
    <div class="insight">
      <strong>分析洞察：</strong>品类 {category['top10_by_buy'][0]['category_id']} 购买量最高（{category['top10_by_buy'][0]['buy']} 次），
      TOP10 品类贡献了大部分销量，符合电商长尾分布特征。建议对头部品类加大库存和曝光，
      对尾部品类考虑 bundling 搭售策略。
    </div>
  </div>

  <!-- 6. 24小时活跃时段 -->
  <div class="section">
    <h2>6. 24小时用户活跃时段</h2>
    <div class="desc">各时段浏览、加购、购买行为分布</div>
    <div id="chart-hourly" class="chart"></div>
    <div class="insight">
      <strong>分析洞察：</strong>浏览高峰在 <strong>{hourly['peak_pv_hour']}:00</strong>，
      购买高峰同样在 <strong>{hourly['peak_buy_hour']}:00</strong>。
      存在午间(12:00)和晚间(21:00)双高峰，晚间为全天最活跃时段。
      建议将限时秒杀、直播带货等活动安排在 20:00-22:00 黄金时段。
    </div>
  </div>

</div>

<div class="footer">
  电商用户行为分析报告 | 数据来源：天池 UserBehavior 数据集（采样） | 分析工具：Python 标准库 + ECharts
</div>

<script>
// 1. PV/UV 趋势
var chart1 = echarts.init(document.getElementById('chart-pv-uv'));
chart1.setOption({{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: ['PV(浏览量)', 'UV(访客数)'], top: 5 }},
  grid: {{ left: '8%', right: '5%', bottom: '12%', top: '15%' }},
  xAxis: {{ type: 'category', data: {json.dumps(daily_dates, ensure_ascii=False)} }},
  yAxis: [
    {{ type: 'value', name: 'PV', position: 'left' }},
    {{ type: 'value', name: 'UV', position: 'right' }}
  ],
  series: [
    {{ name: 'PV(浏览量)', type: 'bar', data: {daily_pv}, itemStyle: {{ color: '#667eea' }}, barWidth: '40%' }},
    {{ name: 'UV(访客数)', type: 'line', yAxisIndex: 1, data: {daily_uv}, itemStyle: {{ color: '#f39c12' }},
       lineStyle: {{ width: 3 }}, symbol: 'circle', symbolSize: 8 }}
  ]
}});

// 2. 漏斗图
var chart2 = echarts.init(document.getElementById('chart-funnel'));
chart2.setOption({{
  tooltip: {{ trigger: 'item', formatter: '{{b}}<br/>用户数: {{c}} ({{d}}%)' }},
  series: [{{
    type: 'funnel',
    left: '15%', right: '15%', top: '10%', bottom: '10%',
    minSize: '30%',
    label: {{ show: true, position: 'inside', formatter: '{{b}}\\n{{c}}人 ({{d}}%)' }},
    data: [
      {{ value: {funnel_users[0]}, name: '{funnel_stages[0]}' }},
      {{ value: {funnel_users[1]}, name: '{funnel_stages[1]}' }},
      {{ value: {funnel_users[2]}, name: '{funnel_stages[2]}' }},
      {{ value: {funnel_users[3]}, name: '{funnel_stages[3]}' }}
    ],
    itemStyle: {{ borderColor: '#fff', borderWidth: 2 }},
    color: ['#667eea', '#764ba2', '#f39c12', '#e74c3c']
  }}]
}});

// 3. RFM 饼图
var chart3 = echarts.init(document.getElementById('chart-rfm'));
chart3.setOption({{
  tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}}人 ({{d}}%)' }},
  legend: {{ orient: 'vertical', left: 'left', textStyle: {{ fontSize: 12 }} }},
  series: [{{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['55%', '50%'],
    label: {{ formatter: '{{b}}\\n{{d}}%', fontSize: 11 }},
    data: {rfm_pie_data}
    color: ['#e74c3c', '#f39c12', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c', '#e67e22', '#95a5a6']
  }}]
}});

// 4. 购买次数分布
var chart4 = echarts.init(document.getElementById('chart-repurchase'));
chart4.setOption({{
  tooltip: {{ trigger: 'axis' }},
  grid: {{ left: '10%', right: '8%', bottom: '12%', top: '10%' }},
  xAxis: {{ type: 'category', data: {json.dumps(buy_dist_ranges, ensure_ascii=False)}, axisLabel: {{ fontSize: 12 }} }},
  yAxis: {{ type: 'value', name: '用户数' }},
  series: [{{
    type: 'bar',
    data: {buy_dist_users},
    itemStyle: {{ color: '#667eea' }},
    barWidth: '50%',
    label: {{ show: true, position: 'top' }}
  }}]
}});

// 5. TOP10 品类
var chart5 = echarts.init(document.getElementById('chart-category'));
chart5.setOption({{
  tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
  legend: {{ data: ['浏览量', '购买量'], top: 5 }},
  grid: {{ left: '10%', right: '8%', bottom: '15%', top: '15%' }},
  xAxis: {{ type: 'category', data: {json.dumps(cat_labels, ensure_ascii=False)}, axisLabel: {{ rotate: 30 }} }},
  yAxis: [
    {{ type: 'value', name: '浏览量' }},
    {{ type: 'value', name: '购买量', position: 'right' }}
  ],
  series: [
    {{ name: '浏览量', type: 'bar', data: {cat_pv}, itemStyle: {{ color: '#667eea' }} }},
    {{ name: '购买量', type: 'bar', yAxisIndex: 1, data: {cat_buy}, itemStyle: {{ color: '#e74c3c' }} }}
  ]
}});

// 6. 24小时活跃
var chart6 = echarts.init(document.getElementById('chart-hourly'));
chart6.setOption({{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: ['浏览(pv)', '加购(cart)', '购买(buy)'], top: 5 }},
  grid: {{ left: '8%', right: '5%', bottom: '12%', top: '15%' }},
  xAxis: {{ type: 'category', data: {hours}.map(h => h + ':00') }},
  yAxis: {{ type: 'value' }},
  series: [
    {{ name: '浏览(pv)', type: 'line', data: {hourly_pv}, smooth: true, itemStyle: {{ color: '#667eea' }}, areaStyle: {{ opacity: 0.2 }} }},
    {{ name: '加购(cart)', type: 'line', data: {hourly_cart}, smooth: true, itemStyle: {{ color: '#f39c12' }} }},
    {{ name: '购买(buy)', type: 'line', data: {hourly_buy}, smooth: true, itemStyle: {{ color: '#e74c3c' }} }}
  ]
}});

// 响应式
window.addEventListener('resize', function() {{
  chart1.resize(); chart2.resize(); chart3.resize();
  chart4.resize(); chart5.resize(); chart6.resize();
}});
</script>

</body>
</html>"""
    return html


def main():
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        result = json.load(f)

    html = generate_html(result)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = os.path.getsize(REPORT_FILE) / 1024
    print(f"报告生成完成！")
    print(f"路径: {REPORT_FILE}")
    print(f"大小: {file_size:.1f} KB")


if __name__ == "__main__":
    main()
