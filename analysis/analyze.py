# -*- coding: utf-8 -*-
"""电商用户行为分析 — 数据清洗 + 核心分析。

使用纯 Python 标准库（csv/collections/datetime）完成全部分析，
不依赖 pandas/numpy/matplotlib。

分析模块：
  1. 数据清洗（去重、缺失值、异常时间、时间解析）
  2. PV/UV 趋势分析（按天 + 按小时）
  3. 行为漏斗分析（pv → fav → cart → buy 转化率）
  4. RFM 用户分群（8 类用户）
  5. 复购率分析
  6. 品类差异分析（TOP 热销品类 + 品类行为分布）
  7. 用户活跃时段分析

输出：JSON 结果文件 + 控制台摘要
"""
import csv
import json
import os
from collections import defaultdict, Counter
from datetime import datetime, timedelta

# ============ 路径配置 ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "..", "data", "user_behavior.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")
RESULT_FILE = os.path.join(OUTPUT_DIR, "analysis_result.json")

# 分析基准日期（数据结束后一天，用于计算 Recency）
ANALYSIS_DATE = datetime(2017, 12, 4, 0, 0, 0)

# 日期标签
DATE_LABELS = ["11-25(六)", "11-26(日)", "11-27(一)", "11-28(二)",
               "11-29(三)", "11-30(四)", "12-01(五)", "12-02(六)", "12-03(日)"]


def load_and_clean(filepath):
    """加载数据并清洗。

    清洗规则：
      - 去重（完全相同的行）
      - 缺失值过滤（任一字段为空）
      - timestamp 异常过滤（超出 2017.11.25~12.3 范围）
      - behavior_type 规范化（只保留 pv/fav/cart/buy）
      - 解析 timestamp 为 datetime + 日期 + 小时
    """
    print(">>> 步骤 1: 数据加载与清洗")

    records = []
    seen = set()
    dropped = {"duplicate": 0, "missing": 0, "ts_invalid": 0, "behavior_invalid": 0}

    valid_behaviors = {"pv", "fav", "cart", "buy"}
    ts_min = int(datetime(2017, 11, 25, 0, 0, 0).timestamp())
    ts_max = int(datetime(2017, 12, 3, 23, 59, 59).timestamp())

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 缺失值过滤
            if not row.get("user_id") or not row.get("item_id") or \
               not row.get("behavior_type") or not row.get("timestamp"):
                dropped["missing"] += 1
                continue

            uid = row["user_id"]
            iid = row["item_id"]
            cat = row["category_id"]
            btype = row["behavior_type"].strip()
            ts_str = row["timestamp"].strip()

            # 行为类型校验
            if btype not in valid_behaviors:
                dropped["behavior_invalid"] += 1
                continue

            try:
                ts = int(ts_str)
            except ValueError:
                dropped["ts_invalid"] += 1
                continue

            # 时间范围校验
            if ts < ts_min or ts > ts_max:
                dropped["ts_invalid"] += 1
                continue

            # 去重
            key = (uid, iid, btype, ts)
            if key in seen:
                dropped["duplicate"] += 1
                continue
            seen.add(key)

            dt = datetime.fromtimestamp(ts)
            records.append({
                "user_id": uid,
                "item_id": iid,
                "category_id": cat,
                "behavior_type": btype,
                "timestamp": ts,
                "datetime": dt,
                "date": dt.strftime("%Y-%m-%d"),
                "hour": dt.hour,
                "day_idx": (dt - datetime(2017, 11, 25)).days,
            })

    total_raw = len(records) + sum(dropped.values())
    print(f"  原始记录: {total_raw}")
    print(f"  清洗后: {len(records)}")
    print(f"  剔除明细: 重复={dropped['duplicate']}, 缺失={dropped['missing']}, "
          f"时间异常={dropped['ts_invalid']}, 行为异常={dropped['behavior_invalid']}")
    return records, dropped


