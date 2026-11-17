#!/usr/bin/env python3
"""Fill data-dependent numbers in the Markdown docs from the published data.

Docs mark every value that changes with a new analytics import:

    inline:  <!--v:base_cycle-->212<!--/-->
    block:   <!--b:fc_nodes_en-->
             ...generated table or code block...
             <!--/b-->

The text between the markers is overwritten from scripts/params.py, the
latest snapshots and docs/iphone17-forecast.json. Unmarked text (history in
corrections.md, dated "Update (...)" notes) is never touched.

    python3 scripts/sync_docs.py          # rewrite docs in place
    python3 scripts/sync_docs.py --check  # exit 1 if any doc is out of date

Run scripts/forecast.py first; update.sh does both.
"""
import csv
import glob
import json
import math
import os
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import RATED, ROOT, derive, non_stale, snapshots  # noqa: E402

INLINE = re.compile(r"<!--v:([a-z_]+)-->(.*?)<!--/-->", re.S)
BLOCK = re.compile(r"<!--b:([a-z_]+)-->\n.*?\n<!--/b-->", re.S)
LOCAL_TZ = timezone(timedelta(hours=8))   # device timezone (+0800)

EN_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen",
            "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
            "nineteen", "twenty"]
ZH_DIGITS = "零一二三四五六七八九"


