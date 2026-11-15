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
check("nameplate battery energy matches V x mAh",
      abs(dev.get("battery_energy_wh", 0) -
          dev["nominal_voltage_v"] * RATED / 1000) < 0.001)
check("cell energy exceeds pack energy",
      dev.get("cell_energy_wh", 0) > dev.get("battery_energy_wh", 0),
      f"{dev.get('cell_energy_wh')} vs {dev.get('battery_energy_wh')} Wh")
check("model family is iPhone 17 (owner-confirmed)",
      dev.get("model") == "iPhone 17")
check("nameplate ceiling equals iPhone 17 series 1-199 band",
      int(round(dev["charge_limit_voltage_v"] * 1000)) == 4500)

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

print("\n=== reference device (cross-check only) ===")
ref = json.load(open(os.path.join(ROOT, "devices/reference-01/reference.json"),
                     encoding="utf-8"))
check("reference: cycles >= 1000 band", ref["cycle_count"] >= 1000,
      str(ref["cycle_count"]))
check("reference: VacVoltageLimit 4340 mV",
      ref["vac_voltage_limit_mv"] == 4340)
np = ref["nameplate"]
check("reference: battery energy = nominal V x rated mAh",
      abs(np["nominal_voltage_v"] * np["rated_capacity_mah"] / 1000 -
          np["battery_energy_wh"]) < 0.005,
      f"{np['nominal_voltage_v']}V x {np['rated_capacity_mah']}mAh "
      f"= {np['nominal_voltage_v']*np['rated_capacity_mah']/1000:.3f}Wh")
# Forward prediction from the known nameplate using the node table:
# -20mV at 200/250/300, extra -50mV at >=1000.
predicted = int(round((np["charge_limit_voltage_v"] - 0.02 * 3 - 0.05) * 1000))
check("reference: nameplate minus node steps equals measured VacVoltageLimit",
      predicted == ref["vac_voltage_limit_mv"],
      f"{np['charge_limit_voltage_v']}V - 0.02x3 - 0.05 = {predicted} mV")
check("reference: nameplate voltage equals lifetime peak pack voltage",
      int(round(np["charge_limit_voltage_v"] * 1000)) ==
      ref["maximum_pack_voltage_mv"])
# Back-project the ladder: >=1000 is -110mV from the first band.
inferred_first = ref["vac_voltage_limit_mv"] + 110
check("reference: inferred 1-199 band equals lifetime peak pack voltage",
      inferred_first == ref["maximum_pack_voltage_mv"],
      f"{inferred_first} mV vs {ref['maximum_pack_voltage_mv']} mV")
health_gap = ref["maximum_capacity_percent_reported"] - \
    ref["nominal_charge_capacity_mah"] / np["rated_capacity_mah"] * 100
check("reference: Apple health differs from NCC/nameplate by >10pp",
      health_gap > 10, f"gap {health_gap:.2f} pp")

print("\n=== reference-02 (nameplate + gauge snapshot) ===")
r2 = json.load(open(os.path.join(ROOT, "devices/reference-02/reference.json"),
                    encoding="utf-8"))
n2 = r2["nameplate"]
check("ref-02: battery energy = nominal V x rated mAh",
      abs(n2["nominal_voltage_v"] * n2["rated_capacity_mah"] / 1000 -
          n2["battery_energy_wh"]) < 0.005,
      f"{n2['nominal_voltage_v']}V x {n2['rated_capacity_mah']}mAh "
      f"= {n2['nominal_voltage_v']*n2['rated_capacity_mah']/1000:.3f}Wh")
check("ref-02: cell energy exceeds pack energy",
      n2["cell_energy_wh"] > n2["battery_energy_wh"])
check("ref-02: same voltage platform as reference-01",
      n2["nominal_voltage_v"] == np["nominal_voltage_v"] and
      n2["charge_limit_voltage_v"] == np["charge_limit_voltage_v"])
check("ref-02: capacity/energy ratios agree with reference-01",
      abs(n2["rated_capacity_mah"] / np["rated_capacity_mah"] -
          n2["battery_energy_wh"] / np["battery_energy_wh"]) < 0.001,
      f"{n2['rated_capacity_mah']/np['rated_capacity_mah']:.4f}x vs "
      f"{n2['battery_energy_wh']/np['battery_energy_wh']:.4f}x")
ladder = r2["predicted_voltage_ladder_mv"]
check("ref-02: predicted >=1000 band matches reference-01 measured",
      ladder[">=1000"] == ref["vac_voltage_limit_mv"])
g2 = r2["gauge"]
check("ref-02: gauge cycle count is high", g2["cycle_count"] > 1000,
      str(g2["cycle_count"]))
check("ref-02: peak pack voltage ~= 4.45V nameplate",
      abs(g2["maximum_pack_voltage_mv"] -
          n2["charge_limit_voltage_v"] * 1000) <= 5,
      f"{g2['maximum_pack_voltage_mv']} mV vs "
      f"{int(n2['charge_limit_voltage_v']*1000)} mV")
