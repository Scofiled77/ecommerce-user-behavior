# -*- coding: utf-8 -*-
"""纯 Python 标准库生成 DOCX（不依赖 python-docx）。

docx 本质是 ZIP + XML，本脚本用 zipfile + 字符串模板构建基础 Word 文档，
支持标题、段落、表格、加粗文本。
"""
import json
import os
import zipfile
from xml.sax.saxutils import escape
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")
RESULT_FILE = os.path.join(OUTPUT_DIR, "analysis_result.json")
DOCX_FILE = os.path.join(OUTPUT_DIR, "电商用户行为分析报告.docx")


# ============ DOCX XML 模板 ============

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/>
        <w:sz w:val="21"/>
        <w:szCs w:val="21"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:after="120" w:line="360" w:lineRule="auto"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:pPr><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/><w:b/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:pPr><w:spacing w:before="280" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/><w:b/><w:sz w:val="30"/><w:color w:val="667EEA"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:pPr><w:spacing w:before="200" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/><w:b/><w:sz w:val="26"/></w:rPr>
  </w:style>
</w:styles>"""


def xml_text(text, bold=False):
    """生成带格式的文本 run XML。"""
    text = escape(str(text))
    if bold:
        return f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'
    return f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r>'


def xml_para(text, style=None, bold=False):
    """生成段落 XML。"""
    pPr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    return f'<w:p>{pPr}{xml_text(text, bold)}</w:p>'


def xml_table(headers, rows):
    """生成表格 XML。"""
    xml = '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
    xml += '<w:tblW w:w="5000" w:type="pct"/>'
    xml += '<w:tblBorders>'
    for border in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        xml += f'<w:{border} w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
    xml += '</w:tblBorders></w:tblPr>'

    # 表头
    xml += '<w:tr>'
    for h in headers:
        xml += f'<w:tc><w:tcPr><w:shd w:val="clear" w:fill="667EEA"/></w:tcPr>'
        xml += f'<w:p><w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr>'
        xml += f'<w:t xml:space="preserve">{escape(str(h))}</w:t></w:r></w:p></w:tc>'
    xml += '</w:tr>'

    # 数据行
    for row in rows:
        xml += '<w:tr>'
        for cell in row:
            xml += '<w:tc><w:p>'
            xml += xml_text(cell)
            xml += '</w:p></w:tc>'
        xml += '</w:tr>'

    xml += '</w:tbl>'
    # 表后空段
    xml += '<w:p/>'
    return xml


def generate_docx(r):
    """从分析结果 JSON 生成 DOCX。"""
    meta = r["meta"]
    pv = r["pv_uv"]
    fn = r["funnel"]
    rfm = r["rfm"]
    rp = r["repurchase"]
    cat = r["category"]
    hr = r["hourly_pattern"]

    body = []

    # 标题
    body.append(xml_para("电商用户行为分析报告", "Heading1"))
    body.append(xml_para(f"数据来源：{meta['data_source']}"))
    body.append(xml_para(f"时间范围：{meta['time_range']}"))
    body.append(xml_para(f"样本规模：{meta['total_records']:,} 条行为记录\n"))

    # 一、摘要
    body.append(xml_para("一、分析摘要", "Heading2"))
    body.append(xml_para(
        f"本报告基于淘宝用户行为数据（2017.11.25-12.03，共9天），对 {meta['total_records']:,} 条行为记录"
        f"进行清洗与分析，覆盖 {pv['total_uv']:,} 个活跃用户，从 PV/UV 趋势、行为转化漏斗、"
        f"RFM 用户分群、复购率、品类差异、活跃时段 6 个维度进行深度分析。"
    ))
    body.append(xml_para("核心发现：", bold=True))
    findings = [
        f"总 PV {pv['total_pv']:,}，日均 PV {pv['avg_daily_pv']:,.0f}，人均浏览 {pv['pv_per_user']} 次",
        f"浏览→购买转化率 {fn['pv_to_buy_rate']}%，加购→购买转化率 {fn['cart_to_buy_rate']}%",
        f"RFM 分群识别出 {rfm['total_buyers']} 个购买用户，重要价值用户占比最高",
        f"跨日复购率 {rp['repurchase_rate']}%，多次购买率 {rp['multi_buy_rate']}%",
        f"品类总数 {cat['total_categories']} 个，TOP10 贡献主要销量",
        f"活跃高峰在 {hr['peak_pv_hour']}:00，午间+晚间双高峰",
    ]
    for f in findings:
        body.append(xml_para(f"• {f}"))

    # 二、PV/UV
    body.append(xml_para("二、PV/UV 趋势分析", "Heading2"))
    headers = ["日期", "PV(浏览量)", "UV(访客数)"]
    rows = [[d["date"], f"{d['pv']:,}", f"{d['uv']:,}"] for d in pv["daily"]]
    body.append(xml_table(headers, rows))
    body.append(xml_para(
        f"总 PV {pv['total_pv']:,} | 总 UV {pv['total_uv']:,} | 日均 PV {pv['avg_daily_pv']:,.0f} | 人均 PV {pv['pv_per_user']}",
        bold=True
    ))
    body.append(xml_para("分析结论：周末 PV 和 UV 均高于工作日，用户活跃存在明显周期性。建议在周末加大促销活动和广告投放力度。"))

    # 三、漏斗
    body.append(xml_para("三、行为转化漏斗分析", "Heading2"))
    body.append(xml_para("3.1 各行为总量", "Heading3"))
    bc = fn["behavior_count"]
    total_b = sum(bc.values())
    headers = ["行为类型", "记录数", "占比"]
    rows = [[b, f"{bc[b]:,}", f"{bc[b]*100/total_b:.1f}%"] for b in ["pv", "fav", "cart", "buy"]]
    body.append(xml_table(headers, rows))

    body.append(xml_para("3.2 用户级漏斗（按用户去重）", "Heading3"))
    headers = ["漏斗阶段", "用户数", "转化率"]
    rows = [[f["stage"], f"{f['users']:,}", f"{f['rate']}%"] for f in fn["funnel"]]
    body.append(xml_table(headers, rows))

    body.append(xml_para("关键转化率：", bold=True))
    body.append(xml_para(f"• 浏览→购买：{fn['pv_to_buy_rate']}%"))
    body.append(xml_para(f"• 加购→购买：{fn['cart_to_buy_rate']}%"))
    body.append(xml_para(f"• 收藏→购买：{fn['fav_to_buy_rate']}%"))
    body.append(xml_para(
        f"分析结论：加购用户购买转化率是浏览用户的 {fn['cart_to_buy_rate']/fn['pv_to_buy_rate']:.0f} 倍。"
        "建议针对加购未购用户推送限时优惠，回收潜在订单。"
    ))

    # 四、RFM
    body.append(xml_para("四、RFM 用户分群", "Heading2"))
    body.append(xml_para(f"对 {rfm['total_buyers']} 个购买用户进行 RFM 分群："))
    body.append(xml_para(f"• R (Recency)：最近购买距分析日天数，中位数 {rfm['thresholds']['R_median']} 天"))
    body.append(xml_para(f"• F (Frequency)：9天内购买次数，中位数 {rfm['thresholds']['F_median']} 次"))
    body.append(xml_para(f"• M (Monetary)：购买品类数，中位数 {rfm['thresholds']['M_median']} 个"))
    headers = ["用户分群", "人数", "占比"]
    rows = [[s["segment"], str(s["count"]), f"{s['pct']}%"]
            for s in rfm["segments"] if s["count"] > 0]
    body.append(xml_table(headers, rows))
    body.append(xml_para("运营建议：重要价值用户推 VIP 权益，重要挽留用户发召回优惠券，一般挽留用户精准再营销。"))

    # 五、复购
    body.append(xml_para("五、复购率分析", "Heading2"))
    body.append(xml_para(f"• 购买用户数：{rp['total_buyers']}"))
    body.append(xml_para(f"• 跨日复购用户：{rp['repurchase_users']} 人（复购率 {rp['repurchase_rate']}%）"))
    body.append(xml_para(f"• 多次购买用户：{rp['multi_buy_users']} 人（多次购买率 {rp['multi_buy_rate']}%）"))
    headers = ["购买次数", "用户数"]
    rows = [[b["range"], str(b["users"])] for b in rp["buy_dist"]]
    body.append(xml_table(headers, rows))
    body.append(xml_para("分析结论：超过半数购买用户会再次购买，建议通过会员积分、组合推荐提升复购频次。"))

    # 六、品类
    body.append(xml_para("六、品类差异分析", "Heading2"))
    body.append(xml_para(f"覆盖 {cat['total_categories']} 个品类，TOP10 热销品类（按购买量）："))
    headers = ["品类", "浏览量", "收藏", "加购", "购买", "转化率"]
    rows = [[f"品类{c['category_id']}", f"{c['pv']:,}", str(c["fav"]), str(c["cart"]),
             str(c["buy"]), f"{c['buy_rate']}%"] for c in cat["top10_by_buy"]]
    body.append(xml_table(headers, rows))
    body.append(xml_para("分析结论：TOP10 品类贡献大部分销量，长尾效应明显。建议头部品类加大库存，尾部品类 bundling 搭售。"))

    # 七、时段
    body.append(xml_para("七、用户活跃时段分析", "Heading2"))
    body.append(xml_para(f"浏览高峰：{hr['peak_pv_hour']}:00 | 购买高峰：{hr['peak_buy_hour']}:00"))
    headers = ["时段", "浏览(pv)", "加购(cart)", "购买(buy)"]
    rows = [[f"{h['hour']}:00", f"{h['pv']:,}", str(h["cart"]), str(h["buy"])]
            for h in hr["hourly"]]
    body.append(xml_table(headers, rows))
    body.append(xml_para("分析结论：午间(12:00)+晚间(21:00)双高峰，晚间最活跃。建议限时秒杀安排在 20:00-22:00。"))

    # 八、总结
    body.append(xml_para("八、总结与建议", "Heading2"))
    body.append(xml_para("运营建议：", bold=True))
    suggestions = [
        "转化提升：针对加购未购用户触发限时优惠/Push 提醒（加购转化率 32%）",
        "用户运营：RFM 分群精细化运营，重要价值用户推 VIP 权益",
        "活动排期：限时秒杀/直播带货安排在 20:00-22:00 黄金时段",
        "品类策略：头部品类加大库存曝光，尾部品类 bundling 搭售",
        "复购提升：会员积分体系 + 组合推荐提升复购频次",
    ]
    for s in suggestions:
        body.append(xml_para(f"• {s}"))

    body.append(xml_para(""))
    body.append(xml_para(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"))
    body.append(xml_para("分析工具：Python 标准库（csv/collections/datetime）+ ECharts"))

    # 组装 document.xml
    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
{''.join(body)}
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
</w:body>
</w:document>"""

    # 写入 ZIP
    with zipfile.ZipFile(DOCX_FILE, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CONTENT_TYPES)
        z.writestr('_rels/.rels', RELS)
        z.writestr('word/_rels/document.xml.rels', DOC_RELS)
        z.writestr('word/document.xml', doc_xml)
        z.writestr('word/styles.xml', STYLES)

    file_size = os.path.getsize(DOCX_FILE) / 1024
    print(f"DOCX 报告生成完成！")
    print(f"路径: {DOCX_FILE}")
    print(f"大小: {file_size:.1f} KB")


def main():
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        result = json.load(f)
    generate_docx(result)


if __name__ == "__main__":
    main()
