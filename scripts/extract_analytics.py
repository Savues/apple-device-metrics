#!/usr/bin/env python3
"""Extract a WHITELIST of battery-health fields from iOS analytics .ips files.

iOS daily analytics files are NDJSON (bug_type 211). The first line is a
header; the rest are aggregate records with a `name` and a `message` dict.
They contain deviceId / UUID / carrier / country / incident_id and other
identifiers. NONE of those are emitted here: only explicitly whitelisted
numeric battery fields are copied.

One file per date is archived as devices/iphone-01/analytics/<date>.json and
a combined devices/iphone-01/analytics-timeline.csv is rebuilt each run.

Usage:
    # archive one or many files, rebuild timeline, print node check
    python3 extract_analytics.py --archive FILE [FILE ...]

    # just print one file's whitelisted fields to stdout
    python3 extract_analytics.py FILE

    # write one file's fields to a specific path
    python3 extract_analytics.py -o out.json FILE
"""
import argparse
import csv
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_DIR = os.path.join(ROOT, "devices", "iphone-01", "analytics")
TIMELINE = os.path.join(ROOT, "devices", "iphone-01", "analytics-timeline.csv")

BATTERY_RECORD = "BatteryConfigValueHistogramFinal_V2"
VOLTAGE_RECORD = "VacVoltageLimit"
VOLTAGE_FIELD = "last_value_VacVoltageLimit"

# Whitelist. Everything else (deviceId, uuid, configUuid, incident_id,
# carrier, country, serial-related flags, ChemID, firmware version...) is
# deliberately dropped.
FIELDS = {
    "cycle_count": "CycleCount",
    "apple_raw_max_capacity_mah": "AppleRawMaxCapacity",
    "nominal_charge_capacity_mah": "NominalChargeCapacity",
    "daily_min_soc_pct": "DailyMinSoc",
    "daily_max_soc_pct": "DailyMaxSoc",
    "maximum_capacity_percent_reported": "MaximumCapacityPercent",
    "maximum_pack_voltage_mv": "MaximumPackVoltage",
    "minimum_pack_voltage_mv": "MinimumPackVoltage",
    "maximum_fcc_mah": "MaximumFCC",
    "minimum_fcc_mah": "MinimumFCC",
    "ncc_max_mah": "NCCMax",
    "ncc_min_mah": "NCCMin",
    "qmax_cell0_mah": "QmaxCell0",
    "qmax_max_mah": "MaximumQmax",
    "qmax_min_mah": "MinimumQmax",
    "cycle_count_last_qmax": "CycleCountLastQmax",
    "gauge_update_time_utc": "UpdateTime",
    "average_temperature_c": "AverageTemperature",
    "battery_health_metric": "BatteryHealthMetric",
    "weighted_ra": "WeightedRa",
    "total_operating_time_h": "TotalOperatingTime",
}

TIMELINE_COLS = ["date", "cycle_count", "vac_voltage_limit_mv",
                 "expected_voltage_mv", "node_band", "voltage_matches_band",
                 "nominal_charge_capacity_mah", "apple_raw_max_capacity_mah",
                 "nominal_health_pct", "daily_min_soc_pct", "daily_max_soc_pct",
                 "cycle_count_last_qmax", "qmax_cell0_mah",
                 "gauge_update_time_utc", "ios_version"]

# iPhone 17 series, third-party table (see docs/voltage-nodes.md).
# (upper_bound_exclusive, limit_mV, label)
BANDS = [(200, 4500, "1-199"), (250, 4480, "200-249"),
         (300, 4460, "250-299"), (1000, 4440, "300-999"),
         (10 ** 9, 4390, ">=1000")]

BANNED = ("deviceId", "uuid", "incident_id", "configUuid", "carrier",
          "Country", "productSku", "serial", "Serial", "ChemID")


def expected_voltage(cycles):
    for upper, mv, label in BANDS:
        if cycles < upper:
            return mv, label
    return None, "unknown"


def parse(path):
    header, battery, voltage = None, None, None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("bug_type") and not header:
                header = d
            name = d.get("name")
            if name == BATTERY_RECORD:
                battery = d.get("message", {})
            elif name == VOLTAGE_RECORD:
                voltage = d.get("message", {})
    missing = [n for n, v in (("header", header), (BATTERY_RECORD, battery),
                              (VOLTAGE_RECORD, voltage)) if not v]
    if missing:
        raise SystemExit(f"{path}: missing required records: {', '.join(missing)}")
    return header, battery, voltage


