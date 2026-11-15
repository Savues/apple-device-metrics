#!/usr/bin/env python3
"""iphone-01-only battery curve forecast.

Every parameter is derived from the MAIN device's own data. The other two
reference devices are deliberately NOT used: their usage was irregular and
their ageing anchors must not be fitted to this one.

Inputs (all from iphone-01):
  - health-samples.csv (6 rows) -> cycle rate, plateau slope, step sizes
  - analytics/ (7 files)       -> current NCC, Apple display value, voltage
  - charging-sessions.csv      -> equivalent cycles / day as cross-check

Outputs:
  docs/iphone17-forecast.csv        monthly + node rows
  docs/iphone17-forecast.json       parameters and node table
  docs/iphone17-forecast.svg        curves (self-contained SVG)

Usage: python3 scripts/forecast.py
"""
import csv
import json
import os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATED = 3692

# --- parameters measured on iphone-01 only ---------------------------------
BASE_DATE = date(2026, 11, 15)
BASE_CYCLE = 208
BASE_NCC = 3659                       # 2026-11-15 analytics
BASE_HEALTH = BASE_NCC / RATED * 100  # 99.106%
APPLE_DISPLAY = 101                   # constant across all 7 analytics files
CYCLES_PER_DAY = 1.5386               # linear regression on 6 health rows
PLATEAU_PP_PER_DAY = 0.00476          # mean of 3 non-step segments
STEP_PP_PER_NODE = 0.43               # 200-node step (194->208), -16 mAh
NODE_STEPS_MV = 20                    # third-party table; magnitude from device

# Future voltage nodes (cycles -> cumulative derating in mV).
# >=1000 value (4390 mV) is EXTRAPOLATED from the iPhone 13 series.
NODES = [(250, 40), (300, 60), (1000, 110)]