def analyze_pv_uv(records):
    """PV/UV 趋势分析（按天 + 按小时）。"""
    print("\n>>> 步骤 2: PV/UV 趋势分析")

    daily_pv = defaultdict(int)
    daily_uv = defaultdict(set)
    hourly_pv = defaultdict(int)
    hourly_uv = defaultdict(set)

    for r in records:
        daily_pv[r["date"]] += 1
        daily_uv[r["date"]].add(r["user_id"])
        hourly_pv[r["hour"]] += 1
        hourly_uv[r["hour"]].add(r["user_id"])

    # 按日期排序
    dates = sorted(daily_pv.keys())
    daily_pv_list = []
    daily_uv_list = []
    for d in dates:
        idx = (datetime.strptime(d, "%Y-%m-%d") - datetime(2017, 11, 25)).days
        daily_pv_list.append({"date": DATE_LABELS[idx], "pv": daily_pv[d], "uv": len(daily_uv[d])})
        daily_uv_list.append({"date": DATE_LABELS[idx], "uv": len(daily_uv[d])})

    # 按小时排序
    hourly_pv_list = []
    hourly_uv_list = []
    for h in range(24):
        hourly_pv_list.append({"hour": h, "pv": hourly_pv.get(h, 0)})
        hourly_uv_list.append({"hour": h, "uv": len(hourly_uv.get(h, set()))})

    total_pv = sum(daily_pv.values())
    total_uv = len(set(r["user_id"] for r in records))
    avg_daily_pv = total_pv / 9
    avg_daily_uv = total_uv  # UV 是全量去重

    print(f"  总 PV: {total_pv:,}")
    print(f"  总 UV: {total_uv:,}")
    print(f"  日均 PV: {avg_daily_pv:,.0f}")
    print(f"  人均 PV: {total_pv/total_uv:.1f}")

    return {
        "total_pv": total_pv,
        "total_uv": total_uv,
        "avg_daily_pv": round(avg_daily_pv, 0),
        "pv_per_user": round(total_pv / total_uv, 1),
        "daily": daily_pv_list,
        "hourly_pv": hourly_pv_list,
        "hourly_uv": hourly_uv_list,
    }


def analyze_funnel(records):
    """行为漏斗分析：pv → fav → cart → buy。"""
    print("\n>>> 步骤 3: 行为漏斗分析（pv → fav → cart → buy）")

    # 按用户统计每种行为
    user_behaviors = defaultdict(set)
    behavior_total = Counter()

    for r in records:
        user_behaviors[r["user_id"]].add(r["behavior_type"])
        behavior_total[r["behavior_type"]] += 1

    # 漏斗：有 pv 的用户 → 有 fav 的 → 有 cart 的 → 有 buy 的
    users_pv = set()
    users_fav = set()
    users_cart = set()
    users_buy = set()

    for uid, bset in user_behaviors.items():
        if "pv" in bset:
            users_pv.add(uid)
        if "fav" in bset:
            users_fav.add(uid)
        if "cart" in bset:
            users_cart.add(uid)
        if "buy" in bset:
            users_buy.add(uid)

    funnel = [
        {"stage": "浏览(pv)", "users": len(users_pv), "rate": 100.0},
        {"stage": "收藏(fav)", "users": len(users_fav),
         "rate": round(len(users_fav) * 100 / len(users_pv), 2) if users_pv else 0},
        {"stage": "加购(cart)", "users": len(users_cart),
         "rate": round(len(users_cart) * 100 / len(users_pv), 2) if users_pv else 0},
        {"stage": "购买(buy)", "users": len(users_buy),
         "rate": round(len(users_buy) * 100 / len(users_pv), 2) if users_pv else 0},
    ]

    # 行为总量
    behavior_count = {
        "pv": behavior_total.get("pv", 0),
        "fav": behavior_total.get("fav", 0),
        "cart": behavior_total.get("cart", 0),
        "buy": behavior_total.get("buy", 0),
    }

    # 关键转化率
    pv_to_buy_rate = round(behavior_count["buy"] * 100 / behavior_count["pv"], 2)
    cart_to_buy_rate = round(behavior_count["buy"] * 100 / behavior_count["cart"], 2)
    fav_to_buy_rate = round(behavior_count["buy"] * 100 / behavior_count["fav"], 2)

    print(f"  行为总量: pv={behavior_count['pv']:,} fav={behavior_count['fav']:,} "
          f"cart={behavior_count['cart']:,} buy={behavior_count['buy']:,}")
    print(f"  浏览→购买转化率: {pv_to_buy_rate}%")
    print(f"  加购→购买转化率: {cart_to_buy_rate}%")
    print(f"  收藏→购买转化率: {fav_to_buy_rate}%")

    return {
        "funnel": funnel,
        "behavior_count": behavior_count,
        "pv_to_buy_rate": pv_to_buy_rate,
        "cart_to_buy_rate": cart_to_buy_rate,
        "fav_to_buy_rate": fav_to_buy_rate,
    }


