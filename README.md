# apple-device-metrics

Longitudinal battery and charging measurements from Apple devices, published as
de-identified open data.

All numbers here are **derived from iOS analytics snapshots and charging logs**,
not from marketing material. The goal is a reproducible record of how the
reported battery health figure actually behaves over time.

---

## Devices

| ID | Platform | Data | Coverage |
|----|----------|------|----------|
| [`iphone-01`](devices/iphone-01/) | iOS 26.4.2, 3.887V / 3692mAh / 4.50V limit | 6 health snapshots, 325 charge sessions, 1 voltage reading | 2026-09-01 → 2026-11-15 (76 days) |

More devices can be added as sibling directories under `devices/`.

---

## Headline findings

1. **`nominal_health_pct = nominal_capacity_mah / 3692`**, using the *fixed*
   nameplate rated capacity. Verified against all 6 snapshots with error
   ≤ 0.005 percentage points. The `raw_capacity_mah` column (3742→3692,
   drifting) is **not** the denominator and does not enter the health figure.

2. **Degradation is stepwise, not linear.** Flat plateaus of ~0.004%/day
   (genuine chemical ageing) punctuated by two one-off drops of ~-0.41pp and
   ~-0.43pp at 126→152 and 194→208 cycles.

3. **The 194→208 interval straddles cycle 200**, matching a widely reported
   (non-official) mechanism where iOS lowers the software charge-voltage target
   at cycle-count nodes (200 / 250 / 300 / 1000, −0.02V per step, −0.05V at
   ≥1000). The nameplate 4.50V is the hardware ceiling; the software target is
   set below it. See [`docs/voltage-nodes.md`](docs/voltage-nodes.md).

4. **The 200-cycle step is confirmed by analytics**, not just inferred:
   `last_value_VacVoltageLimit = 4480 mV` at cycle 208, versus the 4.50 V
   nameplate ceiling — exactly the predicted −0.02 V step. The first cliff
   (126→152) instead contains `CycleCountLastQmax = 138`, pointing to a
   gauge recalibration. See
   [`devices/iphone-01/ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.md).

5. **Linear extrapolation to 80% is wrong for this device.** Middle-term
   behaviour is better described by a step model: ~96% at cycle 1000 before
   the ≥1000 step, versus 90.5% from a naive 0.0165%/day fit.

6. **Charging behaviour**: 325 sessions / 76 days, 98.83 equivalent full
   cycles, mean 1.65%/min (1.76%/min excluding anomalies). 18 sessions
   (5.5%) recorded zero net charge, one recorded SOC *dropping* while
   plugged in — 19 anomalous rows (5.8%) in total.

See [`docs/findings.md`](docs/findings.md) for the full analysis, including
corrections to earlier misreadings.

---

## Data & privacy

The source charging diary contains second-resolution wall-clock timestamps.
**These are not published.** Published session rows contain only:

`session_id`, `day_offset` (days since first record, no calendar date),
`duration_sec`, `soc_start`, `soc_end`, `charged_pct`,
`rate_pct_per_min`, `anomaly`.

Publishing the raw timestamps would expose sleep/wake and travel patterns, so
they are stripped at parse time. Health snapshots keep their dates (6 points,
no behavioural detail). Serial numbers, UDIDs, model identifiers and the
analytics source filenames are excluded.

---

## Reproduce

```sh
# Re-derive every summary number from the CSVs
python3 scripts/verify.py

# Re-parse a private raw diary into the de-identified CSV
# (raw diary is deliberately NOT in this repository)
python3 scripts/parse_charging_log.py /path/to/private/raw.txt \
    devices/iphone-01/charging-sessions.csv docs/charging-summary.json
```

| Path | Contents |
|------|----------|
| `devices/iphone-01/health-samples.csv` | 6 analytics snapshots |
| `devices/iphone-01/charging-sessions.csv` | 325 de-identified sessions |
| `devices/iphone-01/device.json` | nameplate parameters |
| `devices/iphone-01/voltage-reading.md` | single 4.04V @ 70% reading + OCV check |
| `docs/findings.md` | full analysis |
| `docs/voltage-nodes.md` | cycle-node voltage table and its provenance |
| `docs/methodology.md` | field definitions, units, known limitations |
| `docs/corrections.md` | errors found and corrected during analysis |
| `devices/iphone-01/ANALYTICS-EVIDENCE.md` | raw analytics fields + confirmed voltage step |
| `devices/iphone-01/analytics-current.json` | whitelisted fields from the 2026-11-15 analytics file |
| `docs/charging-summary.json` | computed aggregates |
| `scripts/verify.py` | consistency checks |
| `scripts/parse_charging_log.py` | charging diary parser / de-identifier |
| `scripts/extract_analytics.py` | analytics `.ips` parser / de-identifier |
| `scripts/ingest_analytics.py` | append plain-text health-table exports |

---

## Status of claims

The cycle-node voltage table is **third-party reverse-engineering**, not Apple
documentation. Apple's public material only states "80% capacity at 1000
cycles" and documents performance management / optimised charging. Everything
in this repo is labelled accordingly.

**Update (2026-11-15)**: the 200-cycle step is now directly confirmed on this
device by `VacVoltageLimit = 4480 mV` at cycle 208 in the iOS analytics file —
see [`devices/iphone-01/ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.md).
The mid-SOC voltage test is no longer needed. Remaining open questions: the
exact voltage before cycle 200, and whether the first cliff is a Qmax
recalibration. A pre-200 analytics snapshot would settle both.

## Feeding in new analytics files

Send any `.ips` / `.ips.ca.synced` daily analytics file. It is NDJSON with a
header line plus named aggregate records. Parse it locally:

```sh
python3 scripts/extract_analytics.py /path/to/Analytics-YYYY-MM-DD.ips \
    -o devices/iphone-01/analytics-YYYY-MM-DD.json
```

Only a whitelist of numeric battery fields is emitted; the raw file (which
contains deviceId, UUIDs, carrier/country and incident IDs) must never be
committed. Snapshots from before cycle 200 are especially valuable. For the
plain-text health-table export, use `scripts/ingest_analytics.py`.

## License

Data and scripts: CC0-1.0 (public domain). See [`LICENSE`](LICENSE).
