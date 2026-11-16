#!/usr/bin/env python3
"""iphone-01-only battery curve forecast, using CURRENT daily usage and mAh.

Owner request: forecast from the main device's own data only, at its present
daily usage, and report real mAh (not just percentages). The two other
reference devices are excluded (irregular usage).

Usage rate: measured from this device's own charging diary (76 days,
4801 mAh/day = 1.30 cycles/day) and independently confirmed by the analytics
CycleCount regression over 7 independent gauge writes (1.233 cycles/day,
2026-11-08 .. 11-15). The earlier 1.5386 cycles/day from a 57-day regression
on sparse export rows was biased high by a heavy 30-day stretch and is NOT
current usage; it is retained only as a sensitivity case.

Outputs: docs/iphone17-forecast.{csv,json,svg}
"""
import csv
import json
import os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATED = 3692

# --- measured on iphone-01 only --------------------------------------------
BASE_DATE = date(2026, 11, 16)
BASE_CYCLE = 209
BASE_NCC = 3660
BASE_HEALTH = BASE_NCC / RATED * 100          # 99.133%
APPLE_DISPLAY = 101

# Current daily usage (primary). Two independent device measurements agree.
DIARY_TOTAL_PCT = 9883                         # sum(charged_pct), 325 sessions
DIARY_DAYS = 76                               # 2026-09-01 .. 2026-11-15
MAH_PER_DAY = DIARY_TOTAL_PCT / 100 * RATED / DIARY_DAYS   # 4801.1 mAh/day
CYCLES_PER_DAY = round(MAH_PER_DAY / RATED, 2)             # 1.30 /day
# Independent check: 7 non-stale analytics gauge writes, 2026-11-08..11-15,
# CycleCount 200 -> 209 over 7.28 days => 1.233 cycles/day by regression.
PLATEAU_PP_PER_DAY = 0.00476                   # 3 non-step segments
PLATEAU_MAH_PER_DAY = PLATEAU_PP_PER_DAY / 100 * RATED
STEP_PP_PER_NODE = 0.43                        # observed 200-node step
STEP_MAH_PER_NODE = STEP_PP_PER_NODE / 100 * RATED

NODES = [(250, 40), (300, 60), (1000, 110)]   # cycles -> cumulative -mV

# Sensitivity: other usage windows measured on this same device.
RATE_CASES = [
    ("recent 7 days", 0.99),
    ("recent 14 days", 1.21),
    ("independent gauge snapshots (regression)", 1.233),
    ("full 76-day diary (primary)", 1.30),
    ("recent 30 days", 1.53),
    ("57-day export regression (old, biased high)", 1.5386),
]


def derating_mv(cycle):
    mv = 20
    for n, cum in NODES:
        if cycle >= n:
            mv = cum
    return mv


def at(cycle, rate=CYCLES_PER_DAY):
    days = (cycle - BASE_CYCLE) / rate
    plateau = PLATEAU_PP_PER_DAY * days
    steps = sum(1 for n, _ in NODES if cycle >= n) * STEP_PP_PER_NODE
    health = BASE_HEALTH - plateau - steps
    chemical = BASE_HEALTH - plateau
    return {
        "date": (BASE_DATE + timedelta(days=days)).isoformat(),
        "days_from_base": round(days, 1),
        "cycle": cycle,
        "vac_voltage_limit_mv": 4500 - derating_mv(cycle),
        "ncc_health_pct": round(health, 3),
        "ncc_mah": round(health / 100 * RATED, 1),
        "plateau_loss_pp": round(plateau, 3),
        "plateau_loss_mah": round(plateau / 100 * RATED, 1),
        "node_lockin_pp": round(steps, 3),
        "node_lockin_mah": round(steps / 100 * RATED, 1),
        "chemical_only_pct": round(chemical, 3),
        "chemical_only_mah": round(chemical / 100 * RATED, 1),
        "apple_display": APPLE_DISPLAY if cycle == BASE_CYCLE else "",
    }


