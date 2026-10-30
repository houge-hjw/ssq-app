import requests
import random
import itertools
import json
import os
import sys


def resource_path(rel):
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)


CACHE_FILE = resource_path("ssq_cache.json")


RED_FESTIVE = "#C1272D"
RED_DARK = "#8B0000"
RED_LIGHT = "#E63946"
GOLD = "#FFD700"
GOLD_DARK = "#DAA520"
GOLD_LIGHT = "#FFE4B5"
CREAM = "#FFF8E7"
BLUE_BALL = "#1E5AA8"


def fetch_lottery_data(count=50):
    api_url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
    params = {"name": "ssq", "issueCount": str(count)}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.cwl.gov.cn/ygkj/wqkjgg/ssq/",
        "Accept": "application/json, text/plain, */*",
    }
    try:
        resp = requests.get(api_url, params=params, headers=headers, timeout=15)
        resp.encoding = "utf-8"
        data = resp.json()
        if data.get("state") != 0:
            raise Exception(data.get("message", "未知错误"))
        results = []
        for item in data.get("result", []):
            red_balls = sorted(int(x) for x in item["red"].split(","))
            blue_ball = int(item["blue"])
            results.append({
                "issue": item["code"],
                "date": item["date"],
                "red": red_balls,
                "blue": blue_ball,
            })
        if results:
            save_cache(results)
        return results
    except Exception as e:
        print(f"网络请求失败: {e}")
        cached = load_cache()
        if cached:
            print("使用本地缓存数据")
            return cached[:count]
        return []


