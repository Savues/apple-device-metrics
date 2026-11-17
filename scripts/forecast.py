#!/usr/bin/env python3
"""iphone-01-only battery curve forecast, using CURRENT daily usage and mAh.

Owner request: forecast from the main device's own data only, at its present
daily usage, and report real mAh (not just percentages). The two other
reference devices are excluded (irregular usage).

Every parameter is derived from the published data by scripts/params.py:
base = latest analytics snapshot; usage = charging diary throughput;
cross-check = analytics CycleCount regression over non-stale gauge writes;
plateau slope and node step = the 6-row health export. Importing a new
snapshot and re-running this script refreshes the forecast with no edits.

Outputs: docs/iphone17-forecast.{csv,json,svg}
"""
import csv
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import NODES, FIRST_BAND_MV, RATED, ROOT, derive  # noqa: E402

P = derive()

# --- measured on iphone-01 only --------------------------------------------
BASE_DATE = date.fromisoformat(P["base"]["date"])
BASE_CYCLE = P["base"]["cycle"]
BASE_NCC = P["base"]["ncc_mah"]
BASE_HEALTH = P["base"]["health_pct"]
APPLE_DISPLAY = P["base"]["apple_display"]

DIARY_TOTAL_PCT = P["diary"]["total_charged_pct"]
DIARY_DAYS = P["diary"]["span_days"]
MAH_PER_DAY = P["diary"]["mah_per_day"]
CYCLES_PER_DAY = P["diary"]["cycles_per_day"]
GAUGE = P["rates"]
PLATEAU_PP_PER_DAY = P["plateau_pp_per_day"]
PLATEAU_MAH_PER_DAY = PLATEAU_PP_PER_DAY / 100 * RATED
STEP_PP_PER_NODE = P["step_pp_per_node"]
STEP_MAH_PER_NODE = STEP_PP_PER_NODE / 100 * RATED

# Sensitivity: other usage windows measured on this same device.
RATE_CASES = [
    ("recent 7 days", GAUGE["recent_7"]),
    ("recent 14 days", GAUGE["recent_14"]),
    ("independent gauge snapshots (regression)", GAUGE["gauge_regression"]),
    (f"full {DIARY_DAYS}-day diary (primary)", CYCLES_PER_DAY),
    ("recent 30 days", GAUGE["recent_30"]),
    ("57-day export regression (old, biased high)", GAUGE["export_regression"]),
]
DIARY_BASIS = (
    f"{DIARY_DAYS}-day charging diary ({DIARY_TOTAL_PCT}% = "
    f"{round(DIARY_TOTAL_PCT / 100 * RATED)} mAh total) = "
    f"{round(MAH_PER_DAY)} mAh/day; cross-checked by "
    f"{P['non_stale_snapshot_count']} non-stale analytics gauge writes "
    f"(CycleCount +{GAUGE['gauge_cycle_delta']} over "
    f"{GAUGE['gauge_span_days']} days) = {GAUGE['gauge_regression']} "
    f"cycles/day by regression. Both rely on coulomb counting, so the "
    f"cross-check is not independent")


def derating_mv(cycle):
    mv = 20
    for n, cum in NODES:
        if cycle >= n:
            mv = cum
    return mv


# Only nodes still ahead of the base cost a future step; a node already
# passed is contained in the measured base NCC.
FUTURE_NODES = [(n, mv) for n, mv in NODES if n > BASE_CYCLE]