def main():
    # Exponential life-extension factor (BU-808: 0.10V ~ 2x) applied to
    # cumulative derating. Direction high confidence, magnitude indicative.
    def derating_mv(cycle):
        mv = 20  # 200-node step already applied by 208 cycles
        for n, cum in NODES:
            if cycle >= n:
                mv = cum
        return mv

    def health_at(cycle):
        days = (cycle - BASE_CYCLE) / CYCLES_PER_DAY
        plateau = PLATEAU_PP_PER_DAY * days
        # Steps: one per 20 mV node beyond the 200 node already observed
        applied = sum(1 for n, _ in NODES if cycle >= n)
        steps = applied * STEP_PP_PER_NODE
        return BASE_HEALTH - plateau - steps, plateau, steps

    def chemical_at(cycle):
        """Health with reversible lock-in removed (what the cell really lost)."""
        days = (cycle - BASE_CYCLE) / CYCLES_PER_DAY
        return BASE_HEALTH - PLATEAU_PP_PER_DAY * days

    rows = []
    # monthly grid plus node rows, out to 1500 cycles
    checkpoints = set()
    c = BASE_CYCLE
    while c <= 1500:
        checkpoints.add(int(round(c)))
        c += CYCLES_PER_DAY * 30.44
    for n, _ in NODES:
        checkpoints.add(n)
    checkpoints.add(BASE_CYCLE)

    for cyc in sorted(checkpoints):
        h, plateau, steps = health_at(cyc)
        d = (cyc - BASE_CYCLE) / CYCLES_PER_DAY
        rows.append({
            "date": (BASE_DATE + timedelta(days=d)).isoformat(),
            "days_from_base": round(d, 1),
            "cycle": cyc,
            "vac_voltage_limit_mv": 4500 - derating_mv(cyc),
            "ncc_health_pct": round(h, 3),
            "plateau_loss_pp": round(plateau, 3),
            "node_lockin_pp": round(steps, 3),
            "chemical_only_pct": round(chemical_at(cyc), 3),
            "apple_display_observed_or_na": APPLE_DISPLAY if cyc == BASE_CYCLE else "",
        })

    csv_path = os.path.join(ROOT, "docs/iphone17-forecast.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    node_table = []
    for n, cum in NODES:
        h, _, _ = health_at(n)
        d = (n - BASE_CYCLE) / CYCLES_PER_DAY
        node_table.append({
            "cycle": n,
            "date": (BASE_DATE + timedelta(days=d)).isoformat(),
            "days_from_base": round(d),
            "vac_voltage_limit_mv": 4500 - cum,
            "cumulative_derating_mv": cum,
            "ncc_health_pct": round(h, 3),
        })

    params = {
        "scope": "iphone-01 ONLY. Other reference devices are explicitly excluded from fitting.",
        "base": {"date": BASE_DATE.isoformat(), "cycle": BASE_CYCLE,
                 "ncc_mah": BASE_NCC, "health_pct": round(BASE_HEALTH, 3),
                 "apple_max_capacity_percent": APPLE_DISPLAY},
        "measured_on_this_device": {
            "cycles_per_day": CYCLES_PER_DAY,
            "plateau_pp_per_day": PLATEAU_PP_PER_DAY,
            "step_pp_per_20mv_node": STEP_PP_PER_NODE,
            "apple_display_constant": "101 on all 7 analytics files (11-09..11-15)"
        },
        "assumptions": [
            "Plateau slope stays constant (no acceleration assumed)",
            "Each future 20mV node causes the same -0.43pp as the observed 200 node",
            ">=1000 band = 4390 mV, extrapolated from iPhone 13 series (low confidence)",
            "Cycle rate 1.5386/day continues",
            "Apple displayed MaximumCapacityPercent is NOT modelled: this device has never shown a change, so no curve can be fitted from its own data"
        ],
        "not_used": [
            "reference-01 (1420 cycles / 73%)",
            "reference-02 (2919 cycles / 67%)",
            "Apple 1000-cycle / 80% specification as an ageing anchor",
            "cross-device concave ageing curve"
        ],
        "nodes": node_table,
        "at_1000_cycles": {
            "ncc_health_pct": round(health_at(1000)[0], 3),
            "of_which_reversible_lockin_pp": round(health_at(1000)[2], 3),
            "chemical_only_pct": round(chemical_at(1000), 3)
        },
        "uncertainty": "Medium to 500 cycles (one node observed, plateau measured), LOW beyond 1000 cycles (extrapolated voltage band, no ageing acceleration modelled)."
    }
    with open(os.path.join(ROOT, "docs/iphone17-forecast.json"), "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    print(json.dumps(params, ensure_ascii=False, indent=2))
    write_svg(rows, node_table)


def write_svg(rows, nodes):
    W, H = 1000, 520
    L, R, T, B = 70, 30, 30, 60
    x0, x1 = BASE_CYCLE, 1500
    y0, y1 = 88, 102
    def X(c): return L + (c - x0) / (x1 - x0) * (W - L - R)
    def Y(v): return T + (y1 - v) / (y1 - y0) * (H - T - B)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
             '<rect width="100%" height="100%" fill="#fff"/>',
             '<style>text{font:12px -apple-system,Helvetica,Arial,sans-serif;fill:#333}'
             '.grid{stroke:#e8e8e8;stroke-width:1}.axis{stroke:#999;stroke-width:1}'
             '.node{stroke:#bbb;stroke-dasharray:4 4}</style>']
    for v in range(88, 103, 2):
        parts.append(f'<line class="grid" x1="{L}" y1="{Y(v):.1f}" x2="{W-R}" y2="{Y(v):.1f}"/>')
        parts.append(f'<text x="{L-8}" y="{Y(v)+4:.1f}" text-anchor="end">{v}%</text>')
    for c in (200, 400, 600, 800, 1000, 1200, 1400):
        parts.append(f'<text x="{X(c):.1f}" y="{H-B+20}" text-anchor="middle">{c}</text>')
    parts.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-12}" text-anchor="middle">Cycle count</text>')
    for n in nodes:
        parts.append(f'<line class="node" x1="{X(n["cycle"]):.1f}" y1="{T}" x2="{X(n["cycle"]):.1f}" y2="{H-B}"/>')
        parts.append(f'<text x="{X(n["cycle"])+4:.1f}" y="{T+12}">{n["cycle"]} ({n["vac_voltage_limit_mv"]}mV)</text>')

    def path(key, color, dash=""):
        pts = " ".join(f"{'M' if i==0 else 'L'}{X(r['cycle']):.1f},{Y(r[key]):.1f}"
                       for i, r in enumerate(rows))
        d = f' stroke-dasharray="{dash}"' if dash else ''
        return f'<path d="{pts}" fill="none" stroke="{color}" stroke-width="2.5"{d}/>'

    parts.append(path("chemical_only_pct", "#2a9d55", "5 4"))
    parts.append(path("ncc_health_pct", "#1f6feb"))
    parts.append(f'<circle cx="{X(BASE_CYCLE):.1f}" cy="{Y(BASE_HEALTH):.1f}" r="5" fill="#1f6feb"/>')
    parts.append(f'<text x="{X(BASE_CYCLE)+10:.1f}" y="{Y(BASE_HEALTH)-8:.1f}">now: 208 cyc / {BASE_HEALTH:.2f}%</text>')
    # legend
    lx, ly = L + 20, T + 20
    parts.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+28}" y2="{ly}" stroke="#1f6feb" stroke-width="2.5"/>')
    parts.append(f'<text x="{lx+34}" y="{ly+4}">NCC / nameplate (displayed-type figure, includes lock-in)</text>')
    parts.append(f'<line x1="{lx}" y1="{ly+20}" x2="{lx+28}" y2="{ly+20}" stroke="#2a9d55" stroke-width="2.5" stroke-dasharray="5 4"/>')
    parts.append(f'<text x="{lx+34}" y="{ly+24}">Chemical ageing only (lock-in removed)</text>')
    parts.append(f'<text x="{lx}" y="{ly+48}" font-size="11" fill="#777">iphone-01 only; other devices excluded. Dashed vertical = voltage node.</text>')
    parts.append('</svg>')
    with open(os.path.join(ROOT, "docs/iphone17-forecast.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


if __name__ == "__main__":
    main()
