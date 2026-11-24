# Methodology

## Sources

### Health snapshots

`devices/iphone-01/health-samples.csv` — 6 rows extracted from **iOS
analytics snapshots generated at 08:00 local time** on each sample date.
These are system-generated daily aggregates, not manual readings and not
live gauge queries. Column names in the source export:

```
Date  Cycl.  Raw Capacity  Nominal Capacity  Nominal Health  iOS  Hrs Soc  Min Soc
```

| Field | Unit | Meaning |
|-------|------|---------|
| `date` | DD-MM-YYYY | date of the 08:00 analytics snapshot |
| `cycle_count` | cycles | cumulative equivalent full charge cycles |
| `raw_capacity_mah` | mAh | raw gauge capacity estimate; drifts (3742→3692) |
| `nominal_capacity_mah` | mAh | nominal capacity used for the health percentage |
| `nominal_health_pct` | % | reported maximum capacity |
| `ios_version` | — | OS build at snapshot time (26.4.2 throughout) |
| `hrs_soc` | — | source column; always 0; **meaning unknown** |
| `min_soc_pct` | % | `Min Soc` in the source export (18–39%). Interpreted as the minimum SOC in that snapshot period — **inferred from the column name, not documented**; definitely **not** the SOC at read time |

Because these are 08:00 aggregates, day boundaries do not align with the
charging diary's calendar days — this is part of why the cycle cross-check
in `findings.md` lands at 0.93–1.10 rather than exactly 1.00.

Precisely (confirmed from two consecutive files): a file whose header reads
`YYYY-MM-DD 08:00:00 +0800` carries metadata `startTimestamp` of the
**previous day** at `00:00:00Z` (= 08:00 +0800) with
`rolloverReason: scheduled`. It therefore covers the 24 h window
D−1 08:00 → D 08:00 local. Health-table rows are labelled by generation date
D, while the charging diary uses calendar days.

### Charging diary

`devices/iphone-01/charging-sessions.csv` — <!--v:sessions-->357<!--/--> sessions since
2026-09-01 (<!--v:span_days-->85<!--/--> days). Source is a plain-text diary with three lines per
session:

```
开始充电：<date> <time> | 结束充电：<date> <time>
充电时长：<h/m/s> | 充入电量：<n>%
电池电量：<a>% → <b>%  | 每分钟充入：<r>%
```

The raw diary is **not in this repository**. It carries a
device identifier in its header line and second-resolution wall-clock
timestamps that would reveal sleep, wake and travel patterns.

### Daily analytics file (`.ips.ca.synced`)

`devices/iphone-01/analytics/2026-11-15.json` — a whitelisted extraction from
the 2026-11-15 daily file (NDJSON, `bug_type 211`, 863 records) by
`scripts/extract_analytics.py`. The raw file is **not published**: it
contains `deviceId`, UUIDs, `incident_id`, carrier/country, SKU and other
identifiers. Only numeric battery fields from
`BatteryConfigValueHistogramFinal_V2` and `VacVoltageLimit` are emitted, and
the script refuses to write output if any identifier-like key appears.

This file confirms the exact source of each health-table column:

| Export column | Analytics field |
|---------------|-----------------|
| `Cycl.` | `CycleCount` |
| `Raw Capacity` | `AppleRawMaxCapacity` |
| `Nominal Capacity` | `NominalChargeCapacity` |
| `Min Soc` | `DailyMinSoc` |
| `Nominal Health` | derived `NCC / 3692` |
| `iOS` | header `os_version` |
| `Hrs Soc` | no matching field found |

