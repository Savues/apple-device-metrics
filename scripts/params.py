#!/usr/bin/env python3
"""Single source for every number derived from iphone-01's published data.

forecast.py and verify.py both import this module, so a new analytics
snapshot or a re-parsed charging diary changes the forecast without editing
any constant by hand.

Run directly to print the derived parameters:
    python3 scripts/params.py
"""
import csv
import glob
import json
import os
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV = os.path.join(ROOT, "devices", "iphone-01")
RATED = 3692

# Third-party cycle-node table for the iPhone 17 series
# (docs/voltage-nodes.md). (node_cycle, cumulative derating in mV).
# The >=1000 value is extrapolated from the iPhone 13 series.
NODES = [(250, 40), (300, 60), (1000, 110)]
FIRST_BAND_MV = 4500
STEP_NODE = 200            # the node observed on this device
STEP_THRESHOLD_MAH = 10    # NCC drop above this in one export segment = step
                           # (daily gauge jitter is <=2 mAh)


def _csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _slope(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    return (sum((x - mx) * (y - my) for x, y in zip(xs, ys)) /
            sum((x - mx) ** 2 for x in xs))


def snapshots():
    out = []
    for p in sorted(glob.glob(os.path.join(DEV, "analytics", "*.json"))):
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f))
    return sorted(out, key=lambda r: r["date"])


def sessions():
    return _csv(os.path.join(DEV, "charging-sessions.csv"))


def health_export():
    return _csv(os.path.join(DEV, "health-samples.csv"))


def non_stale(snaps):
    """Drop files that re-report the previous gauge write."""
    out = []
    for s in snaps:
        if not out or out[-1]["gauge_update_time_utc"] != s["gauge_update_time_utc"]:
            out.append(s)
    return out


def derive():
    snaps = snapshots()
    sess = sessions()
    export = health_export()
    latest = snaps[-1]

    # --- usage from the charging diary ------------------------------------
    total_pct = sum(int(r["charged_pct"]) for r in sess)
    last_day = max(int(r["day_offset"]) for r in sess)
    span_days = last_day - min(int(r["day_offset"]) for r in sess) + 1
    mah_per_day = total_pct / 100 * RATED / span_days

    def window(n):
        pct = sum(int(r["charged_pct"]) for r in sess
                  if int(r["day_offset"]) > last_day - n)
        return round(pct / 100 / n, 2)

    # --- usage from independent gauge writes ------------------------------
    ns = non_stale(snaps)
    gx = [datetime.fromisoformat(s["gauge_update_time_utc"].replace("Z", "+00:00"))
          .timestamp() / 86400 for s in ns]
    gauge_rate = round(_slope(gx, [s["cycle_count"] for s in ns]), 3)

    # --- old export regression (kept as a sensitivity case) ---------------
    ex = [date.fromisoformat(r["date"]).toordinal() for r in export]
    export_rate = round(_slope(ex, [int(r["cycle_count"]) for r in export]), 4)

    # --- ageing from the 6-row health export ------------------------------
    # A segment whose NCC falls by more than STEP_THRESHOLD_MAH is a one-off
    # step (126->152 and the 200-node 194->208, docs/findings.md); all other
    # segments form the plateau. The step used for future nodes is the one
    # that straddles the observed 200-cycle node. NCC/3692 throughout.
    plateau, step_mah = [], None
    for a, b in zip(export, export[1:]):
        ca, cb = int(a["cycle_count"]), int(b["cycle_count"])
        na, nb = int(a["nominal_capacity_mah"]), int(b["nominal_capacity_mah"])
        days = date.fromisoformat(b["date"]).toordinal() - \
            date.fromisoformat(a["date"]).toordinal()
        if ca < STEP_NODE <= cb:
            step_mah = na - nb
        elif na - nb <= STEP_THRESHOLD_MAH:
            plateau.append((na - nb) / RATED * 100 / days)
    plateau_pp_day = round(sum(plateau) / len(plateau), 5)
    step_pp = round(step_mah / RATED * 100, 2)

    return {
        "rated_mah": RATED,
        "base": {
            "date": latest["date"],
            "cycle": latest["cycle_count"],
            "ncc_mah": latest["nominal_charge_capacity_mah"],
            "health_pct": latest["nominal_charge_capacity_mah"] / RATED * 100,
            "apple_display": latest["maximum_capacity_percent_reported"],
            "vac_voltage_limit_mv": latest["vac_voltage_limit_mv"],
        },
        "snapshot_count": len(snaps),
        "non_stale_snapshot_count": len(ns),
        "diary": {
            "sessions": len(sess),
            "total_charged_pct": total_pct,
            "span_days": span_days,
            "mah_per_day": mah_per_day,
            "cycles_per_day": round(mah_per_day / RATED, 2),
        },
        "rates": {
            "recent_7": window(7),
            "recent_14": window(14),
            "recent_30": window(30),
            "gauge_regression": gauge_rate,
            "gauge_span_days": round(gx[-1] - gx[0], 2),
            "gauge_cycle_delta": ns[-1]["cycle_count"] - ns[0]["cycle_count"],
            "export_regression": export_rate,
        },
        "plateau_pp_per_day": plateau_pp_day,
        "plateau_segments": len(plateau),
        "step_pp_per_node": step_pp,
        "step_mah_observed": step_mah,
    }


if __name__ == "__main__":
    print(json.dumps(derive(), indent=2))
