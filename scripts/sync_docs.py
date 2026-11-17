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
        "date_half": d500.strftime("%Y-%m"),
        "ncc_kilo": rnd(k['ncc_mah']),
        "chem_kilo": rnd(k['chemical_only_mah']),
        "lockin_kilo": rnd(k['reversible_lockin_mah']),
        "wear_kilo": rnd(k['total_wear_mah']),
        "wear_kilo_pct": rnd(k['total_wear_mah'] / RATED * 100, 1),
    }
    return v, blocks(P, fc)


SENS_LABELS = {
    "recent 7 days": ("recent 7 days", "最近 7 天"),
    "recent 14 days": ("recent 14 days", "最近 14 天"),
    "recent 30 days": ("recent 30 days", "最近 30 天"),
    "independent gauge snapshots (regression)":
        ("independent gauge snapshots (regression)", "独立电量计快照（回归）"),
    "full 76-day diary (primary)":
        ("full 76-day diary (primary)", "完整 76 天充电日志（主值）"),
    "57-day export regression (old, biased high)":
        ("old 57-day regression (withdrawn)", "旧的 57 天回归（已撤回）"),
}


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
            en, zh = SENS_LABELS[r["case"]]
            primary = "primary" in r["case"]
            cells = [en if lang == "en" else zh,
                     f"{r['cycles_per_day']:.2f}" if primary else f"{r['cycles_per_day']}",
                     f"{r['mah_per_day']}", r["date_250"], r["date_1000"],
                     rnd(r['ncc_mah_at_1000'])]
            if primary:
                cells = [f"**{c}**" for c in cells]
            rows.append("| " + " | ".join(cells) + " |")
        out[f"fc_sens_{lang}"] = "\n".join(rows)

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
