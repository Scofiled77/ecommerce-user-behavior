# -*- coding: utf-8 -*-
"""生成基于天池 UserBehavior 数据集特征的采样数据。

天池 UserBehavior 原始数据集（淘宝用户行为 2017.11.25-12.3）约 1 亿条，
需登录天池下载。本脚本基于该数据集公开统计特征生成 50 万条采样数据，
用于完整复现 PV/UV 趋势、转化漏斗、RFM 分群、复购率、品类差异等分析。

字段格式与原始数据集完全一致：
    user_id, item_id, category_id, behavior_type, timestamp

behavior_type 取值：pv（浏览）/ fav（收藏）/ cart（加购物车）/ buy（购买）
"""
import csv
import random
import time
from datetime import datetime, timedelta
from collections import defaultdict
import os

# ============ 参数配置 ============
NUM_USERS = 5000          # 用户数
NUM_ITEMS = 50000         # 商品数
NUM_CATEGORIES = 958      # 品类数（天池原始约 958 个）
TOTAL_RECORDS = 500000    # 总行为记录数
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "user_behavior.csv")

# 时间范围：2017-11-25 00:00:00 ~ 2017-12-03 23:59:59
START_TS = int(datetime(2017, 11, 25, 0, 0, 0).timestamp())
END_TS = int(datetime(2017, 12, 3, 23, 59, 59).timestamp())

# 行为类型比例（基于天池 UserBehavior 公开统计）
BEHAVIOR_WEIGHTS = [("pv", 89.0), ("cart", 5.5), ("fav", 3.7), ("buy", 1.8)]

# 每小时活跃度权重（24小时，反映淘宝用户行为双高峰：12点午间 + 21点晚间）
HOURLY_WEIGHTS = [
    1.2, 0.8, 0.5, 0.3, 0.2, 0.3,   # 0-5点（凌晨低谷）
    0.8, 2.0, 4.0, 5.5, 6.5, 7.8,   # 6-11点（上升）
    8.5, 7.0, 6.0, 5.8, 6.2, 6.8,   # 12-17点（午间高峰后回落）
    7.5, 8.2, 9.0, 9.5, 8.8, 6.5,   # 18-23点（晚间高峰21点）
]

# 9天的日期权重（11.25周六, 11.26周日, 11.27-12.1工作日, 12.2周六, 12.3周日）
# 周末活跃度略高
DAY_WEIGHTS = [1.15, 1.15, 0.95, 0.92, 0.92, 0.92, 0.95, 1.10, 1.10]


def weighted_choice(items, weights):
    """加权随机选择。"""
    total = sum(weights)
    r = random.random() * total
    upto = 0
    for item, w in zip(items, weights):
        if upto + w >= r:
            return item
        upto += w
    return items[-1]


def generate_user_activity_profile(num_users):
    """为每个用户生成活跃度权重（幂律分布：少数用户极活跃）。"""
    profiles = []
    for i in range(num_users):
        # 幂律分布：base + Pareto tail
        base = random.random() * 0.3
        if random.random() < 0.1:  # 10% 的用户是高活跃用户
            base += random.random() * 3.0 + 1.0
        elif random.random() < 0.3:  # 30% 是中等活跃
            base += random.random() * 0.8
        profiles.append(max(base, 0.05))
    return profiles


def generate_category_popularity(num_categories):
    """品类热度（长尾分布：少数品类极热门）。"""
    pop = []
    for i in range(num_categories):
        # 排名越靠前热度越高（Zipf 分布近似）
        base = 1.0 / (i + 1) ** 0.7
        base *= (1 + random.random() * 0.5)
        pop.append(max(base, 0.01))
    return pop