def at(cycle, rate=CYCLES_PER_DAY):
    days = (cycle - BASE_CYCLE) / rate
    plateau = PLATEAU_PP_PER_DAY * days
    steps = sum(1 for n, _ in FUTURE_NODES if cycle >= n) * STEP_PP_PER_NODE
    health = BASE_HEALTH - plateau - steps
    chemical = BASE_HEALTH - plateau
    return {
        "date": (BASE_DATE + timedelta(days=days)).isoformat(),
        "days_from_base": round(days, 1),
        "cycle": cycle,
        "vac_voltage_limit_mv": FIRST_BAND_MV - derating_mv(cycle),
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
    for n, _ in FUTURE_NODES:
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
                  for n, _ in FUTURE_NODES]

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
        "generated_from": "scripts/params.py (derived from published CSV/JSON; no hand-entered constants)",
        "base": {
            "date": BASE_DATE.isoformat(), "cycle": BASE_CYCLE,
            "ncc_mah": BASE_NCC, "health_pct": round(BASE_HEALTH, 3),
            "apple_max_capacity_percent": APPLE_DISPLAY,
        },
        "current_usage": {
            "cycles_per_day": CYCLES_PER_DAY,
            "mah_per_day_throughput": round(MAH_PER_DAY),
            "basis": DIARY_BASIS,
            "gauge_regression_cycles_per_day": GAUGE["gauge_regression"],
            "previous_rate_withdrawn": "1.5386 cycles/day (57-day regression on sparse export rows) was biased high by a heavy 30-day stretch; kept only as a sensitivity case",
            "plateau_wear_mah_per_day": round(PLATEAU_MAH_PER_DAY, 3),
            "lockin_mah_per_20mv_node": round(STEP_MAH_PER_NODE, 1),
        },
        "mah_conversion": "ncc_mah = ncc_health_pct / 100 * 3692 (fixed nameplate rated capacity). Same for chemical_only_mah and node_lockin_mah.",
        "assumptions": [
            f"Current {CYCLES_PER_DAY:.2f} cycles/day continues (sensitivity table shows other windows)",
            f"Plateau slope {PLATEAU_PP_PER_DAY} pp/day = {PLATEAU_MAH_PER_DAY:.3f} mAh/day stays constant",
            f"Each future 20mV node costs the same -{STEP_PP_PER_NODE}pp = -{STEP_MAH_PER_NODE:.1f} mAh as the observed 200 node",
            ">=1000 band 4390 mV extrapolated from iPhone 13 series (low confidence)",
            f"Apple displayed MaximumCapacityPercent NOT modelled: latest value {APPLE_DISPLAY} across {P['snapshot_count']} analytics files",
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


ADV = {  # Helvetica advance widths (/1000 em) for the characters used here
    " ": 278, "(": 333, ")": 333, "/": 278, ".": 278, ",": 278, "%": 889, "-": 333,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556, "h": 556,
    "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556, "p": 556,
    "q": 556, "r": 333, "s": 500, "t": 278, "u": 556, "v": 500, "w": 722, "x": 500,
    "y": 500, "z": 500, "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611,
    "G": 778, "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722,
    "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667,
    "W": 944, "X": 667, "Y": 667, "Z": 611,
}


def text_width(s, size=12):
    """Approximate rendered width (deliberately ~6% wide, so checks stay safe)."""
    w = 0.0
    for ch in s:
        w += 556 if ch.isdigit() else ADV.get(ch, 556)
    return w / 1000 * size * 1.06


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
    placed = []
    for n in sorted(nodes, key=lambda n: n["cycle"]):
        p.append(f'<line class="node" x1="{X(n["cycle"]):.1f}" y1="{T}" x2="{X(n["cycle"]):.1f}" y2="{H-B}"/>')
        label = f'{n["cycle"]} ({n["vac_voltage_limit_mv"]}mV)'
        lx = X(n["cycle"]) + 4
        lw = text_width(label)
        ly = T + 12
        while any(ly - 10 < py + ph and ly + 4 > py and lx < px + pw + 6 and lx + lw + 6 > px
                  for px, py, pw, ph in placed):
            ly += 16
        placed.append((lx, ly - 10, lw, 14))
        p.append(f'<text x="{lx:.1f}" y="{ly}">{label}</text>')
    def path(k, col, dash=""):
        pts = " ".join(f"{'M' if i==0 else 'L'}{X(r['cycle']):.1f},{Y(r[k]):.1f}"
                       for i, r in enumerate(rows))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return f'<path d="{pts}" fill="none" stroke="{col}" stroke-width="2.5"{d}/>'
    p.append(path("chemical_only_pct", "#2a9d55", "5 4"))
    p.append(path("ncc_health_pct", "#1f6feb"))
    p.append(f'<circle cx="{X(BASE_CYCLE):.1f}" cy="{Y(BASE_HEALTH):.1f}" r="5" fill="#1f6feb"/>')
    p.append(f'<text x="{X(BASE_CYCLE)+10:.1f}" y="{Y(BASE_HEALTH)-8:.1f}">now {BASE_CYCLE} cyc / {BASE_HEALTH:.3f}% / {BASE_NCC} mAh</text>')
    # Legend sits in the empty lower-left corner: the curves are far above it,
    # while the top-left belongs to the 250/300 node labels (x starts at the base).
    lx, ly = L + 20, H - B - 36
    p.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+28}" y2="{ly}" stroke="#1f6feb" stroke-width="2.5"/>')
    p.append(f'<text x="{lx+34}" y="{ly+4}">NCC (includes reversible lock-in)</text>')
    p.append(f'<line x1="{lx}" y1="{ly+20}" x2="{lx+28}" y2="{ly+20}" stroke="#2a9d55" stroke-width="2.5" stroke-dasharray="5 4"/>')
    p.append(f'<text x="{lx+34}" y="{ly+24}">Chemical ageing only (mAh on right axis)</text>')
    p.append(f'<text x="{L}" y="{T-10}" font-size="11" fill="#777">At current usage {CYCLES_PER_DAY:.2f} cycles/day = {round(MAH_PER_DAY)} mAh/day. iphone-01 only.</text>')
    p.append('</svg>')
    with open(os.path.join(ROOT, "docs/iphone17-forecast.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(p))


if __name__ == "__main__":
    main()