Note `MaximumCapacityPercent` in the analytics is **101**, not <!--v:base_health_two-->99.13<!--/--> — the
export tool's `Nominal Health` is its own ratio, not that system field.
See [`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md) §6:
all stepwise-decay conclusions in this repo describe the NCC-derived ratio,
whereas Apple's own health field stayed at 101 across the 200-cycle step.

### Single voltage reading

`devices/iphone-01/voltage-reading.md` — one manual reading of terminal
voltage at a stated SOC. Loaded terminal voltage, not resting OCV.

---

## De-identification rules

Applied by `scripts/parse_charging_log.py`:

| Kept | Dropped |
|------|---------|
| `session_id` (sequential 1..<!--v:sessions-->357<!--/-->) | device identifier / diary header |
| `day_offset` (days since first record) | absolute calendar dates |
| `duration_sec` | start/end clock times |
| `soc_start`, `soc_end` | timezone, locale |
| `charged_pct` | any free text |
| `rate_pct_per_min` | |
| `anomaly` flag | |

`day_offset` is a relative integer, so daily session counts and time-series
shape remain analysable, while no absolute date or clock time can be
recovered. Health snapshot dates are retained (6 coarse points, no
behavioural detail). `device.json` contains nameplate electrical parameters
plus the model family (`iPhone 17`, published on purpose) —
no serial, UDID, exact variant identifier or analytics filename.

## Derived fields

- `duration_sec` parsed from Chinese `<h>小时<m>分钟<s>秒` strings.
- `charged_pct` as declared in the diary; signed (one session is −19%).
- `anomaly`: semicolon-joined flags — `soc_dropped` (charged_pct < 0 or SOC
  fell), `no_charge`, `soc_delta_mismatch` (`soc_end − soc_start ≠
  charged_pct`), `rate_mismatch` (`|charged_pct/(duration/60) − rate| >
  0.06`).
- `equivalent_full_cycles` = Σ `charged_pct` / 100.

## Validation

`python3 scripts/verify.py` asserts:

1. health percentage equals `nominal_capacity_mah / 3692 × 100` within 0.01 pp;
2. session count and aggregate totals match `docs/charging-summary.json`;
3. `soc_end − soc_start = charged_pct` for all rows (0 mismatches);
4. declared rate consistent with duration/charge within 0.06 %/min;
5. CSV contains no absolute date, clock time, or device-identifier strings;
6. every archived analytics JSON is identifier-free, dated correctly, and
   its `VacVoltageLimit` matches the cycle-node band;
7. `analytics-timeline.csv` is an exact projection of the archive;
8. every archived snapshot records `gauge_update_time_utc`, and consecutive
   files with identical battery state are flagged as stale re-reports
   (informational, not a failure).

`gauge_update_time_utc` comes from `last_value_UpdateTime` (Unix seconds)
and is normalised to ISO-8601 UTC. It records **when the gauge state was
actually written**, which can predate the file's generation date — e.g. the
11-11 and 11-12 files both carry `2026-11-10T14:03:43Z` (22:03 local),
meaning the 11-12 file merely re-reported a stale snapshot, while the 11-10
file carries `2026-11-09T13:58:20Z` (11-09 21:58 local) and is independent.

Source-log integrity: <!--v:sessions-->357<!--/-->/<!--v:sessions-->357<!--/--> sessions parsed, 0 parse errors.

## Known limitations

- Six health snapshots over 57 days is a small sample; the two cliffs cannot
  be fully attributed without an observation at the 250-cycle node.
- `min_soc_pct` varies 18–39% across snapshots, so sampling conditions are
  not controlled. Fixed-SOC sampling is recommended going forward.
- OCV curves used in the voltage check are typical curves for 4.5 V-class
  cells, not a measured curve for this specific cell. The mapping is
  indicative only.
- The cycle-node voltage table is third-party and internally inconsistent
  across sources; see `voltage-nodes.md`.
- Linear assumptions about SOC-vs-voltage are explicitly **not** used in the
  final analysis — the curve is steep near full charge. An earlier linear
  estimate of 4.132 V at 70% was wrong (see `corrections.md`).
- **Retention ceiling**: iOS keeps only ~7–8 days of daily analytics. The
  archive (<!--v:first_md-->11-09<!--/--> … <!--v:base_md-->11-24<!--/-->) is the complete obtainable window; no pre-200 or
  ~138-cycle snapshot exists. A direct 4500 mV reading and the exact step
  timestamp are unrecoverable. The lifetime `MaximumPackVoltage = 4496 mV`
  is used as indirect evidence of the earlier ceiling instead.
