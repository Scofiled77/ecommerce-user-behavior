# -*- coding: utf-8 -*-
"""生成 Markdown 分析报告（可后续转 docx）。"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")
RESULT_FILE = os.path.join(OUTPUT_DIR, "analysis_result.json")
MD_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")


def generate_markdown(r):
    meta = r["meta"]
    pv = r["pv_uv"]
    fn = r["funnel"]
    rfm = r["rfm"]
    rp = r["repurchase"]
    cat = r["category"]
    hr = r["hourly_pattern"]

    lines = []
    lines.append("# 电商用户行为分析报告\n")
    lines.append(f"> 数据来源：{meta['data_source']}  ")
    lines.append(f"> 时间范围：{meta['time_range']}  ")
    lines.append(f"> 样本规模：{meta['total_records']:,} 条行为记录\n")

    # 摘要
    lines.append("## 一、分析摘要\n")
    lines.append(f"本报告基于淘宝用户行为数据（2017.11.25-12.03，共9天），对 **{meta['total_records']:,}** 条行为记录进行清洗与分析，"
                 f"覆盖 **{pv['total_uv']:,}** 个活跃用户，从 PV/UV 趋势、行为转化漏斗、RFM 用户分群、复购率、品类差异、"
                 f"活跃时段 6 个维度进行深度分析，核心发现如下：\n")
    lines.append(f"- 总 PV **{pv['total_pv']:,}**，日均 PV **{pv['avg_daily_pv']:,.0f}**，人均浏览 **{pv['pv_per_user']}** 次")
    lines.append(f"- 浏览→购买整体转化率仅 **{fn['pv_to_buy_rate']}%**，但加购→购买转化率达 **{fn['cart_to_buy_rate']}%**，收藏→购买达 **{fn['fav_to_buy_rate']}%**")
    lines.append(f"- RFM 分群识别出 **{rfm['total_buyers']}** 个购买用户，重要价值用户占比最高")
    lines.append(f"- 跨日复购率 **{rp['repurchase_rate']}%**，多次购买率 **{rp['multi_buy_rate']}%**")
    lines.append(f"- 品类总数 **{cat['total_categories']}** 个，TOP10 品类贡献主要销量")
    lines.append(f"- 用户活跃高峰在 **{hr['peak_pv_hour']}:00**，存在午间+晚间双高峰\n")

    # PV/UV
    lines.append("## 二、PV/UV 趋势分析\n")
    lines.append("| 日期 | PV(浏览量) | UV(访客数) |")
    lines.append("|------|-----------|-----------|")
    for d in pv["daily"]:
        lines.append(f"| {d['date']} | {d['pv']:,} | {d['uv']:,} |")
    lines.append(f"\n**关键指标：** 总 PV {pv['total_pv']:,} | 总 UV {pv['total_uv']:,} | "
                 f"日均 PV {pv['avg_daily_pv']:,.0f} | 人均 PV {pv['pv_per_user']}\n")
    lines.append("**分析结论：** 周末（11.25/26、12.02/03）PV 和 UV 均高于工作日，用户活跃存在明显周期性。"
                 "建议在周末加大促销活动和广告投放力度，抓住流量高峰窗口。\n")

    # 漏斗
    lines.append("## 三、行为转化漏斗分析\n")
    lines.append("### 3.1 各行为总量\n")
    lines.append("| 行为类型 | 记录数 | 占比 |")
    lines.append("|---------|--------|------|")
    bc = fn["behavior_count"]
    total_b = sum(bc.values())
    for b in ["pv", "fav", "cart", "buy"]:
        lines.append(f"| {b} | {bc[b]:,} | {bc[b]*100/total_b:.1f}% |")
    lines.append("")
    lines.append("### 3.2 用户级漏斗（按用户去重）\n")
    lines.append("| 漏斗阶段 | 用户数 | 转化率 |")
    lines.append("|---------|--------|-------|")
    for f in fn["funnel"]:
        lines.append(f"| {f['stage']} | {f['users']:,} | {f['rate']}% |")
    lines.append(f"\n**关键转化率：**\n")
    lines.append(f"- 浏览→购买：**{fn['pv_to_buy_rate']}%**")
    lines.append(f"- 加购→购买：**{fn['cart_to_buy_rate']}%**")
    lines.append(f"- 收藏→购买：**{fn['fav_to_buy_rate']}%**\n")
    lines.append("**分析结论：** 加购和收藏是强烈的购买意向信号，加购用户购买转化率是浏览用户的 "
                 f"{fn['cart_to_buy_rate']/fn['pv_to_buy_rate']:.0f} 倍。"
                 "建议针对加购未购用户推送限时优惠或降价提醒，预计可回收大量潜在订单。\n")

    # RFM
    lines.append("## 四、RFM 用户分群\n")
    lines.append(f"对 **{rfm['total_buyers']}** 个购买用户进行 RFM 分群：\n")
    lines.append(f"- **R (Recency)**：最近购买距分析日天数，中位数 **{rfm['thresholds']['R_median']}** 天")
    lines.append(f"- **F (Frequency)**：9天内购买次数，中位数 **{rfm['thresholds']['F_median']}** 次")
    lines.append(f"- **M (Monetary)**：购买商品品类数，中位数 **{rfm['thresholds']['M_median']}** 个\n")
    lines.append("| 用户分群 | 人数 | 占比 |")
    lines.append("|---------|------|------|")
    for s in rfm["segments"]:
        if s["count"] > 0:
            lines.append(f"| {s['segment']} | {s['count']} | {s['pct']}% |")
    lines.append(f"\n**均值：** R={rfm['rfm_avg']['avg_R']}天, F={rfm['rfm_avg']['avg_F']}次, M={rfm['rfm_avg']['avg_M']}个品类\n")
    lines.append("**运营建议：**\n")
    lines.append("- **重要价值用户**：推送 VIP 专享权益，提升忠诚度")
    lines.append("- **重要挽留用户**：发送召回优惠券，激活沉睡用户")
    lines.append("- **一般挽留用户**：精准再营销，通过 push/短信触达\n")

    # 复购
    lines.append("## 五、复购率分析\n")
    lines.append(f"- 购买用户数：**{rp['total_buyers']}**")
    lines.append(f"- 跨日复购用户：**{rp['repurchase_users']}** 人（复购率 **{rp['repurchase_rate']}%**）")
    lines.append(f"- 多次购买用户：**{rp['multi_buy_users']}** 人（多次购买率 **{rp['multi_buy_rate']}%**）\n")
    lines.append("### 购买次数分布\n")
    lines.append("| 购买次数 | 用户数 |")
    lines.append("|---------|--------|")
    for b in rp["buy_dist"]:
        lines.append(f"| {b['range']} | {b['users']} |")
    lines.append("\n**分析结论：** 超过半数购买用户会再次购买，平台有一定用户粘性。"
                 "建议通过会员积分、组合推荐等方式进一步提升复购频次。\n")

    # 品类
    lines.append("## 六、品类差异分析\n")
    lines.append(f"覆盖 **{cat['total_categories']}** 个品类，TOP10 热销品类（按购买量）：\n")
    lines.append("| 品类 | 浏览量 | 收藏 | 加购 | 购买 | 购买转化率 |")
    lines.append("|------|--------|------|------|------|-----------|")
    for c in cat["top10_by_buy"]:
        lines.append(f"| 品类{c['category_id']} | {c['pv']:,} | {c['fav']} | {c['cart']} | {c['buy']} | {c['buy_rate']}% |")
    lines.append("\n**分析结论：** TOP10 品类贡献了大部分销量，符合电商长尾分布特征。"
                 "建议对头部品类加大库存和曝光，对尾部品类考虑 bundling 搭售策略。\n")

    # 时段
    lines.append("## 七、用户活跃时段分析\n")
    lines.append(f"- 浏览高峰时段：**{hr['peak_pv_hour']}:00**")
    lines.append(f"- 购买高峰时段：**{hr['peak_buy_hour']}:00**\n")
    lines.append("| 时段 | 浏览(pv) | 加购(cart) | 购买(buy) |")
    lines.append("|------|---------|-----------|----------|")
    for h in hr["hourly"]:
        lines.append(f"| {h['hour']}:00 | {h['pv']:,} | {h['cart']} | {h['buy']} |")
    lines.append("\n**分析结论：** 存在午间(12:00)和晚间(21:00)双高峰，晚间为全天最活跃时段。"
                 "建议将限时秒杀、直播带货等活动安排在 20:00-22:00 黄金时段。\n")

    # 总结
    lines.append("## 八、总结与建议\n")
    lines.append("### 核心发现\n")
    lines.append(f"1. **流量规模**：9天覆盖 {pv['total_uv']:,} 用户、{pv['total_pv']:,} 次浏览，人均 {pv['pv_per_user']} 次")
    lines.append(f"2. **转化瓶颈**：浏览→购买转化率仅 {fn['pv_to_buy_rate']}%，加购/收藏是高价值转化信号")
    lines.append(f"3. **用户价值**：RFM 分群识别出重要价值用户，应重点维护")
    lines.append(f"4. **复购能力**：复购率 {rp['repurchase_rate']}%，超过半数用户会再次购买")
    lines.append(f"5. **品类集中**：TOP10 品类贡献主要销量，长尾效应明显")
    lines.append(f"6. **时段规律**：晚间 21:00 为全天活跃高峰\n")
    lines.append("### 运营建议\n")
    lines.append("- **转化提升**：针对加购未购用户触发限时优惠/Push 提醒")
    lines.append("- **用户运营**：RFM 分群精细化运营，重要价值用户推 VIP 权益，挽留用户发优惠券")
    lines.append("- **活动排期**：限时秒杀/直播带货安排在 20:00-22:00 黄金时段")
    lines.append("- **品类策略**：头部品类加大库存曝光，尾部品类 bundling 搭售")
    lines.append("- **复购提升**：会员积分体系 + 组合推荐提升复购频次\n")
    lines.append("---")
    lines.append(f"\n*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*  ")
    lines.append(f"*分析工具：Python 标准库（csv/collections/datetime）+ ECharts*")

    return "\n".join(lines)


def main():
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        result = json.load(f)

    md = generate_markdown(result)

    with open(MD_FILE, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Markdown 报告生成完成！")
    print(f"路径: {MD_FILE}")
    print(f"大小: {os.path.getsize(MD_FILE)/1024:.1f} KB")


if __name__ == "__main__":
    main()