def main():
    checkpoints = {BASE_CYCLE}
    c = float(BASE_CYCLE)
    while c <= 1500:
        checkpoints.add(int(round(c)))
        c += CYCLES_PER_DAY * 30.44
    for n, _ in NODES:
        checkpoints.add(n)
    rows = [at(cyc) for cyc in sorted(checkpoints)]

    with open(os.path.join(ROOT, "docs/iphone17-forecast.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    node_table = [{k: at(n)[k] for k in
                   ("cycle", "date", "days_from_base", "vac_voltage_limit_mv",
                    "ncc_health_pct", "ncc_mah", "node_lockin_mah",
                    "chemical_only_pct", "chemical_only_mah")}
                  for n, _ in NODES]

    sensitivity = []
    for label, r in RATE_CASES:
        sensitivity.append({
            "case": label,
            "cycles_per_day": r,
            # The primary rate is the measured diary throughput; the other
            # cases are hypothetical rates, so convert them via the nameplate.
            "mah_per_day": (round(MAH_PER_DAY) if r == CYCLES_PER_DAY
                            else round(r * RATED)),
            "date_250": at(250, r)["date"],
            "date_300": at(300, r)["date"],
            "date_1000": at(1000, r)["date"],
            "health_at_1000_pct": at(1000, r)["ncc_health_pct"],
            "ncc_mah_at_1000": at(1000, r)["ncc_mah"],
        })

    params = {
        "scope": "iphone-01 ONLY. Other reference devices excluded from fitting.",
        "owner_question": "Is this based on current daily usage, and does it include real mAh? YES to both.",
        "base": {
            "date": BASE_DATE.isoformat(), "cycle": BASE_CYCLE,
            "ncc_mah": BASE_NCC, "health_pct": round(BASE_HEALTH, 3),
            "apple_max_capacity_percent": APPLE_DISPLAY,
        },
        "current_usage": {
            "cycles_per_day": CYCLES_PER_DAY,
            "mah_per_day_throughput": round(MAH_PER_DAY),
            "basis": "76-day charging diary (9883% = 364880 mAh total) = 4801 mAh/day; independently confirmed by 7 non-stale analytics gauge writes (CycleCount 200->209 over 7.28 days) = 1.233 cycles/day by regression",
            "previous_rate_withdrawn": "1.5386 cycles/day (57-day regression on sparse export rows) was biased high by a heavy 30-day stretch; kept only as a sensitivity case",
            "plateau_wear_mah_per_day": round(PLATEAU_MAH_PER_DAY, 3),
            "lockin_mah_per_20mv_node": round(STEP_MAH_PER_NODE, 1),
        },
        "mah_conversion": "ncc_mah = ncc_health_pct / 100 * 3692 (fixed nameplate rated capacity). Same for chemical_only_mah and node_lockin_mah.",
        "assumptions": [
            "Current 1.30 cycles/day continues (sensitivity table shows other windows)",
            "Plateau slope 0.00476 pp/day = 0.176 mAh/day stays constant",
            "Each future 20mV node costs the same -0.43pp = -15.9 mAh as the observed 200 node",
            ">=1000 band 4390 mV extrapolated from iPhone 13 series (low confidence)",
            "Apple displayed MaximumCapacityPercent NOT modelled: constant 101 on all 7 files",
        ],
        "not_used": ["reference-01 (1420/73%)", "reference-02 (2919/67%)",
                     "Apple 1000-cycle/80% as ageing anchor",
                     "cross-device concave ageing curve"],
        "nodes": node_table,
        "at_1000_cycles": {
            "ncc_health_pct": at(1000)["ncc_health_pct"],
            "ncc_mah": at(1000)["ncc_mah"],
            "reversible_lockin_mah": at(1000)["node_lockin_mah"],
            "chemical_only_pct": at(1000)["chemical_only_pct"],
            "chemical_only_mah": at(1000)["chemical_only_mah"],
            "total_wear_mah": round(RATED - at(1000)["chemical_only_mah"], 1),
        },
        "sensitivity_to_usage_rate": sensitivity,
        "uncertainty": "Medium to 500 cycles; LOW beyond 1000 (extrapolated voltage band, no ageing acceleration modelled).",
    }
    with open(os.path.join(ROOT, "docs/iphone17-forecast.json"), "w",
              encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    print(json.dumps({k: params[k] for k in
                      ("current_usage", "nodes", "at_1000_cycles",
                       "sensitivity_to_usage_rate")},
                     ensure_ascii=False, indent=2))
    write_svg(rows, node_table)


def write_svg(rows, nodes):
    W, H = 1000, 520
    L, R, T, B = 70, 30, 30, 60
    x0, x1, y0, y1 = BASE_CYCLE, 1500, 88, 102
    X = lambda c: L + (c - x0) / (x1 - x0) * (W - L - R)
    Y = lambda v: T + (y1 - v) / (y1 - y0) * (H - T - B)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<rect width="100%" height="100%" fill="#fff"/>',
         '<style>text{font:12px -apple-system,Helvetica,Arial,sans-serif;fill:#333}'
         '.grid{stroke:#e8e8e8}.axis{stroke:#999}.node{stroke:#bbb;stroke-dasharray:4 4}</style>']
    for v in range(88, 103, 2):
        p.append(f'<line class="grid" x1="{L}" y1="{Y(v):.1f}" x2="{W-R}" y2="{Y(v):.1f}"/>')
        p.append(f'<text x="{L-8}" y="{Y(v)+4:.1f}" text-anchor="end">{v}%</text>')
        p.append(f'<text x="{W-R+4}" y="{Y(v)+4:.1f}" fill="#999">{round(v/100*RATED)}</text>')
    for c in (200, 400, 600, 800, 1000, 1200, 1400):
        p.append(f'<text x="{X(c):.1f}" y="{H-B+20}" text-anchor="middle">{c}</text>')
    p.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-12}" text-anchor="middle">Cycle count (right axis: mAh)</text>')
    for n in nodes:
        p.append(f'<line class="node" x1="{X(n["cycle"]):.1f}" y1="{T}" x2="{X(n["cycle"]):.1f}" y2="{H-B}"/>')
        p.append(f'<text x="{X(n["cycle"])+4:.1f}" y="{T+12}">{n["cycle"]} ({n["vac_voltage_limit_mv"]}mV)</text>')
    def path(k, col, dash=""):
        pts = " ".join(f"{'M' if i==0 else 'L'}{X(r['cycle']):.1f},{Y(r[k]):.1f}"
                       for i, r in enumerate(rows))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return f'<path d="{pts}" fill="none" stroke="{col}" stroke-width="2.5"{d}/>'
    p.append(path("chemical_only_pct", "#2a9d55", "5 4"))
    p.append(path("ncc_health_pct", "#1f6feb"))
    p.append(f'<circle cx="{X(BASE_CYCLE):.1f}" cy="{Y(BASE_HEALTH):.1f}" r="5" fill="#1f6feb"/>')
    p.append(f'<text x="{X(BASE_CYCLE)+10:.1f}" y="{Y(BASE_HEALTH)-8:.1f}">now {BASE_CYCLE} cyc / {BASE_HEALTH:.3f}% / {BASE_NCC} mAh</text>')
    lx, ly = L + 20, T + 20
    p.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+28}" y2="{ly}" stroke="#1f6feb" stroke-width="2.5"/>')
    p.append(f'<text x="{lx+34}" y="{ly+4}">NCC (includes reversible lock-in)</text>')
    p.append(f'<line x1="{lx}" y1="{ly+20}" x2="{lx+28}" y2="{ly+20}" stroke="#2a9d55" stroke-width="2.5" stroke-dasharray="5 4"/>')
    p.append(f'<text x="{lx+34}" y="{ly+24}">Chemical ageing only (mAh on right axis)</text>')
    p.append(f'<text x="{lx}" y="{ly+48}" font-size="11" fill="#777">At current usage {CYCLES_PER_DAY:.2f} cycles/day = {round(MAH_PER_DAY)} mAh/day. iphone-01 only.</text>')
    p.append('</svg>')
    with open(os.path.join(ROOT, "docs/iphone17-forecast.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(p))


if __name__ == "__main__":
    main()
