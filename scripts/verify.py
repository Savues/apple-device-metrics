#!/usr/bin/env python3
"""Consistency checks for the published datasets.

Run: python3 scripts/verify.py
Exits non-zero on any failure. Does not need the private raw diary.
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATED = 3692
failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def load(path):
    with open(os.path.join(ROOT, path), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


health = load("devices/iphone-01/health-samples.csv")
sess = load("devices/iphone-01/charging-sessions.csv")
summary = json.load(open(os.path.join(ROOT, "docs/charging-summary.json"), encoding="utf-8"))
dev = json.load(open(os.path.join(ROOT, "devices/iphone-01/device.json"), encoding="utf-8"))

print("=== nameplate ===")
check("rated capacity matches health denominator", dev["rated_capacity_mah"] == RATED)
check("rated energy consistent",
      abs(dev["rated_energy_wh"] - dev["nominal_voltage_v"] * RATED / 1000) < 0.001,
      f"{dev['nominal_voltage_v']}V x {RATED}mAh = {dev['nominal_voltage_v']*RATED/1000:.3f}Wh")

print("\n=== health snapshots ===")
check("6 snapshots", len(health) == 6, str(len(health)))
worst = 0.0
for r in health:
    calc = int(r["nominal_capacity_mah"]) / RATED * 100
    worst = max(worst, abs(calc - float(r["nominal_health_pct"])))
check("health = nominal/3692 within 0.01pp", worst < 0.01, f"max error {worst:.4f} pp")
cyc = [int(r["cycle_count"]) for r in health]
check("cycle counts strictly increasing", all(a < b for a, b in zip(cyc, cyc[1:])))
nom = [int(r["nominal_capacity_mah"]) for r in health]
check("nominal capacity monotonically decreasing", all(a >= b for a, b in zip(nom, nom[1:])))

print("\n=== charging sessions ===")
check("session count matches summary", len(sess) == summary["sessions"],
      f"{len(sess)} vs {summary['sessions']}")
check("session ids contiguous",
      [int(r["session_id"]) for r in sess] == list(range(1, len(sess) + 1)))
total_pct = sum(int(r["charged_pct"]) for r in sess)
total_sec = sum(int(r["duration_sec"]) for r in sess)
check("total charged matches summary", total_pct == summary["total_charged_pct"],
      f"{total_pct}")
check("total duration matches summary",
      abs(total_sec / 3600 - summary["total_duration_hours"]) < 0.01,
      f"{total_sec/3600:.2f}h")
check("span days matches summary",
      max(int(r["day_offset"]) for r in sess) + 1 == summary["span_days"])

bad_soc = [r["session_id"] for r in sess
           if int(r["soc_end"]) - int(r["soc_start"]) != int(r["charged_pct"])]
check("soc delta == charged for all rows", not bad_soc, f"{len(bad_soc)} mismatches")
bad_rate = [r["session_id"] for r in sess
            if int(r["duration_sec"]) and
            abs(int(r["charged_pct"]) / (int(r["duration_sec"]) / 60)
                - float(r["rate_pct_per_min"])) > 0.06]
check("declared rate consistent", not bad_rate, f"{len(bad_rate)} mismatches")
n_nocharge = sum(1 for r in sess if int(r["charged_pct"]) == 0)
n_drop = sum(1 for r in sess if int(r["charged_pct"]) < 0)
check("no-gain sessions match summary", n_nocharge == summary["zero_charge_sessions"])
check("soc-dropped sessions match summary", n_drop == summary["soc_dropped_sessions"],
      f"{n_drop} session(s)")

print("\n=== de-identification ===")
blob = open(os.path.join(ROOT, "devices/iphone-01/charging-sessions.csv"),
            encoding="utf-8").read()
check("no absolute calendar dates", not re.search(r"\d{4}[-/年]\d{1,2}", blob))
check("no clock times", not re.search(r"\d{1,2}:\d{2}", blob))
# The source diary header carries a device identifier. Check structurally
# (an uppercase alphanumeric token) rather than hard-coding it here, so the
# identifier itself never appears in the published repository.
check("no source device identifier token",
      not re.search(r"\b[A-Z0-9]{8,}\b", blob))
allowed = {"session_id", "day_offset", "duration_sec", "soc_start", "soc_end",
           "charged_pct", "rate_pct_per_min", "anomaly"}
hdr = set(open(os.path.join(ROOT, "devices/iphone-01/charging-sessions.csv"),
               encoding="utf-8").readline().strip().split(","))
check("only whitelisted columns", hdr == allowed, str(sorted(hdr)))

print("\n=== derived figures quoted in findings.md ===")
rates = [float(r["rate_pct_per_min"]) for r in sess]
clean = [float(r["rate_pct_per_min"]) for r in sess if not r["anomaly"]]
check("mean rate", abs(sum(rates) / len(rates) - summary["avg_rate_pct_per_min"]) < 0.001)
check("mean rate excl anomalies",
      abs(sum(clean) / len(clean) - summary["avg_rate_excl_anomaly"]) < 0.001,
      f"{sum(clean)/len(clean):.3f} %/min")

print("\n" + ("ALL CHECKS PASSED" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
