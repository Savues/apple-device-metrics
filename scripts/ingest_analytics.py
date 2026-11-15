#!/usr/bin/env python3
"""Ingest new iOS analytics health snapshots into the dataset.

Accepts the tab/space/CSV-separated table that the analytics export produces,
with or without a header row:

    Date        Cycl.  Raw Capacity  Nominal Capacity  Nominal Health  iOS     Hrs Soc  Min Soc
    15-11-2026  208    3692          3659              99.11%          26.4.2  0        39%

Rules:
  - dates may be DD-MM-YYYY (source) or YYYY-MM-DD (already normalised)
  - percent signs are stripped
  - duplicate dates are NOT silently overwritten; use --replace to update them
  - health is recomputed from nominal/3692 and cross-checked against the input
  - rows are appended in ascending date order
  - cycle-node crossings (200/250/300/1000) are reported explicitly

Usage:
    python3 scripts/ingest_analytics.py <input.txt>
    python3 scripts/ingest_analytics.py <input.txt> --replace
    python3 scripts/ingest_analytics.py <input.txt> --dry-run
"""
import argparse
import csv
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "devices/iphone-01/health-samples.csv")
RATED = 3692
COLS = ["date", "cycle_count", "raw_capacity_mah", "nominal_capacity_mah",
        "nominal_health_pct", "ios_version", "hrs_soc", "min_soc_pct"]
NODES = (200, 250, 300, 1000)


def parse_date(s):
    s = s.strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_row(parts, lineno):
    if len(parts) < 8:
        return None, f"line {lineno}: only {len(parts)} fields (need 8)"
    d = parse_date(parts[0])
    if not d:
        return None, f"line {lineno}: bad date {parts[0]!r}"

    def num(x):
        return float(re.sub(r"[%,\s]", "", x))

    try:
        cyc = int(num(parts[1]))
        raw = int(num(parts[2]))
        nom = int(num(parts[3]))
        health = num(parts[4])
        ios = parts[5].strip()
        hrs = num(parts[6])
        minsoc = num(parts[7])
    except (ValueError, IndexError) as e:
        return None, f"line {lineno}: numeric parse failed: {e}"

    calc = nom / RATED * 100
    if abs(calc - health) > 0.02:
        return None, (f"line {lineno}: health {health:.2f}% != "
                      f"nominal/{RATED} = {calc:.3f}%")
    return {
        "date": d,
        "cycle_count": str(cyc),
        "raw_capacity_mah": str(raw),
        "nominal_capacity_mah": str(nom),
        "nominal_health_pct": f"{health:.2f}",
        "ios_version": ios,
        "hrs_soc": str(int(hrs)),
        "min_soc_pct": str(int(minsoc)),
    }, None


def read_existing():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def split(s):
    s = s.strip()
    if not s or s.startswith("#"):
        return []
    if "\t" in s:
        return [x.strip() for x in s.split("\t") if x.strip()]
    if "," in s and re.search(r"\d{4}-\d{2}-\d{2}", s):
        return [x.strip() for x in s.split(",")]
    return re.split(r"\s{2,}|\s+", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--replace", action="store_true",
                    help="allow overwriting an existing date")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    incoming, skipped = [], []
    for n, line in enumerate(open(args.input, encoding="utf-8"), 1):
        parts = split(line)
        if not parts:
            continue
        if parse_date(parts[0]) is None:      # header / prose
            skipped.append((n, "header or non-data line"))
            continue
        row, err = parse_row(parts, n)
        if err:
            skipped.append((n, err))
        else:
            incoming.append(row)

    if not incoming:
        print("No valid rows found.", file=sys.stderr)
        for s in skipped:
            print(" ", s, file=sys.stderr)
        sys.exit(1)

    existing = read_existing()
    by_date = {r["date"]: r for r in existing}
    new_rows, replaced = [], []
    for r in incoming:
        if r["date"] in by_date:
            if args.replace:
                replaced.append(r["date"])
                by_date[r["date"]] = r
            else:
                skipped.append((r["date"], "duplicate date (use --replace)"))
        else:
            new_rows.append(r)
            by_date[r["date"]] = r

    merged = sorted(by_date.values(), key=lambda r: r["date"])
    print(f"input rows: {len(incoming)}  |  new: {len(new_rows)}  "
          f"replaced: {len(replaced)}  skipped: {len(skipped)}")
    for s in skipped:
        print("  skipped:", s, file=sys.stderr)

    if not args.dry_run:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(merged)
        print(f"wrote {len(merged)} rows -> {os.path.relpath(CSV_PATH, ROOT)}")

    # report deltas for the newest rows
    print("\n=== new snapshots ===")
    for r in sorted(new_rows, key=lambda x: x["date"]):
        prev = [x for x in merged if x["date"] < r["date"]]
        if not prev:
            print(f"  {r['date']}  cyc={r['cycle_count']}  "
                  f"nom={r['nominal_capacity_mah']}mAh  {r['nominal_health_pct']}%")
            continue
        p = prev[-1]
        dcyc = int(r["cycle_count"]) - int(p["cycle_count"])
        dnom = int(r["nominal_capacity_mah"]) - int(p["nominal_capacity_mah"])
        dh = float(r["nominal_health_pct"]) - float(p["nominal_health_pct"])
        days = (datetime.fromisoformat(r["date"]) -
                datetime.fromisoformat(p["date"])).days
        crossed = [n for n in NODES
                   if int(p["cycle_count"]) < n <= int(r["cycle_count"])]
        tag = f"  *** CROSSED NODE(S): {crossed} ***" if crossed else ""
        print(f"  {r['date']}  +{days}d  +{dcyc} cyc  "
              f"nom {dnom:+d} mAh  health {dh:+.2f} pp{tag}")

    if new_rows and not args.dry_run:
        print("\nNext: python3 scripts/verify.py && review docs/findings.md")


if __name__ == "__main__":
    main()
