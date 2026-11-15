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
# Only the sparse 6-row export is monotonic. Daily analytics snapshots show
# small rebounds (3658 -> 3659 mAh), so do NOT apply this check to the archive.
check("export-table nominal capacity monotonically decreasing",
      all(a >= b for a, b in zip(nom, nom[1:])))

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

print("\n=== analytics archive ===")
ana_dir = os.path.join(ROOT, "devices", "iphone-01", "analytics")
ana_files = sorted(f for f in os.listdir(ana_dir) if f.endswith(".json")) \
    if os.path.isdir(ana_dir) else []
check("at least one analytics snapshot", len(ana_files) > 0, f"{len(ana_files)} file(s)")

# Third-party node table: (<upper bound exclusive>, limit mV)
bands = [(200, 4500), (250, 4480), (300, 4460), (1000, 4440), (10 ** 9, 4390)]
snaps = []
for fn in ana_files:
    p = os.path.join(ana_dir, fn)
    blob = open(p, encoding="utf-8").read()
    r = json.loads(blob)
    snaps.append(r)
    check(f"{fn}: no identifier-like keys",
          not any(k in blob for k in ("deviceId", "incident_id", "configUuid",
                                      "carrier", "productSku", "Serial", "ChemID")))
    check(f"{fn}: filename matches header date",
          fn == r.get("date", "") + ".json")
    check(f"{fn}: Apple health field present",
          isinstance(r.get("maximum_capacity_percent_reported"), int),
          f"MaximumCapacityPercent={r.get('maximum_capacity_percent_reported')}")
    check(f"{fn}: health matches NCC/3692",
          abs(r.get("nominal_health_pct", 0) -
              r.get("nominal_charge_capacity_mah", 0) / RATED * 100) < 0.01)
    exp = next(mv for upper, mv in bands if r.get("cycle_count", 0) < upper)
    check(f"{fn}: VacVoltageLimit matches node band",
          r.get("vac_voltage_limit_mv") == exp,
          f"cycle={r.get('cycle_count')} {r.get('vac_voltage_limit_mv')}mV "
          f"expected {exp}mV")

check("snapshot dates sorted & unique",
      [r["date"] for r in snaps] == sorted({r["date"] for r in snaps}))

# A daily analytics file may re-report a stale gauge snapshot. Flag (do not
# fail) consecutive files whose whitelisted battery state is byte-identical
# apart from the date, so repeats are not mistaken for independent samples.
def state_without_date(r):
    return json.dumps({k: v for k, v in sorted(r.items()) if k != "date"},
                      sort_keys=True)
stale = [b["date"] for a, b in zip(snaps, snaps[1:])
         if state_without_date(a) == state_without_date(b)]
if stale:
    print(f"  NOTE  stale gauge snapshot repeated on: {', '.join(stale)}")
check("gauge_update_time_utc present on all snapshots",
      all(r.get("gauge_update_time_utc") for r in snaps))

# Timeline CSV must be exactly the projection of the archive.
tl = load("devices/iphone-01/analytics-timeline.csv")
check("timeline row count matches archive", len(tl) == len(snaps),
      f"{len(tl)} vs {len(snaps)}")
check("timeline dates match archive",
      [x["date"] for x in tl] == [r["date"] for r in snaps])
check("timeline values match archive", all(
    int(t["cycle_count"]) == s["cycle_count"] and
    int(t["vac_voltage_limit_mv"]) == s["vac_voltage_limit_mv"] and
    int(t["nominal_charge_capacity_mah"]) == s["nominal_charge_capacity_mah"]
    for t, s in zip(tl, snaps)))
check("all timeline rows match their node band",
      all(t["voltage_matches_band"] == "True" for t in tl))

# The newest analytics snapshot must agree with the newest health CSV row.
if snaps:
    newest = snaps[-1]
    check("newest analytics cycle == last health sample",
          newest["cycle_count"] == cyc[-1])
    check("newest analytics NCC == last health sample",
          newest["nominal_charge_capacity_mah"] == nom[-1])
    check("newest analytics DailyMinSoc == last health sample",
          newest["daily_min_soc_pct"] == int(health[-1]["min_soc_pct"]))

print("\n" + ("ALL CHECKS PASSED" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
