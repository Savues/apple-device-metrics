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
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import RATED, derive  # noqa: E402

P = derive()
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

# The dataset's defining collection condition: iOS Charge Limit is set to
# 80% as a safety net, but the owner unplugs before 80%, so NO full charge
# (and no completed Apple calibration charge) occurs anywhere in the window.
# If a future import breaks this, every conclusion in
# docs/shallow-charging-accuracy.md must be re-examined.
max_soc_end = max(int(r["soc_end"]) for r in sess)
check("no session reaches a full charge (soc_end <= 81)",
      max_soc_end <= 81, f"max soc_end={max_soc_end}")
check("no session near full (soc_end < 95)",
      all(int(r["soc_end"]) < 95 for r in sess), f"max soc_end={max_soc_end}")

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

# The 6-row health export and the daily analytics archive are two independent
# sources. Where they overlap in date they must agree; the archive is allowed
# (and expected) to be newer than the sparse export.
if snaps:
    export_last = health[-1]
    overlap = next((s for s in snaps
                    if s["date"] == export_last["date"]), None)
    check("export/analytics overlap: cycle count agrees",
          overlap is not None and
          overlap["cycle_count"] == int(export_last["cycle_count"]))
    check("export/analytics overlap: NCC agrees",
          overlap is not None and
          overlap["nominal_charge_capacity_mah"] ==
          int(export_last["nominal_capacity_mah"]))
    check("no calibration full charge: all DailyMaxSoc <= 81%",
          all(s["daily_max_soc_pct"] <= 81 for s in snaps),
          str(max(s["daily_max_soc_pct"] for s in snaps)))
    check("export/analytics overlap: DailyMinSoc agrees",
          overlap is not None and
          overlap["daily_min_soc_pct"] == int(export_last["min_soc_pct"]))
    check("analytics archive extends past the export",
          snaps[-1]["date"] > export_last["date"] and
          snaps[-1]["cycle_count"] > int(export_last["cycle_count"]))
    check("analytics archive has at least 8 snapshots",
          len(snaps) >= 8, str(len(snaps)))
    check("cycle count never decreases across snapshots",
          all(b["cycle_count"] >= a["cycle_count"]
              for a, b in zip(snaps, snaps[1:])))
    # Only day-to-day pairs inside one voltage band measure jitter; a gap or
    # a node crossing is allowed to move NCC by a whole step.
    daily = [(a, b) for a, b in zip(snaps, snaps[1:])
             if (date.fromisoformat(b["date"]) -
                 date.fromisoformat(a["date"])).days <= 2 and
             a["vac_voltage_limit_mv"] == b["vac_voltage_limit_mv"]]
    check("NCC daily jitter stays within +/-2 mAh (same band, <=2 days apart)",
          all(abs(b["nominal_charge_capacity_mah"] -
                  a["nominal_charge_capacity_mah"]) <= 2 for a, b in daily),
          f"{len(daily)} pairs")

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
check("forecast: other devices and 80% spec excluded",
      any("reference-01" in x for x in fc["not_used"]) and
      any("reference-02" in x for x in fc["not_used"]) and
      any("80%" in x for x in fc["not_used"]))
check("forecast: usage rate equals diary throughput",
      fc["current_usage"]["cycles_per_day"] == P["diary"]["cycles_per_day"] and
      fc["current_usage"]["mah_per_day_throughput"] ==
      round(P["diary"]["mah_per_day"]),
      f"{fc['current_usage']['cycles_per_day']}/day")
check("forecast: diary total matches charging-summary.json",
      P["diary"]["total_charged_pct"] ==
      json.load(open(os.path.join(ROOT, "docs/charging-summary.json")))
      ["total_charged_pct"])
check("forecast: gauge cross-check within 10% of diary rate",
      abs(P["rates"]["gauge_regression"] / P["diary"]["cycles_per_day"] - 1)
      < 0.10,
      f"{P['rates']['gauge_regression']} vs {P['diary']['cycles_per_day']}")
check("forecast: old inflated rate explicitly withdrawn",
      "withdrawn" in str(fc["current_usage"]["previous_rate_withdrawn"]).lower() or
      "biased high" in str(fc["current_usage"]["previous_rate_withdrawn"]).lower())
check("forecast: plateau/step derived from health export",
      fc["current_usage"]["plateau_wear_mah_per_day"] ==
      round(P["plateau_pp_per_day"] / 100 * RATED, 3) and
      fc["current_usage"]["lockin_mah_per_20mv_node"] ==
      round(P["step_pp_per_node"] / 100 * RATED, 1),
      f"{P['plateau_pp_per_day']} pp/day, {P['step_pp_per_node']} pp/node")
check("forecast: plateau uses >=3 non-step export segments",
      P["plateau_segments"] >= 3, str(P["plateau_segments"]))
latest = snaps[-1]
check("forecast: base is the latest analytics snapshot",
      fc["base"]["date"] == latest["date"] and
      fc["base"]["cycle"] == latest["cycle_count"] and
      fc["base"]["ncc_mah"] == latest["nominal_charge_capacity_mah"],
      f"{fc['base']['date']} / {fc['base']['cycle']} / {fc['base']['ncc_mah']}")
LADDER = {250: 4460, 300: 4440, 1000: 4390}
future = [n for n in LADDER if n > fc["base"]["cycle"]]
check("forecast: node table = future nodes on the 4460/4440/4390 ladder",
      [(n["cycle"], n["vac_voltage_limit_mv"]) for n in fc["nodes"]] ==
      [(n, LADDER[n]) for n in future])
