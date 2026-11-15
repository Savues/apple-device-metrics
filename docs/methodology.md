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

### Charging diary

`devices/iphone-01/charging-sessions.csv` — 325 sessions, 2026-09-01 to
2026-11-15 (76 days). Source is a plain-text diary with three lines per
session:

```
开始充电：<date> <time> | 结束充电：<date> <time>
充电时长：<h/m/s> | 充入电量：<n>%
电池电量：<a>% → <b>%  | 每分钟充入：<r>%
```

The raw diary is **deliberately excluded** from this repository. It carries a
device identifier in its header line and second-resolution wall-clock
timestamps that would reveal sleep, wake and travel patterns.

### Single voltage reading

`devices/iphone-01/voltage-reading.md` — one manual reading of terminal
voltage at a stated SOC. Loaded terminal voltage, not resting OCV.

---

## De-identification rules

Applied by `scripts/parse_charging_log.py`:

| Kept | Dropped |
|------|---------|
| `session_id` (sequential 1..325) | device identifier / diary header |
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
only — no serial, UDID, model identifier or analytics filename.

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
5. CSV contains no absolute date, clock time, or device-identifier strings.

Source-log integrity: 325/325 sessions parsed, 0 parse errors.

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