def extract(path, rated=3692):
    header, bat, volt = parse(path)
    ts = header["timestamp"]                    # "2026-11-15 08:00:00.00 +0800"
    date = ts.split()[0]
    ios = header.get("os_version", "").replace("iPhone OS ", "").split(" (")[0]

    out = {"date": date, "ios_version": ios}
    for dst, src in FIELDS.items():
        v = bat.get("last_value_" + src)
        if v is not None:
            out[dst] = v
    mv = volt.get(VOLTAGE_FIELD)
    if mv is None:
        raise SystemExit(f"{path}: no {VOLTAGE_FIELD}")
    out["vac_voltage_limit_mv"] = mv
    out["vac_voltage_limit_v"] = round(mv / 1000, 3)

    ncc = out.get("nominal_charge_capacity_mah")
    if ncc:
        out["nominal_health_pct"] = round(ncc / rated * 100, 3)
        out["health_denominator_mah"] = rated
    out["rated_capacity_mah"] = rated
    u = out.get("gauge_update_time_utc")
    if isinstance(u, (int, float)) and u > 0:
        out["gauge_update_time_utc"] = datetime.fromtimestamp(
            u, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return out


def guard(text):
    for b in BANNED:
        if b in text:
            raise SystemExit(f"REFUSING OUTPUT: identifier-like key {b!r} present")


def archive(rec):
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    path = os.path.join(ARCHIVE_DIR, rec["date"] + ".json")
    existed = os.path.exists(path)
    text = json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True)
    guard(text)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return path, existed


def load_archive():
    out = []
    if os.path.isdir(ARCHIVE_DIR):
        for name in sorted(os.listdir(ARCHIVE_DIR)):
            if name.endswith(".json"):
                with open(os.path.join(ARCHIVE_DIR, name), encoding="utf-8") as f:
                    out.append(json.load(f))
    return sorted(out, key=lambda r: r["date"])


def build_timeline(records):
    with open(TIMELINE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TIMELINE_COLS)
        w.writeheader()
        for r in records:
            cycles = r.get("cycle_count")
            mv = r.get("vac_voltage_limit_mv")
            exp, band = expected_voltage(cycles) if cycles is not None else (None, "unknown")
            w.writerow({
                "date": r.get("date", ""),
                "cycle_count": cycles,
                "vac_voltage_limit_mv": mv,
                "expected_voltage_mv": exp,
                "node_band": band,
                "voltage_matches_band": (mv == exp) if exp else "",
                "nominal_charge_capacity_mah": r.get("nominal_charge_capacity_mah"),
                "apple_raw_max_capacity_mah": r.get("apple_raw_max_capacity_mah"),
                "nominal_health_pct": r.get("nominal_health_pct"),
                "daily_min_soc_pct": r.get("daily_min_soc_pct"),
                "daily_max_soc_pct": r.get("daily_max_soc_pct"),
                "cycle_count_last_qmax": r.get("cycle_count_last_qmax"),
                "qmax_cell0_mah": r.get("qmax_cell0_mah"),
                "gauge_update_time_utc": r.get("gauge_update_time_utc", ""),
                "ios_version": r.get("ios_version", ""),
            })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="+", help="one or more .ips analytics files")
    ap.add_argument("-o", "--output", help="write a single JSON (one input only)")
    ap.add_argument("--archive", action="store_true",
                    help="archive each file by date and rebuild the timeline CSV")
    ap.add_argument("--rated", type=int, default=3692)
    args = ap.parse_args()

    if args.output and len(args.input) > 1:
        raise SystemExit("--output accepts exactly one input file")

    for src in args.input:
        rec = extract(src, args.rated)
        text = json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True)
        guard(text)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        elif args.archive:
            path, existed = archive(rec)
            exp, band = expected_voltage(rec["cycle_count"])
            print(f"{'updated' if existed else 'added':>7}  "
                  f"{os.path.relpath(path, ROOT)}  "
                  f"cycle={rec['cycle_count']:<4} "
                  f"VacVoltageLimit={rec['vac_voltage_limit_mv']}mV "
                  f"(expected {exp}mV / {band})")
        else:
            print(text)

    if args.archive:
        records = load_archive()
        build_timeline(records)
        print(f"\nrebuilt devices/iphone-01/analytics-timeline.csv "
              f"with {len(records)} snapshots")
        for r in records:
            exp, band = expected_voltage(r["cycle_count"])
            ok = "OK " if r["vac_voltage_limit_mv"] == exp else "?? "
            print(f"  {ok} {r['date']}  cyc={r['cycle_count']:<4} "
                  f"{r['vac_voltage_limit_mv']}mV  band={band}")


if __name__ == "__main__":
    main()