def analyze_rfm(records):
    """RFM 用户分群。

    R (Recency): 最近一次购买距分析日(12.04)的天数，越小越好
    F (Frequency): 9天内购买次数，越大越好
    M (Monetary): 购买商品种类数，越大越好

    分群阈值：R/F/M 各取中位数，高于中位数=高，低于=低
    8 类用户：
      R高F高M高 = 重要价值用户
      R高F高M低 = 重要发展用户
      R高F低M高 = 重要保持用户
      R高F低M低 = 重要挽留用户
      R低F高M高 = 一般价值用户
      R低F高M低 = 一般发展用户
      R低F低M高 = 一般保持用户
      R低F低M低 = 一般挽留用户
    """
    print("\n>>> 步骤 4: RFM 用户分群")

    # 只分析有购买行为的用户
    buy_records = [r for r in records if r["behavior_type"] == "buy"]

    user_rfm = {}
    for r in buy_records:
        uid = r["user_id"]
        if uid not in user_rfm:
            user_rfm[uid] = {"last_buy": r["datetime"], "buy_count": 0, "items": set()}
        user_rfm[uid]["last_buy"] = max(user_rfm[uid]["last_buy"], r["datetime"])
        user_rfm[uid]["buy_count"] += 1
        user_rfm[uid]["items"].add(r["item_id"])

    # 计算 R/F/M
    rfm_list = []
    for uid, data in user_rfm.items():
        r_days = (ANALYSIS_DATE - data["last_buy"]).days
        f = data["buy_count"]
        m = len(data["items"])
        rfm_list.append({"user_id": uid, "R": r_days, "F": f, "M": m})

    if not rfm_list:
        print("  无购买用户，跳过 RFM")
        return {"segments": [], "thresholds": {}, "total_buyers": 0}

    # 计算中位数阈值
    r_values = sorted([x["R"] for x in rfm_list])
    f_values = sorted([x["F"] for x in rfm_list])
    m_values = sorted([x["M"] for x in rfm_list])

    n = len(rfm_list)
    r_median = r_values[n // 2]
    f_median = f_values[n // 2]
    m_median = m_values[n // 2]

    # 分群
    SEGMENT_MAP = {
        (1, 1, 1): "重要价值用户",
        (1, 1, 0): "重要发展用户",
        (1, 0, 1): "重要保持用户",
        (1, 0, 0): "重要挽留用户",
        (0, 1, 1): "一般价值用户",
        (0, 1, 0): "一般发展用户",
        (0, 0, 1): "一般保持用户",
        (0, 0, 0): "一般挽留用户",
    }

    segment_count = Counter()
    for x in rfm_list:
        r_high = 1 if x["R"] <= r_median else 0  # R 越小越好
        f_high = 1 if x["F"] >= f_median else 0
        m_high = 1 if x["M"] >= m_median else 0
        seg = SEGMENT_MAP[(r_high, f_high, m_high)]
        segment_count[seg] += 1

    segments = []
    SEGMENT_ORDER = ["重要价值用户", "重要发展用户", "重要保持用户", "重要挽留用户",
                     "一般价值用户", "一般发展用户", "一般保持用户", "一般挽留用户"]
    for seg_name in SEGMENT_ORDER:
        count = segment_count.get(seg_name, 0)
        pct = round(count * 100 / n, 1)
        segments.append({"segment": seg_name, "count": count, "pct": pct})

    print(f"  购买用户数: {n}")
    print(f"  R 中位数: {r_median} 天  F 中位数: {f_median} 次  M 中位数: {m_median} 个品类")
    print(f"  分群结果:")
    for s in segments:
        if s["count"] > 0:
            print(f"    {s['segment']}: {s['count']} 人 ({s['pct']}%)")

    return {
        "total_buyers": n,
        "thresholds": {"R_median": r_median, "F_median": f_median, "M_median": m_median},
        "segments": segments,
        "rfm_avg": {
            "avg_R": round(sum(x["R"] for x in rfm_list) / n, 1),
            "avg_F": round(sum(x["F"] for x in rfm_list) / n, 1),
            "avg_M": round(sum(x["M"] for x in rfm_list) / n, 1),
        },
    }


def analyze_repurchase(records):
    """复购率分析。"""
    print("\n>>> 步骤 5: 复购率分析")

    # 统计每个用户的购买次数
    user_buy_count = Counter()
    user_buy_dates = defaultdict(set)

    for r in records:
        if r["behavior_type"] == "buy":
            user_buy_count[r["user_id"]] += 1
            user_buy_dates[r["user_id"]].add(r["date"])

    total_buyers = len(user_buy_count)
    # 复购用户：在不同天购买 >= 2 次
    repurchase_users = sum(1 for uid, dates in user_buy_dates.items() if len(dates) >= 2)
    # 多次购买用户（总购买次数 >= 2）
    multi_buy_users = sum(1 for uid, count in user_buy_count.items() if count >= 2)

    repurchase_rate = round(repurchase_users * 100 / total_buyers, 2) if total_buyers else 0
    multi_buy_rate = round(multi_buy_users * 100 / total_buyers, 2) if total_buyers else 0

    # 购买次数分布
    buy_dist = Counter()
    for uid, count in user_buy_count.items():
        if count == 1:
            buy_dist["1次"] += 1
        elif count <= 3:
            buy_dist["2-3次"] += 1
        elif count <= 5:
            buy_dist["4-5次"] += 1
        elif count <= 10:
            buy_dist["6-10次"] += 1
        else:
            buy_dist["10次以上"] += 1

    buy_dist_list = [
        {"range": "1次", "users": buy_dist.get("1次", 0)},
        {"range": "2-3次", "users": buy_dist.get("2-3次", 0)},
        {"range": "4-5次", "users": buy_dist.get("4-5次", 0)},
        {"range": "6-10次", "users": buy_dist.get("6-10次", 0)},
        {"range": "10次以上", "users": buy_dist.get("10次以上", 0)},
    ]

    print(f"  购买用户数: {total_buyers}")
    print(f"  跨日复购用户: {repurchase_users} ({repurchase_rate}%)")
    print(f"  多次购买用户: {multi_buy_users} ({multi_buy_rate}%)")

    return {
        "total_buyers": total_buyers,
        "repurchase_users": repurchase_users,
        "repurchase_rate": repurchase_rate,
        "multi_buy_users": multi_buy_users,
        "multi_buy_rate": multi_buy_rate,
        "buy_dist": buy_dist_list,
    }


def analyze_category(records):
    """品类差异分析。"""
    print("\n>>> 步骤 6: 品类差异分析")

    # 每个品类的各行为计数
    cat_behavior = defaultdict(lambda: Counter())
    for r in records:
        cat_behavior[r["category_id"]][r["behavior_type"]] += 1

    # 按购买量排序 TOP10
    cat_buy = [(cat, bc["buy"], bc) for cat, bc in cat_behavior.items()]
    cat_buy.sort(key=lambda x: x[1], reverse=True)

    top10 = []
    for cat, buy_count, bc in cat_buy[:10]:
        total = sum(bc.values())
        top10.append({
            "category_id": cat,
            "pv": bc.get("pv", 0),
            "fav": bc.get("fav", 0),
            "cart": bc.get("cart", 0),
            "buy": bc.get("buy", 0),
            "total": total,
            "buy_rate": round(buy_count * 100 / bc.get("pv", 1), 2),
        })

    # 按浏览量排序 TOP10
    cat_pv = [(cat, bc["pv"], bc) for cat, bc in cat_behavior.items()]
    cat_pv.sort(key=lambda x: x[1], reverse=True)

    top10_pv = []
    for cat, pv_count, bc in cat_pv[:10]:
        top10_pv.append({
            "category_id": cat,
            "pv": pv_count,
            "buy": bc.get("buy", 0),
            "buy_rate": round(bc.get("buy", 0) * 100 / pv_count, 2) if pv_count else 0,
        })

    # 品类总数
    total_categories = len(cat_behavior)

    print(f"  品类总数: {total_categories}")
    print(f"  TOP3 热销品类（按购买）:")
    for c in top10[:3]:
        print(f"    品类 {c['category_id']}: 购买 {c['buy']} 次, 浏览 {c['pv']} 次, 转化率 {c['buy_rate']}%")

    return {
        "total_categories": total_categories,
        "top10_by_buy": top10,
        "top10_by_pv": top10_pv,
    }


def analyze_hourly_pattern(records):
    """用户活跃时段分析。"""
    print("\n>>> 步骤 7: 用户活跃时段分析")

    hourly_behavior = defaultdict(lambda: Counter())
    for r in records:
        hourly_behavior[r["hour"]][r["behavior_type"]] += 1

    hourly_data = []
    for h in range(24):
        bc = hourly_behavior.get(h, Counter())
        hourly_data.append({
            "hour": h,
            "pv": bc.get("pv", 0),
            "fav": bc.get("fav", 0),
            "cart": bc.get("cart", 0),
            "buy": bc.get("buy", 0),
        })

    # 找出高峰时段
    peak_pv_hour = max(range(24), key=lambda h: hourly_behavior.get(h, Counter()).get("pv", 0))
    peak_buy_hour = max(range(24), key=lambda h: hourly_behavior.get(h, Counter()).get("buy", 0))

    print(f"  浏览高峰时段: {peak_pv_hour}:00")
    print(f"  购买高峰时段: {peak_buy_hour}:00")

    return {
        "hourly": hourly_data,
        "peak_pv_hour": peak_pv_hour,
        "peak_buy_hour": peak_buy_hour,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. 加载与清洗
    records, dropped = load_and_clean(DATA_FILE)

    # 2. PV/UV 趋势
    pv_uv = analyze_pv_uv(records)

    # 3. 漏斗分析
    funnel = analyze_funnel(records)

    # 4. RFM 分群
    rfm = analyze_rfm(records)

    # 5. 复购率
    repurchase = analyze_repurchase(records)

    # 6. 品类差异
    category = analyze_category(records)

    # 7. 活跃时段
    hourly = analyze_hourly_pattern(records)

    # 汇总输出
    result = {
        "meta": {
            "data_source": "天池 UserBehavior 数据集（采样）",
            "time_range": "2017-11-25 ~ 2017-12-03",
            "total_records": len(records),
            "clean_dropped": dropped,
        },
        "pv_uv": pv_uv,
        "funnel": funnel,
        "rfm": rfm,
        "repurchase": repurchase,
        "category": category,
        "hourly_pattern": hourly,
    }

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"分析完成！结果已保存至: {RESULT_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