check("ref-02: VacVoltageLimit explicitly absent",
      r2["vac_voltage_limit_available"] is False)
check("ref-02: battery status recorded as original (owner-confirmed)",
      "original" in r2["battery_status"].lower() and
      g2["battery_serial_changed"] is False)
check("ref-02: OriginalBattery=0 semantics left unconfirmed",
      g2["original_battery"] == 0 and
      "unconfirmed" in str(r2["caveats"]).lower() + r2["battery_status"].lower())
check("ref-02: NCC/nameplate gap reverses sign (unexplained)",
      g2["maximum_capacity_percent_reported"] -
      g2["nominal_charge_capacity_mah"] / n2["rated_capacity_mah"] * 100 < 0,
      f"{g2['maximum_capacity_percent_reported'] - g2['nominal_charge_capacity_mah']/n2['rated_capacity_mah']*100:+.2f} pp")

print("\n=== voltage/capacity A-B experiment ===")
ab = json.load(open(os.path.join(ROOT, "docs/voltage-capacity-experiment.json"),
                    encoding="utf-8"))
ca, cb = ab["conditions"]
check("A-B: same battery (Qmax unchanged)",
      ca["qmax_mah"] == cb["qmax_mah"])
check("A-B: voltage span is 110 mV",
      ca["voltage_limit_mv"] - cb["voltage_limit_mv"] == 110)
check("A-B: capacity drop matches measured slope",
      abs((ca["actual_capacity_mah"] - cb["actual_capacity_mah"]) -
          ab["measured_slope"]["delta_actual_capacity_mah"] * -1) < 1e-9)
slope = (ca["actual_capacity_mah"] - cb["actual_capacity_mah"]) / \
        (ca["voltage_limit_mv"] - cb["voltage_limit_mv"])
check("A-B: 1.46 pp per 20 mV node",
      abs(slope * 20 / ab["device_under_test"]["design_capacity_mah"] * 100
          - 1.46) < 0.01,
      f"{slope*20/ab['device_under_test']['design_capacity_mah']*100:.3f} pp")
check("A-B: span matches iphone-01 top to >=1000 band",
      ca["voltage_limit_mv"] == 4500 and cb["voltage_limit_mv"] == 4390)

print("\n=== iphone-01-only forecast ===")
fc = json.load(open(os.path.join(ROOT, "docs/iphone17-forecast.json"),
                    encoding="utf-8"))
check("forecast: base is 208 cycles / 99.106%",
      fc["base"]["cycle"] == 208 and abs(fc["base"]["health_pct"] - 99.106) < 0.001)
check("forecast: other devices and 80% spec excluded",
      any("reference-01" in x for x in fc["not_used"]) and
      any("reference-02" in x for x in fc["not_used"]) and
      any("80%" in x for x in fc["not_used"]))
check("forecast: current usage 1.30 cycles/day = 4800 mAh/day",
      fc["current_usage"]["cycles_per_day"] == 1.30 and
      fc["current_usage"]["mah_per_day_throughput"] == 4800)
check("forecast: old inflated rate explicitly withdrawn",
      "withdrawn" in str(fc["current_usage"]["previous_rate_withdrawn"]).lower() or
      "biased high" in str(fc["current_usage"]["previous_rate_withdrawn"]).lower())
check("forecast: plateau/step in mAh",
      fc["current_usage"]["plateau_wear_mah_per_day"] == 0.176 and
      fc["current_usage"]["lockin_mah_per_20mv_node"] == 15.9)
check("forecast: 250 node is 2026-12-17 / 4460 mV / 3637 mAh",
      fc["nodes"][0]["date"] == "2026-12-17" and
      fc["nodes"][0]["vac_voltage_limit_mv"] == 4460 and
      abs(fc["nodes"][0]["ncc_mah"] - 3637.4) < 0.2)
check("forecast: 1000 cycles ≈ 94.916% / 3504 mAh / 47.6 mAh lock-in",
      abs(fc["at_1000_cycles"]["ncc_health_pct"] - 94.916) < 0.01 and
      abs(fc["at_1000_cycles"]["ncc_mah"] - 3504.3) < 0.2 and
      abs(fc["at_1000_cycles"]["reversible_lockin_mah"] - 47.6) < 0.2)
check("forecast: sensitivity covers 6 usage windows",
      len(fc["sensitivity_to_usage_rate"]) == 6)
frows = load("docs/iphone17-forecast.csv")
check("forecast: CSV has real mAh columns",
      "ncc_mah" in frows[0] and "chemical_only_mah" in frows[0])
check("forecast: CSV is monotonic non-increasing in health",
      all(float(a["ncc_health_pct"]) >= float(b["ncc_health_pct"])
          for a, b in zip(frows, frows[1:])))
check("forecast: first CSV row matches base",
      float(frows[0]["ncc_health_pct"]) == 99.106 and
      int(frows[0]["cycle"]) == 208 and float(frows[0]["ncc_mah"]) == 3659.0)

print("\n" + ("ALL CHECKS PASSED" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