def rnd(x, nd=0):
    """Round half up (format() rounds 3472.5 to 3472)."""
    q = Decimal(1).scaleb(-nd)
    return str(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def en_word(n):
    return EN_WORDS[n] if n < len(EN_WORDS) else str(n)


def zh_word(n):
    if n < 10:
        return ZH_DIGITS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return (ZH_DIGITS[tens] if tens > 1 else "") + "十" + \
            (ZH_DIGITS[ones] if ones else "")
    return str(n)


def sessions_csv():
    with open(os.path.join(ROOT, "devices/iphone-01/charging-sessions.csv"),
              newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def timeline():
    with open(os.path.join(ROOT, "devices/iphone-01/analytics-timeline.csv"),
              newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def values():
    P = derive()
    fc = json.load(open(os.path.join(ROOT, "docs/iphone17-forecast.json"),
                        encoding="utf-8"))
    snaps = snapshots()
    ns = non_stale(snaps)
    latest = snaps[-1]
    base = fc["base"]
    nodes = {n["cycle"]: n for n in fc["nodes"]}
    rate = P["diary"]["cycles_per_day"]
    cycles = [s["cycle_count"] for s in snaps]
    raw = [s["apple_raw_max_capacity_mah"] for s in snaps]
    ncc = [s["nominal_charge_capacity_mah"] for s in snaps]
    k = fc["at_1000_cycles"]
    gauge = P["rates"]["gauge_regression"]
    last_gauge = datetime.fromisoformat(
        latest["gauge_update_time_utc"].replace("Z", "+00:00"))
    d500 = date.fromisoformat(base["date"]) + \
        timedelta(days=(500 - base["cycle"]) / rate)
    sens = [c for c in fc["sensitivity_to_usage_rate"]
            if "withdrawn" not in c["case"] and "old" not in c["case"]]
    n = len(snaps)
    raw_range = max(raw) - min(raw)

    v = {
        "base_date": base["date"],
        "base_md": base["date"][5:],
        "base_cycle": str(base["cycle"]),
        "base_ncc": str(base["ncc_mah"]),
        "base_health_two": f"{base['health_pct']:.2f}",
        "base_health": f"{base['health_pct']:.3f}",
        "apple": str(base["apple_max_capacity_percent"]),
        "vac": str(latest["vac_voltage_limit_mv"]),
        "rate": f"{rate:.2f}",
        "first_md": snaps[0]["date"][5:],
        "snap_n": str(n),
        "snap_word": en_word(n),
        "snap_word_cap": en_word(n).capitalize(),
        "snap_zh": zh_word(n),
        "further_n": str(n - 1),
        "further_word": en_word(n - 1),
        "further_word_cap": en_word(n - 1).capitalize(),
        "further_zh": zh_word(n - 1),
        "cycle_range": f"{cycles[0]}–{cycles[-1]}",
        "further_range": f"{cycles[1]}–{cycles[-1]}",
        "cycle_list": "/".join(map(str, cycles)),
        "cycle_last": str(cycles[-1]),
        "ncc_range": f"{min(ncc)}–{max(ncc)}",
        "raw_list": " → ".join(map(str, raw)),
        "raw_range": str(raw_range),
        "raw_range_pp": f"{raw_range / RATED * 100:.3f}",
        "raw_ratio": str(raw_range),          # vs the 1 mAh NCC jitter step
        "maxsoc_list": "`" + ", ".join(str(s["daily_max_soc_pct"]) for s in snaps) + "`",
        "maxsoc_max": str(max(s["daily_max_soc_pct"] for s in snaps)),
        "gauge_last_local": last_gauge.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M"),
        "gauge_n": str(len(ns)),
        "gauge_rate": f"{gauge}",
        "gauge_span": f"{P['rates']['gauge_span_days']}",
        "gauge_cycles": f"{ns[0]['cycle_count']}→{ns[-1]['cycle_count']}",
        "gauge_agree": str(math.ceil(abs(gauge / rate - 1) * 100)),
        "date_next": nodes[250]["date"],
        "date_after": nodes[300]["date"],
        "date_kilo": nodes[1000]["date"],
        # Spread of the forecast dates over the measured usage windows. The
        # withdrawn 57-day regression is excluded: it is kept as a sensitivity
        # case, not as a live usage estimate.
        "date_next_lo": min(c["date_250"] for c in sens),
        "date_next_hi": max(c["date_250"] for c in sens),
        "date_kilo_lo": min(c["date_1000"] for c in sens),
        "date_kilo_hi": max(c["date_1000"] for c in sens),
        "date_half": d500.strftime("%Y-%m"),
        "ncc_kilo": rnd(k['ncc_mah']),
        "chem_kilo": rnd(k['chemical_only_mah']),
        "lockin_kilo": rnd(k['reversible_lockin_mah']),
        "wear_kilo": rnd(k['total_wear_mah']),
        "wear_kilo_pct": rnd(k['total_wear_mah'] / RATED * 100, 1),
    }
    # Usage/charging figures quoted in prose. They move whenever the diary is
    # re-parsed, so they are marked too instead of being edited by hand.
    ss = json.load(open(os.path.join(ROOT, "docs/charging-summary.json"),
                        encoding="utf-8"))
    sess = sessions_csv()
    zero = sum(1 for r in sess if int(r["charged_pct"]) == 0)
    anom = sum(1 for r in sess if r["anomaly"])

    # Distributions quoted in findings.md §3. Computed here rather than read
    # from charging-summary.json, which only carries the aggregates.
    rate = [float(r["rate_pct_per_min"]) for r in sess]
    ends = [int(r["soc_end"]) for r in sess]
    total = len(sess)

    def share(pred):
        return f"{sum(1 for x in rate if pred(x)) / total * 100:.1f}"

    top = Counter(ends).most_common(2)
    ge80 = sorted(e for e in ends if e >= 80)
    longest = max(sess, key=lambda r: int(r["duration_sec"]))
    fastest = max(sess, key=lambda r: float(r["rate_pct_per_min"]))
    v.update({
        "sessions": str(ss["sessions"]),
        "span_days": str(ss["span_days"]),
        "efc": f"{ss['equivalent_full_cycles']:.2f}",
        "mah_day": str(round(P["diary"]["mah_per_day"])),
        "rate_mean": f"{ss['avg_rate_pct_per_min']:.2f}",
        "rate_mean_clean": f"{ss['avg_rate_excl_anomaly']:.2f}",
        "rate_mean_clean_1": f"{ss['avg_rate_excl_anomaly']:.1f}",
        "rate_mean_3": f"{ss['avg_rate_pct_per_min']:.3f}",
        "rate_clean_3": f"{ss['avg_rate_excl_anomaly']:.3f}",
        "clean_sessions": str(ss["clean_sessions"]),
        "zero_sessions": str(zero),
        "zero_pct": f"{zero / ss['sessions'] * 100:.1f}",
        "dropped_sessions": str(ss["soc_dropped_sessions"]),
        "anom_sessions": str(anom),
        "anom_pct": f"{anom / ss['sessions'] * 100:.1f}",
        "dur_hours": f"{ss['total_duration_hours']:.1f}",
        "dur_hours_2": f"{ss['total_duration_hours']:.2f}",
        "charged_sum": str(ss["total_charged_pct"]),
        "avg_dur": f"{ss['avg_duration_min']:.2f}",
        "avg_charge": f"{ss['avg_charged_pct']:.2f}",
        "sess_day": f"{ss['avg_sessions_per_day']:.2f}",
        "sess_day_min": str(ss["min_sessions_one_day"]),
        "sess_day_max": str(ss["max_sessions_one_day"]),
        "ge80_n": str(len(ge80)),
        "ge80_list": "/".join(map(str, ge80)),
        "end_mid_n": str(sum(1 for e in ends if 65 <= e <= 81)),
        "top_a": str(top[0][0]),
        "top_a_n": str(top[0][1]),
        "top_b": str(top[1][0]),
        "top_b_n": str(top[1][1]),
        "speed_gt2": share(lambda x: x > 2.0),
        "speed_15_2": share(lambda x: 1.5 < x <= 2.0),
        "speed_1_15": share(lambda x: 1.0 < x <= 1.5),
        "speed_0_1": share(lambda x: 0 < x <= 1.0),
        "speed_le0": share(lambda x: x <= 0),
        "longest_h": f"{int(longest['duration_sec']) / 3600:.2f}",
        "longest_pct": longest["charged_pct"],
        "fastest": f"{float(fastest['rate_pct_per_min']):.2f}",
        "fastest_lo": fastest["soc_start"],
        "fastest_hi": fastest["soc_end"],
    })
    return v, blocks(P, fc)


def sens_label(case):
    """(en, zh) label for a sensitivity row.

    The case strings carry the diary length ("full 76-day diary (primary)"),
    so they are matched by shape: a hard-coded key would raise KeyError the
    first time the diary is re-parsed and the span changes.
    """
    if case.startswith("recent ") and case.endswith(" days"):
        d = case.split()[1]
        return case, f"最近 {d} 天"
    if case.startswith("independent gauge"):
        return "independent gauge snapshots (regression)", "独立电量计快照（回归）"
    if case.startswith("full ") and "diary" in case:
        d = case.split()[1].split("-")[0]
        return case, f"完整 {d} 天充电日志（主值）"
    if "export regression" in case:
        d = case.split("-")[0]
        return f"old {d}-day regression (withdrawn)", f"旧的 {d} 天回归（已撤回）"
    return case, case


def blocks(P, fc):
    base = fc["base"]
    rate = P["diary"]["cycles_per_day"]
    out = {}

    out["fc_model"] = "\n".join([
        "```",
        f"health(cycle) = {base['health_pct']:.3f}",
        f"              − {P['plateau_pp_per_day']} × days                 (plateau / chemical ageing)",
        f"              − {P['step_pp_per_node']}  × (# of future nodes)   (reversible lock-in)",
        f"chemical_only(cycle) = {base['health_pct']:.3f} − {P['plateau_pp_per_day']} × days",
        f"days = (cycle − {base['cycle']}) / {rate:.2f}                 (CURRENT usage)",
        f"mAh  = pct / 100 × {RATED}                     (fixed nameplate)",
        "```",
    ])

    for lang, head, now in (
        ("en", "| Date | Cycles | Voltage | NCC health | **NCC mAh** | Lock-in mAh | Chemical-only mAh |", " (now)"),
        ("zh", "| 日期 | 循环次数 | 电压 | NCC 健康度 | **NCC mAh** | 锁容 mAh | 仅化学老化 mAh |", "（当前）"),
    ):
        rows = [head,
                "|------|--------|---------|-----------|-------------|-------------|-------------------|",
                f"| {base['date']}{now} | {base['cycle']} | "
                f"{P['base']['vac_voltage_limit_mv']} mV | **{base['health_pct']:.3f}%** | "
                f"**{base['ncc_mah']}** | 0 | {base['ncc_mah']} |"]
        for i, nd in enumerate(fc["nodes"]):
            chem = rnd(nd['chemical_only_mah'])
            if i == len(fc["nodes"]) - 1:
                chem = f"**{chem}**"
            rows.append(f"| **{nd['date']}** | {nd['cycle']} | {nd['vac_voltage_limit_mv']} mV | "
                        f"**{nd['ncc_health_pct']:.3f}%** | **{rnd(nd['ncc_mah'])}** | "
                        f"{rnd(nd['node_lockin_mah'])} | {chem} |")
        out[f"fc_nodes_{lang}"] = "\n".join(rows)

    for lang, head in (
        ("en", "| Usage window | cycles/day | mAh/day | 250 node | 1000 node | NCC mAh @1000 |"),
        ("zh", "| 使用窗口 | cycles/day | mAh/day | 250 节点 | 1000 节点 | 1000 时 NCC mAh |"),
    ):
        rows = [head, "|--------------|-----------|---------|----------|-----------|---------------|"]
        for r in fc["sensitivity_to_usage_rate"]:
            en, zh = sens_label(r["case"])
            primary = "primary" in r["case"]
            cells = [en if lang == "en" else zh,
                     f"{r['cycles_per_day']:.2f}" if primary else f"{r['cycles_per_day']}",
                     f"{r['mah_per_day']}", r["date_250"], r["date_1000"],
                     rnd(r['ncc_mah_at_1000'])]
            if primary:
                cells = [f"**{c}**" for c in cells]
            rows.append("| " + " | ".join(cells) + " |")
        out[f"fc_sens_{lang}"] = "\n".join(rows)

    # Start-SOC bands, recomputed from the sessions CSV.
    sess = sessions_csv()
    bands = [(0, 20, "0–20%"), (20, 40, "20–40%"),
             (40, 60, "40–60%"), (60, 80, "60–80%")]
    for lang, head in (
        ("en", "| Start SOC | Sessions | Mean charged | Mean rate |"),
        ("zh", "| 起始 SOC | 会话数 | 平均充入 | 平均速率 |"),
    ):
        rows = [head, "|-----------|----------|--------------|-----------|"]
        for lo, hi, label in bands:
            sel = [r for r in sess if lo <= int(r["soc_start"]) < hi]
            if not sel:
                continue
            mean_charged = sum(int(r["charged_pct"]) for r in sel) / len(sel)
            mean_rate = sum(float(r["rate_pct_per_min"]) for r in sel) / len(sel)
            rows.append(f"| {label} | {len(sel)} | {mean_charged:.1f}% | {mean_rate:.2f} %/min |")
        out[f"soc_bands_{lang}"] = "\n".join(rows)

    tl = timeline()
    for lang, head, stale in (
        ("en", "| Date (file) | Gauge `UpdateTime` (UTC) | Cycles | `VacVoltageLimit` | Band | `AppleRawMaxCapacity` | NCC | Health | DailyMinSoc |", " (stale)"),
        ("zh", "| 日期（文件） | 电量计 `UpdateTime`（UTC） | 循环 | `VacVoltageLimit` | 区间 | `AppleRawMaxCapacity` | NCC | 健康度 | DailyMinSoc |", "（旧快照）"),
    ):
        rows = [head, "|-------------|--------------------------|--------|-------------------|------|------------------------|-----|--------|-------------|"]
        prev = None
        for i, r in enumerate(tl):
            g = r["gauge_update_time_utc"]
            gcell = f"{g[5:10]} {g[11:19]}" + (stale if g == prev else "")
            prev = g
            cyc = r["cycle_count"]
            if i in (0, len(tl) - 1):
                cyc = f"**{cyc}**"
            mv = int(r["vac_voltage_limit_mv"])
            band = r["node_band"].replace("-", "–") + (" ✓" if r["voltage_matches_band"] == "True" else " ✗")
            rows.append(f"| {r['date']} | {gcell} | {cyc} | {mv} mV ({mv / 1000:.2f}V) | {band} | "
                        f"{r['apple_raw_max_capacity_mah']} | {r['nominal_charge_capacity_mah']} | "
                        f"{float(r['nominal_health_pct']):.3f}% | {r['daily_min_soc_pct']} |")
        out[f"timeline_{lang}"] = "\n".join(rows)
    return out


def doc_files():
    pats = ["README*.md", "docs/*.md", "devices/*/*.md"]
    return sorted({p for pat in pats for p in glob.glob(os.path.join(ROOT, pat))})


def render(text, v, b, missing):
    def inl(m):
        if m.group(1) not in v:
            missing.add(m.group(1))
            return m.group(0)
        return f"<!--v:{m.group(1)}-->{v[m.group(1)]}<!--/-->"

    def blk(m):
        if m.group(1) not in b:
            missing.add(m.group(1))
            return m.group(0)
        return f"<!--b:{m.group(1)}-->\n\n{b[m.group(1)]}\n\n<!--/b-->"
    return BLOCK.sub(blk, INLINE.sub(inl, text))


def main():
    check = "--check" in sys.argv[1:]
    v, b = values()
    stale, missing, marks = [], set(), 0
    for path in doc_files():
        text = open(path, encoding="utf-8").read()
        marks += len(INLINE.findall(text)) + len(BLOCK.findall(text))
        new = render(text, v, b, missing)
        if new != text:
            stale.append(os.path.relpath(path, ROOT))
            if not check:
                open(path, "w", encoding="utf-8").write(new)
    if missing:
        print("unknown marker keys:", ", ".join(sorted(missing)))
        sys.exit(2)
    if check:
        if stale:
            print("docs out of date (run scripts/sync_docs.py):", ", ".join(stale))
            sys.exit(1)
        print(f"docs in sync ({marks} markers)")
    else:
        print(f"{len(stale)} docs updated ({marks} markers)")
        for p in stale:
            print("  ", p)


if __name__ == "__main__":
    main()