def save_cache(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def analyze_frequency(data):
    red_freq = {i: 0 for i in range(1, 34)}
    blue_freq = {i: 0 for i in range(1, 17)}
    for item in data:
        for r in item["red"]:
            red_freq[r] += 1
        blue_freq[item["blue"]] += 1
    return red_freq, blue_freq


def analyze_missing(data):
    red_missing = {i: len(data) for i in range(1, 34)}
    blue_missing = {i: len(data) for i in range(1, 17)}
    for idx, item in enumerate(reversed(data)):
        for r in item["red"]:
            if red_missing[r] == len(data):
                red_missing[r] = idx
        if blue_missing[item["blue"]] == len(data):
            blue_missing[item["blue"]] = idx
    return red_missing, blue_missing


def analyze_hot_cold(red_freq, blue_freq, top_n=10):
    red_sorted = sorted(red_freq.items(), key=lambda x: x[1], reverse=True)
    blue_sorted = sorted(blue_freq.items(), key=lambda x: x[1], reverse=True)
    hot_red = [x[0] for x in red_sorted[:top_n]]
    cold_red = [x[0] for x in red_sorted[-top_n:]]
    hot_blue = [x[0] for x in blue_sorted[:5]]
    cold_blue = [x[0] for x in blue_sorted[-5:]]
    return hot_red, cold_red, hot_blue, cold_blue


def weighted_sample(probs, k):
    nums = [n for n, _ in probs]
    weights = [w for _, w in probs]
    result = []
    remaining_nums = nums[:]
    remaining_weights = weights[:]
    for _ in range(k):
        total = sum(remaining_weights)
        r = random.random() * total
        cumulative = 0
        chosen_idx = 0
        for i, w in enumerate(remaining_weights):
            cumulative += w
            if r <= cumulative:
                chosen_idx = i
                break
        result.append(remaining_nums[chosen_idx])
        remaining_nums.pop(chosen_idx)
        remaining_weights.pop(chosen_idx)
    return result


def generate_prediction(data, num_sets=5):
    if not data:
        return []
    red_freq, blue_freq = analyze_frequency(data)
    red_missing, blue_missing = analyze_missing(data)
    hot_red, cold_red, hot_blue, cold_blue = analyze_hot_cold(red_freq, blue_freq)

    red_weighted = []
    for num in range(1, 34):
        freq_score = red_freq[num] * 2
        missing_score = max(0, max(red_missing.values()) - red_missing[num])
        hot_score = 3 if num in hot_red else (1 if num in cold_red else 2)
        score = freq_score + missing_score + hot_score
        red_weighted.append((num, score))

    blue_weighted = []
    for num in range(1, 17):
        freq_score = blue_freq[num] * 2
        missing_score = max(0, max(blue_missing.values()) - blue_missing[num])
        hot_score = 3 if num in hot_blue else (1 if num in cold_blue else 2)
        score = freq_score + missing_score + hot_score
        blue_weighted.append((num, score))

    total_red = sum(w for _, w in red_weighted)
    total_blue = sum(w for _, w in blue_weighted)
    red_probs = [(n, w / total_red) for n, w in red_weighted]
    blue_probs = [(n, w / total_blue) for n, w in blue_weighted]

    predictions = []
    for _ in range(num_sets):
        red_balls = weighted_sample(red_probs, 6)
        blue_ball = weighted_sample(blue_probs, 1)[0]
        predictions.append({"red": sorted(red_balls), "blue": blue_ball})
    return predictions


def calc_ac_value(red_balls):
    diffs = set()
    for a, b in itertools.combinations(red_balls, 2):
        diffs.add(abs(a - b))
    return len(diffs) - (len(red_balls) - 1)


def is_valid_red(red_balls):
    if len(set(red_balls)) != 6:
        return False
    red_balls = sorted(red_balls)
    s = sum(red_balls)
    if s < 70 or s > 140:
        return False
    low = sum(1 for x in red_balls if x <= 16)
    if low < 2 or low > 4:
        return False
    odd = sum(1 for x in red_balls if x % 2 == 1)
    if odd < 2 or odd > 4:
        return False
    ac = calc_ac_value(red_balls)
    if ac < 6:
        return False
    zones = [0, 0, 0]
    for x in red_balls:
        if x <= 11:
            zones[0] = 1
        elif x <= 22:
            zones[1] = 1
        else:
            zones[2] = 1
    if sum(zones) < 2:
        return False
    return True


def generate_rollover_numbers(data):
    if not data:
        return [], []
    red_freq, blue_freq = analyze_frequency(data)
    red_missing, blue_missing = analyze_missing(data)
    hot_red, cold_red, hot_blue, cold_blue = analyze_hot_cold(red_freq, blue_freq, 12)

    red_scores = {}
    for num in range(1, 34):
        freq_score = red_freq[num] * 3
        missing_score = (max(red_missing.values()) - red_missing[num]) * 1.5
        hot_score = 5 if num in hot_red else (1 if num in cold_red else 3)
        zone_score = 2
        red_scores[num] = freq_score + missing_score + hot_score + zone_score

    blue_scores = {}
    for num in range(1, 17):
        freq_score = blue_freq[num] * 3
        missing_score = (max(blue_missing.values()) - blue_missing[num]) * 1.5
        hot_score = 5 if num in hot_blue else (1 if num in cold_blue else 3)
        blue_scores[num] = freq_score + missing_score + hot_score

    red_sorted = sorted(red_scores.items(), key=lambda x: x[1], reverse=True)
    blue_sorted = sorted(blue_scores.items(), key=lambda x: x[1], reverse=True)
    top_red = [n for n, _ in red_sorted[:16]]
    top_blue = [n for n, _ in blue_sorted[:8]]
    return top_red, top_blue


def generate_wheel(data, num_sets=10):
    top_red, top_blue = generate_rollover_numbers(data)
    if not top_red:
        return [], [], []

    red_freq, blue_freq = analyze_frequency(data)
    hot_red, _, hot_blue, _ = analyze_hot_cold(red_freq, blue_freq, 12)

    strategies = [
        ("🔥全热号策略", lambda: sorted(random.sample(hot_red if len(hot_red) >= 6 else top_red, 6))),
        ("❄冷热均衡策略", lambda: _pick_hot_cold(hot_red, top_red, 3, 3)),
        ("📈遗漏回补策略", lambda: _pick_missing_balance(data, top_red)),
        ("🎲覆盖广撒策略", lambda: _pick_wide_coverage(top_red)),
        ("⚖和值平衡策略", lambda: _pick_balanced_sum(top_red)),
        ("🌈三区分布策略", lambda: _pick_three_zone(top_red)),
        ("🎯AC最优策略", lambda: _pick_high_ac(top_red)),
        ("🌙奇偶黄金策略", lambda: _pick_odd_even(top_red)),
        ("🔵蓝球锁定策略", lambda: sorted(random.sample(top_red, 6))),
        ("💎钻石矩阵策略", lambda: _pick_diamond(top_red)),
    ]

    selected_blue = _select_weighted_blue(hot_blue, top_blue)

    results = []
    used_reds = set()
    for i in range(min(num_sets, len(strategies))):
        name, gen = strategies[i]
        for _ in range(100):
            try:
                red = gen()
                if is_valid_red(red):
                    red_key = tuple(sorted(red))
                    if red_key not in used_reds:
                        used_reds.add(red_key)
                        blue = _pick_blue_for_set(i, hot_blue, top_blue, selected_blue)
                        results.append({
                            "red": sorted(red),
                            "blue": blue,
                            "strategy": name,
                        })
                        break
            except Exception:
                continue
        if len(results) <= i:
            results.append({
                "red": sorted(random.sample(top_red, 6)),
                "blue": selected_blue[i % len(selected_blue)] if selected_blue else random.randint(1, 16),
                "strategy": name,
            })

    return results, top_red, top_blue


def _pick_hot_cold(hot, pool, hot_count, cold_count):
    hot_available = [x for x in hot if x in pool]
    cold_available = [x for x in pool if x not in hot]
    h = random.sample(hot_available, min(hot_count, len(hot_available)))
    c = random.sample(cold_available, min(cold_count, len(cold_available)))
    remaining = [x for x in pool if x not in h and x not in c]
    rest = random.sample(remaining, 6 - len(h) - len(c))
    return sorted(h + c + rest)


def _pick_missing_balance(data, pool):
    red_missing, _ = analyze_missing(data)
    scored = [(n, red_missing.get(n, 0)) for n in pool]
    scored.sort(key=lambda x: x[1], reverse=True)
    high_miss = [n for n, _ in scored[:6]]
    low_miss = [n for n, _ in scored[-6:]]
    mid = [n for n, _ in scored[6:-6]]
    picks = random.sample(high_miss, 2) + random.sample(mid, 2) + random.sample(low_miss, 2)
    return sorted(picks)


def _pick_wide_coverage(pool):
    zones = [[], [], []]
    for x in pool:
        if x <= 11:
            zones[0].append(x)
        elif x <= 22:
            zones[1].append(x)
        else:
            zones[2].append(x)
    picks = random.sample(zones[0], 2) + random.sample(zones[1], 2) + random.sample(zones[2], 2)
    return sorted(picks)


def _pick_balanced_sum(pool):
    for _ in range(50):
        red = sorted(random.sample(pool, 6))
        s = sum(red)
        if 90 <= s <= 120:
            return red
    return sorted(random.sample(pool, 6))


def _pick_three_zone(pool):
    zones = [[], [], []]
    for x in pool:
        if x <= 11:
            zones[0].append(x)
        elif x <= 22:
            zones[1].append(x)
        else:
            zones[2].append(x)
    zone_pick = [2, 2, 2] if random.random() < 0.6 else random.choice([[3, 2, 1], [1, 2, 3], [2, 3, 1], [1, 3, 2], [3, 1, 2]])
    picks = []
    for z, c in zip(zones, zone_pick):
        if len(z) >= c:
            picks.extend(random.sample(z, c))
        else:
            picks.extend(z)
    while len(picks) < 6:
        extra = random.choice([x for x in pool if x not in picks])
        picks.append(extra)
    return sorted(picks[:6])


def _pick_high_ac(pool):
    best = None
    best_ac = 0
    for _ in range(100):
        red = sorted(random.sample(pool, 6))
        ac = calc_ac_value(red)
        if ac > best_ac and is_valid_red(red):
            best_ac = ac
            best = red
    return best if best else sorted(random.sample(pool, 6))


def _pick_odd_even(pool):
    odds = [x for x in pool if x % 2 == 1]
    evens = [x for x in pool if x % 2 == 0]
    r = random.random()
    if r < 0.3:
        return sorted(random.sample(odds, 3) + random.sample(evens, 3))
    elif r < 0.6:
        return sorted(random.sample(odds, 4) + random.sample(evens, 2))
    else:
        return sorted(random.sample(odds, 2) + random.sample(evens, 4))


def _pick_diamond(pool):
    center = sorted(random.sample(pool, 1))[0]
    lower = [x for x in pool if x < center]
    upper = [x for x in pool if x > center]
    if len(lower) >= 2 and len(upper) >= 3:
        return sorted(random.sample(lower, 2) + [center] + random.sample(upper, 3))
    return sorted(random.sample(pool, 6))


def _select_weighted_blue(hot_blue, top_blue):
    all_blues = list(set(hot_blue + top_blue))
    all_blues = all_blues[:6]
    return all_blues


def _pick_blue_for_set(idx, hot_blue, top_blue, selected):
    if idx < len(selected):
        return selected[idx]
    pool = list(set(hot_blue + top_blue))
    return random.choice(pool) if pool else random.randint(1, 16)


def calc_next_issue(current_issue):
    try:
        year = int(current_issue[:4])
        num = int(current_issue[4:])
        num += 1
        if num > 154:
            year += 1
            num = 1
        return f"{year}{num:03d}"
    except Exception:
        return ""


def calc_next_draw_date(last_date_str):
    try:
        import re
        import datetime
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", last_date_str)
        if not m:
            return ""
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        last = datetime.date(y, mo, d)
        draw_weekdays = {1, 3, 6}
        candidate = last + datetime.timedelta(days=1)
        while candidate.weekday() not in draw_weekdays:
            candidate += datetime.timedelta(days=1)
        weekday_cn = ["一", "二", "三", "四", "五", "六", "日"][candidate.weekday()]
        return f"{candidate.strftime('%Y-%m-%d')} (周{weekday_cn}) 21:15"
    except Exception:
        return ""