def generate_timestamp():
    """生成符合时间分布的 timestamp。"""
    # 先选日期
    day_idx = weighted_choice(range(9), DAY_WEIGHTS)
    # 再选小时
    hour = weighted_choice(range(24), HOURLY_WEIGHTS)
    # 再选分钟和秒
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    day_offset = day_idx * 86400
    hour_offset = hour * 3600 + minute * 60 + second
    ts = START_TS + day_offset + hour_offset

    # 边界保护
    if ts > END_TS:
        ts = END_TS
    return ts


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    random.seed(42)  # 可复现

    print("=" * 60)
    print("天池 UserBehavior 采样数据生成")
    print(f"用户数: {NUM_USERS}  商品数: {NUM_ITEMS}  品类数: {NUM_CATEGORIES}")
    print(f"目标记录数: {TOTAL_RECORDS}")
    print(f"时间范围: 2017-11-25 ~ 2017-12-03")
    print("=" * 60)

    # 生成用户活跃度
    user_profiles = generate_user_activity_profile(NUM_USERS)
    # 归一化为整数权重
    total_weight = sum(user_profiles)
    user_weights = [p / total_weight for p in user_profiles]

    # 生成品类热度
    cat_pop = generate_category_popularity(NUM_CATEGORIES)
    cat_total = sum(cat_pop)
    cat_weights = [p / cat_total for p in cat_pop]

    # 为每个商品分配品类（热门品类有更多商品）
    item_category = {}
    for item_id in range(1, NUM_ITEMS + 1):
        cat_id = weighted_choice(range(NUM_CATEGORIES), cat_weights) + 1
        item_category[item_id] = cat_id

    # 行为类型
    behaviors = [b for b, _ in BEHAVIOR_WEIGHTS]
    b_weights = [w for _, w in BEHAVIOR_WEIGHTS]

    # 生成记录
    print(f"\n正在生成 {TOTAL_RECORDS} 条记录...")

    # 预计算用户采样表（用累计分布加速）
    user_cumulative = []
    cum = 0
    for w in user_weights:
        cum += w
        user_cumulative.append(cum)

    # 预计算行为采样
    behavior_cumulative = []
    cum = 0
    for b, w in BEHAVIOR_WEIGHTS:
        cum += w
        behavior_cumulative.append((cum, b))

    records = []
    batch_size = 50000
    written = 0

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "item_id", "category_id", "behavior_type", "timestamp"])

        for i in range(TOTAL_RECORDS):
            # 按活跃度选用户
            r = random.random()
            user_idx = 0
            lo, hi = 0, NUM_USERS - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if user_cumulative[mid] < r:
                    lo = mid + 1
                else:
                    hi = mid
            user_id = lo + 1

            # 随机选商品
            item_id = random.randint(1, NUM_ITEMS)
            category_id = item_category[item_id]

            # 选行为类型（r2 映射到 0~100 与权重对齐）
            r2 = random.random() * 100
            behavior_type = "pv"
            for cum_val, btype in behavior_cumulative:
                if r2 <= cum_val:
                    behavior_type = btype
                    break

            # 生成时间戳
            ts = generate_timestamp()

            records.append([user_id, item_id, category_id, behavior_type, ts])

            if len(records) >= batch_size:
                writer.writerows(records)
                written += len(records)
                records.clear()
                if written % 100000 == 0:
                    print(f"  已生成 {written}/{TOTAL_RECORDS} ({written*100//TOTAL_RECORDS}%)")

        if records:
            writer.writerows(records)
            written += len(records)
            records.clear()

    file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\n完成！共写入 {written} 条记录")
    print(f"文件大小: {file_size:.1f} MB")
    print(f"输出路径: {OUTPUT_FILE}")

    # 输出统计摘要
    print("\n--- 数据摘要 ---")
    print(f"行为类型分布（目标 vs 实际）:")
    # 重新读取统计
    type_count = defaultdict(int)
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            type_count[row["behavior_type"]] += 1
    total = sum(type_count.values())
    for b, w in BEHAVIOR_WEIGHTS:
        actual = type_count.get(b, 0)
        pct = actual * 100 / total if total else 0
        print(f"  {b:4s}: 目标 {w:5.1f}%  实际 {pct:5.1f}%  ({actual} 条)")


if __name__ == "__main__":
    main()
