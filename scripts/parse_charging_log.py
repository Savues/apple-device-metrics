#!/usr/bin/env python3
"""Parse an iOS charging diary into a DE-IDENTIFIED session dataset.

Input : raw diary (local only, NEVER committed) -- 3 lines per session:
          开始充电：<date> <time> | 结束充电：<date> <time>
          充电时长：<dur> | 充入电量：<pct>%
          电池电量：<a>% → <b>%  | 每分钟充入：<r>%
Output: CSV with session_id, day_offset, duration_sec, soc_start, soc_end,
        charged_pct, rate_pct_per_min, anomaly.
        NO absolute dates, NO clock times, NO device identifiers.

Usage: python3 parse_charging_log.py <raw.txt> <out.csv> [summary.json]
"""
import csv
import json
import re
import sys
from datetime import datetime

RE_START = re.compile(
    r"开始充电：(\d+)年(\d+)月(\d+)日 (\d+):(\d+):(\d+) "
    r"\| 结束充电：(\d+)年(\d+)月(\d+)日 (\d+):(\d+):(\d+)")
RE_DUR = re.compile(r"充电时长：(.*?) \| 充入电量：(-?\d+)%")
RE_SOC = re.compile(r"电池电量：(\d+)% → (\d+)%\s*\| 每分钟充入：(-?[\d.]+)%")


def parse_duration(s):
    h = re.search(r"(\d+)小时", s)
    m = re.search(r"(\d+)分钟", s)
    sec = re.search(r"(\d+)秒", s)
    return (int(h.group(1)) * 3600 if h else 0) + \
           (int(m.group(1)) * 60 if m else 0) + \
           (int(sec.group(1)) if sec else 0)


def parse(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    sessions, errors = [], []
    i, base = 0, None
    while i < len(lines):
        m = RE_START.search(lines[i])
        if not m:
            i += 1
            continue
        try:
            g = [int(x) for x in m.groups()]
            st = datetime(g[0], g[1], g[2], g[3], g[4], g[5])
            dm = RE_DUR.search(lines[i + 1])
            sm = RE_SOC.search(lines[i + 2])
            if not dm or not sm:
                raise ValueError("malformed duration/soc line")
            dur = parse_duration(dm.group(1))
            charged = int(dm.group(2))
            s0, s1, rate = int(sm.group(1)), int(sm.group(2)), float(sm.group(3))
            if base is None:
                base = st.date()
            # anomaly: charge session where SOC fell (pass-through / bad contact),
            # or a no-op session, or a mismatch between declared and computed values
            flags = []
            if charged < 0 or s1 < s0:
                flags.append("soc_dropped")
            if charged == 0:
                flags.append("no_charge")
            if s1 - s0 != charged:
                flags.append("soc_delta_mismatch")
            if dur and abs(charged / (dur / 60) - rate) > 0.06:
                flags.append("rate_mismatch")
            sessions.append({
                "session_id": len(sessions) + 1,
                "day_offset": (st.date() - base).days,
                "duration_sec": dur,
                "soc_start": s0,
                "soc_end": s1,
                "charged_pct": charged,
                "rate_pct_per_min": rate,
                "anomaly": ";".join(flags),
            })
        except Exception as e:
            errors.append((i + 1, str(e), lines[i:i + 3]))
        i += 3
    return sessions, errors


def main():
    src, out = sys.argv[1], sys.argv[2]
    sessions, errors = parse(src)
    cols = ["session_id", "day_offset", "duration_sec", "soc_start",
            "soc_end", "charged_pct", "rate_pct_per_min", "anomaly"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in sessions:
            w.writerow({k: s[k] for k in cols})

    clean = [s for s in sessions if not s["anomaly"]]
    total_sec = sum(s["duration_sec"] for s in sessions)
    total_pct = sum(s["charged_pct"] for s in sessions)
    days = sorted({s["day_offset"] for s in sessions})
    per_day = {}
    for s in sessions:
        per_day[s["day_offset"]] = per_day.get(s["day_offset"], 0) + 1

    summary = {
        "sessions": len(sessions),
        "clean_sessions": len(clean),
        "parse_errors": len(errors),
        "span_days": days[-1] - days[0] + 1,
        "days_with_sessions": len(days),
        "total_duration_hours": round(total_sec / 3600, 2),
        "total_charged_pct": total_pct,
        "equivalent_full_cycles": round(total_pct / 100, 2),
        "avg_duration_min": round(total_sec / 60 / len(sessions), 2),
        "avg_charged_pct": round(total_pct / len(sessions), 2),
        "avg_rate_pct_per_min": round(
            sum(s["rate_pct_per_min"] for s in sessions) / len(sessions), 3),
        "avg_rate_excl_anomaly": round(
            sum(s["rate_pct_per_min"] for s in clean) / len(clean), 3),
        "zero_charge_sessions": sum(1 for s in sessions if s["charged_pct"] == 0),
        "soc_dropped_sessions": sum(1 for s in sessions if s["charged_pct"] < 0),
        "soc_delta_mismatch": sum(1 for s in sessions if "soc_delta_mismatch" in s["anomaly"]),
        "rate_mismatch_gt_0_06": sum(1 for s in sessions if "rate_mismatch" in s["anomaly"]),
        "max_sessions_one_day": max(per_day.values()),
        "min_sessions_one_day": min(per_day.values()),
        "avg_sessions_per_day": round(len(sessions) / (days[-1] - days[0] + 1), 2),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        print("\nPARSE ERRORS:", file=sys.stderr)
        for e in errors[:5]:
            print(e, file=sys.stderr)
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\nSPEED BINS")
    bins = [(2.0, 99, ">2.0"), (1.5, 2.0, "1.5-2.0"), (1.0, 1.5, "1.0-1.5"),
            (0.001, 1.0, "0-1.0")]
    for lo, hi, label in bins:
        n = sum(1 for s in sessions if lo < s["rate_pct_per_min"] <= hi)
        print(f"  {label:<14} {n:>4}  {n/len(sessions)*100:>5.1f}%")
    n = sum(1 for s in sessions if s["rate_pct_per_min"] <= 0)
    print(f"  {'<=0 (no gain)':<14} {n:>4}  {n/len(sessions)*100:>5.1f}%")

    print("\nSTART-SOC BANDS")
    for lo, hi in [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]:
        g = [s for s in sessions if lo <= s["soc_start"] < hi]
        if not g:
            continue
        print(f"  {lo:>2}-{hi:<3}%  {len(g):>3} sessions  "
              f"avg charged {sum(x['charged_pct'] for x in g)/len(g):5.1f}%  "
              f"avg rate {sum(x['rate_pct_per_min'] for x in g)/len(g):.2f}%/min")

    print("\nEXTREMES")
    longest = max(sessions, key=lambda x: x["duration_sec"])
    fastest = max(sessions, key=lambda x: x["rate_pct_per_min"])
    print(f"  longest: {longest['duration_sec']/3600:.2f}h "
          f"(id={longest['session_id']}, +{longest['charged_pct']}%)")
    print(f"  fastest: {fastest['rate_pct_per_min']}%/min "
          f"(id={fastest['session_id']}, {fastest['soc_start']}→{fastest['soc_end']}%)")


if __name__ == "__main__":
    main()