check("forecast: 1000-cycle lock-in = one step per future node",
      abs(fc["at_1000_cycles"]["reversible_lockin_mah"] -
          len([n for n in future if n <= 1000]) *
          P["step_pp_per_node"] / 100 * RATED) < 0.2,
      f"{len(future)} future nodes")

# The committed outputs must equal a fresh run of forecast.py, so a new
# snapshot cannot be imported without regenerating the forecast.
import subprocess, tempfile, shutil  # noqa: E402
with tempfile.TemporaryDirectory() as tmp:
    for d in ("scripts", "devices", "docs"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(tmp, d))
    subprocess.run([sys.executable, os.path.join(tmp, "scripts/forecast.py")],
                   check=True, stdout=subprocess.DEVNULL)
    stale_out = [f for f in ("iphone17-forecast.csv", "iphone17-forecast.json",
                             "iphone17-forecast.svg")
                 if open(os.path.join(tmp, "docs", f), "rb").read() !=
                 open(os.path.join(ROOT, "docs", f), "rb").read()]
check("forecast: committed outputs equal a fresh forecast.py run",
      not stale_out, "stale: " + ", ".join(stale_out) if stale_out else "")
check("forecast: sensitivity covers 6 usage windows",
      len(fc["sensitivity_to_usage_rate"]) == 6)

# Chart labels must not collide. The x axis starts at the base cycle, so the
# early nodes (250/300) land close together: their labels have to be stacked.
import forecast  # noqa: E402  (module has a main guard, importing is safe)
svg = open(os.path.join(ROOT, "docs/iphone17-forecast.svg"), encoding="utf-8").read()
labels = []
for m in re.finditer(r'<text x="([\d.]+)" y="([\d.]+)"([^>]*)>(.*?)</text>', svg):
    x, y, attrs, txt = float(m.group(1)), float(m.group(2)), m.group(3), m.group(4)
    size = float(re.search(r'font-size="([\d.]+)"', attrs).group(1)) \
        if 'font-size="' in attrs else 12.0
    w = forecast.text_width(txt, size)
    if 'text-anchor="end"' in attrs:
        x -= w
    elif 'text-anchor="middle"' in attrs:
        x -= w / 2
    labels.append((x, y - 0.9 * size, w, 1.2 * size, txt))
clashes = [f"{a[4]!r} x {b[4]!r}"
           for i, a in enumerate(labels) for b in labels[i + 1:]
           if a[0] < b[0] + b[2] - 1 and b[0] < a[0] + a[2] - 1
           and a[1] < b[1] + b[3] - 1 and b[1] < a[1] + a[3] - 1]
check("forecast: chart labels do not overlap",
      not clashes, "; ".join(clashes) if clashes else f"{len(labels)} labels")
frows = load("docs/iphone17-forecast.csv")
check("forecast: CSV has real mAh columns",
      "ncc_mah" in frows[0] and "chemical_only_mah" in frows[0])
check("forecast: CSV is monotonic non-increasing in health",
      all(float(a["ncc_health_pct"]) >= float(b["ncc_health_pct"])
          for a, b in zip(frows, frows[1:])))
check("forecast: first CSV row matches base",
      int(frows[0]["cycle"]) == latest["cycle_count"] and
      float(frows[0]["ncc_mah"]) == float(latest["nominal_charge_capacity_mah"]))

print("\n=== docs: marked numbers match the data (sync_docs.py) ===")
sync = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/sync_docs.py"), "--check"],
                      capture_output=True, text=True)
check("docs: every <!--v:--> / <!--b:--> marker is up to date", sync.returncode == 0,
      (sync.stdout + sync.stderr).strip())
for readme in ("README.md", "README.zh.md"):
    text = open(os.path.join(ROOT, readme), encoding="utf-8").read()
    check(f"{readme}: at-a-glance row is marker-driven",
          all(f"<!--v:{k}-->" in text for k in ("base_cycle", "base_ncc", "base_health_two", "apple", "vac", "rate")))

print("\n=== pre-registered predictions ===")
pr = json.load(open(os.path.join(ROOT, "docs/predictions.json"),
                    encoding="utf-8"))["predictions"]
check("predictions: ids unique",
      len({p["id"] for p in pr}) == len(pr))
# Ex-ante: every prediction must be registered at a cycle below its node.
check("predictions: registered before the 250 node",
      all(p["registered_at_cycle"] < 250 for p in pr))
pre = [s for s in snaps if s["cycle_count"] < 250]
post = [s for s in snaps if s["cycle_count"] >= 250]
first = post[0] if post else None
for p in pr:
    if first is None:
        outcome = "PENDING (no snapshot at >=250 cycles yet)"
    elif p.get("observe_only"):
        outcome = f"OBSERVED {first['maximum_capacity_percent_reported']}"
    elif p["id"] == "node-250-voltage":
        v = first["vac_voltage_limit_mv"]
        outcome = ("HIT" if abs(v - p["expected"]) <= p["tolerance"]
                   else "MISS") + f" ({v} mV)"
    elif p["id"] == "node-250-ncc-step":
        d = pre[-1]["nominal_charge_capacity_mah"] - \
            first["nominal_charge_capacity_mah"]
        outcome = ("HIT" if abs(d - p["expected"]) <= p["tolerance"]
                   else "MISS") + f" ({d} mAh, {pre[-1]['date']} -> {first['date']})"
    elif p["id"] == "node-250-date":
        lo, hi = p["expected_range"]
        outcome = ("HIT" if lo <= first["date"] <= hi else "MISS") + \
            f" ({first['date']})"
    else:
        outcome = "UNSCORED (no scorer for this id)"
    print(f"  NOTE  {p['id']}: {outcome}")

print("\n" + ("ALL CHECKS PASSED" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
