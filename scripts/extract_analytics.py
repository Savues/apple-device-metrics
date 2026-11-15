#!/usr/bin/env python3
"""Extract a WHITELIST of battery-health fields from an iOS analytics .ips file.

iOS daily analytics files are NDJSON (bug_type 211). The first line is a
header; the rest are aggregate records with a `name` and a `message` dict.
They contain deviceId / UUID / carrier / country / incident_id and other
identifiers. NONE of those are emitted here: only explicitly whitelisted
numeric battery fields are copied, and the output is a flat, de-identified
JSON object.

Usage:
    python3 extract_analytics.py <file.ips> [-o out.json] [--append CSV]

The --append CSV mode writes one row into a de-identified per-snapshot table.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The two aggregate records that matter for battery health.
BATTERY_RECORD = "BatteryConfigValueHistogramFinal_V2"
VOLTAGE_RECORD = "VacVoltageLimit"

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
    "average_temperature_c": "AverageTemperature",
    "battery_health_metric": "BatteryHealthMetric",
    "weighted_ra": "WeightedRa",
    "total_operating_time_h": "TotalOperatingTime",
}
VOLTAGE_FIELD = "last_value_VacVoltageLimit"

CSV_COLS = ["date", "cycle_count", "apple_raw_max_capacity_mah",
            "nominal_charge_capacity_mah", "nominal_health_pct",
            "vac_voltage_limit_mv", "daily_min_soc_pct", "daily_max_soc_pct",
            "cycle_count_last_qmax", "qmax_cell0_mah", "ios_version"]


def parse(path):
    header, battery, voltage = None, None, None
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
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
    if not header or not battery or not voltage:
        missing = [n for n, v in (("header", header), (BATTERY_RECORD, battery),
                                  (VOLTAGE_RECORD, voltage)) if not v]
        raise SystemExit("missing required records: " + ", ".join(missing))
    return header, battery, voltage


def extract(path, rated=3692):
    header, bat, volt = parse(path)
    ts = header["timestamp"]                     # "2026-11-15 08:00:00.00 +0800"
    date = ts.split()[0]
    ios = header.get("os_version", "").replace("iPhone OS ", "").split(" (")[0]

    out = {"date": date, "ios_version": ios}
    for dst, src in FIELDS.items():
        v = bat.get("last_value_" + src)
        if v is not None:
            out[dst] = v
    out["vac_voltage_limit_mv"] = volt.get(VOLTAGE_FIELD)
    out["vac_voltage_limit_v"] = round(out["vac_voltage_limit_mv"] / 1000, 3)

    ncc = out.get("nominal_charge_capacity_mah")
    if ncc:
        out["nominal_health_pct"] = round(ncc / rated * 100, 3)
        out["health_denominator_mah"] = rated
    out["rated_capacity_mah"] = rated
    return out


def append_csv(path, rec):
    row = {k: rec.get(k, "") for k in CSV_COLS}
    exists = os.path.exists(path) and os.path.getsize(path) > 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        if not exists:
            w.writeheader()
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--append")
    ap.add_argument("--rated", type=int, default=3692)
    args = ap.parse_args()

    rec = extract(args.input, args.rated)
    text = json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)
    if args.append:
        append_csv(args.append, rec)
        print(f"appended -> {args.append}", file=sys.stderr)

    # Guard: never let identifiers through
    banned = ("deviceId", "uuid", "incident_id", "configUuid", "carrier",
              "Country", "productSku", "serial", "Serial", "ChemID")
    for b in banned:
        if b in text:
            raise SystemExit(f"REFUSING OUTPUT: identifier-like key {b!r} present")


if __name__ == "__main__":
    main()
