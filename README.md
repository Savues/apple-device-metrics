<div align="center">

# apple-device-metrics

**English** · [中文](README.zh.md) · [Website](https://savues.github.io/apple-device-metrics/)

[![verify](https://github.com/Savues/apple-device-metrics/actions/workflows/verify.yml/badge.svg)](https://github.com/Savues/apple-device-metrics/actions/workflows/verify.yml)
[![pages](https://github.com/Savues/apple-device-metrics/actions/workflows/pages.yml/badge.svg)](https://savues.github.io/apple-device-metrics/)
[![license: CC0-1.0](https://img.shields.io/badge/license-CC0--1.0-blue.svg)](LICENSE)
![device: iPhone 17](https://img.shields.io/badge/device-iPhone%2017-30a46c.svg)

Longitudinal battery and charging measurements from Apple devices, published as
de-identified open data.

</div>

All numbers here are **derived from iOS analytics snapshots and charging logs**,
not from marketing material. The goal is a reproducible record of how the
reported battery health figure actually behaves over time.

### At a glance (`iphone-01`, latest snapshot <!--v:base_date-->2026-11-17<!--/-->)

| Cycles | NCC | NCC ÷ 3692 | Apple displayed | Voltage target | Usage |
|:-:|:-:|:-:|:-:|:-:|:-:|
| **<!--v:base_cycle-->212<!--/-->** | **<!--v:base_ncc-->3660<!--/--> mAh** | **<!--v:base_health_two-->99.13<!--/-->%** | **<!--v:apple-->101<!--/-->%** | **<!--v:vac-->4480<!--/--> mV** | **<!--v:rate-->1.30<!--/--> cycles/day** |

Next node: **250 cycles → 4460 mV, ~<!--v:date_next-->2026-12-16<!--/-->** (pre-registered in
[`docs/predictions.json`](docs/predictions.json)).

<p align="center"><img src="docs/iphone17-forecast.svg" alt="iphone-01 forecast curve" width="760"></p>

> **Data-collection condition.** On `iphone-01` iOS *Charge Limit* is set to
> **80% as a safety net**, but the owner unplugs **before 80%** on almost
> every session. Apple's occasional calibration full charge is therefore armed
> but never observed to run: no full charge occurred in the 76-day window. Cycle-driven
> findings (voltage steps, forecast) are unaffected; gauge-derived capacity
> and displayed-SOC readings carry an unquantified bias. See
> [`docs/shallow-charging-accuracy.md`](docs/shallow-charging-accuracy.md).

---

## Devices

| ID | Platform | Data | Coverage |
|----|----------|------|----------|
| [`iphone-01`](devices/iphone-01/) | **iPhone 17**, iOS 26.4.2, 3.887V / 3692mAh / 4.50V limit | <!--v:snap_n-->9<!--/--> analytics snapshots + 6-row health export, 325 charge sessions, 1 voltage reading | 2026-09-01 → <!--v:base_date-->2026-11-17<!--/--> (76-day charging diary) |
| [`reference-01`](devices/reference-01/) | iOS 17.6.1, 1420 cycles, 3.83V / 2815mAh / 4.45V | single analytics snapshot, **reference only** | 2026-11-15 |
| [`reference-02`](devices/reference-02/) | iOS 15.1, 3.83V / 3110mAh / 4.45V | nameplate + one gauge snapshot (2919 cycles, 67%); **no `VacVoltageLimit`** | 2026-11-15 |

`reference-01` and `reference-02` are additional devices used purely to
cross-check the voltage-node ladder, the two-health-metric distinction and
nameplate energy consistency. They are kept in separate directories and
contribute to **none** of the findings' statistics.

More devices can be added as sibling directories under `devices/`.

---

## Headline findings

> **Read this first**: there are two different "battery health" numbers.
> `nominal_health_pct` (99.11%) is a ratio computed by the third-party export
> tool from `NominalChargeCapacity / 3692`. Apple's own analytics field
> `MaximumCapacityPercent` is **101** and **did not change** across the
> 200-cycle step. Every decay figure below describes the NCC-derived ratio,
> not the value iOS displays. See
> [`ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.md) §6.

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

4. **The 200-cycle step is confirmed by analytics**: `VacVoltageLimit =
   4480 mV` at **exactly cycle 200**, versus the 4.50 V nameplate — the
   predicted −0.02 V step. A second device (4.45 V nameplate, 1420 cycles)
   independently confirms the whole ladder:
   `4.45 − 0.02×3 − 0.05 = 4.34 V` equals its measured 4340 mV. Two
   nameplates, two iOS versions, one consistent step table. See
   [`docs/voltage-nodes.md`](docs/voltage-nodes.md) and
   [`devices/reference-01/`](devices/reference-01/).

5. **Ageing is concave, not linear — and the displayed number is not pure
   wear.** Displayed health loss slows from ~−2.31 pp per 100 cycles early
   to ~−0.40 pp late. An A/B measurement on the same 4.50 V platform shows
   that dropping the voltage limit 4500→4390 mV removes **8.0 pp of
   reported capacity while Qmax stays unchanged** — i.e. ~40% of Apple's
   "80% at 1000 cycles" drop is reversible lock-in, not chemical ageing.
   The step-down is *protective*. Full projection:
   [`docs/lifetime-projection.md`](docs/lifetime-projection.md).

6. **Charging behaviour**: 325 sessions / 76 days, 98.83 equivalent full
   cycles, mean 1.65%/min (1.76%/min excluding anomalies). 18 sessions
   (5.5%) recorded zero net charge, one recorded SOC *dropping* while
   plugged in — 19 anomalous rows (5.8%) in total.

7. **`Raw Capacity` is a drifting estimate, proven by consecutive snapshots**:
   11-14 → 11-15 shows `AppleRawMaxCapacity` 3683→3692 (+9 mAh) with
   `NominalChargeCapacity` and health unchanged. Its convergence on the 3692
   nameplate at 11-15 was coincidental.

8. **The −0.43 pp cliff is 16× the daily noise.** <!--v:snap_word_cap-->Nine<!--/--> consecutive analytics
   snapshots give NCC <!--v:ncc_range-->3658–3660<!--/--> mAh (0.027 pp jitter, including rebounds), while
   `AppleRawMaxCapacity` swings <!--v:raw_range-->30<!--/--> mAh (<!--v:raw_ratio-->30<!--/-->× noisier). The cliff is bracketed
   to cycles 194→200 (1.50 cycles/day). The 11-09 file shows
   **4480 mV at exactly cycle 200** — the step fires at the node, not after
   it — and its gauge `UpdateTime` (2026-11-08 17:08 local) bounds the step
   to before that. 11-12 is a stale re-report of 11-11.

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
no behavioural detail). Serial numbers, UDIDs, exact model-variant
identifiers and the analytics source filenames are excluded. The model
family (`iPhone 17`) is published with the owner's consent; the specific
variant is not.

---

## Reproduce

```sh
# Import new analytics files, regenerate the forecast and run every check
scripts/update.sh /path/Analytics-A.ips /path/Analytics-B.ips

# Or only re-run the checks (also confirms the committed forecast equals a
# fresh regeneration, and scores pre-registered predictions)
python3 scripts/verify.py
python3 scripts/check_links.py

# Re-parse a private raw diary into the de-identified CSV
# (raw diary is deliberately NOT in this repository)
python3 scripts/parse_charging_log.py /path/to/private/raw.txt \
    devices/iphone-01/charging-sessions.csv docs/charging-summary.json
```

| Path | Contents |
|------|----------|
| [`devices/iphone-01/health-samples.csv`](devices/iphone-01/health-samples.csv) | 6-row third-party health export (not analytics snapshots) |
| [`devices/iphone-01/charging-sessions.csv`](devices/iphone-01/charging-sessions.csv) | 325 de-identified sessions |
| [`devices/iphone-01/device.json`](devices/iphone-01/device.json) | nameplate parameters |
| [`devices/iphone-01/voltage-reading.md`](devices/iphone-01/voltage-reading.md) | single 4.04V @ 70% reading + OCV check |
| [`docs/findings.md`](docs/findings.md) | full analysis |
| [`docs/lifetime-projection.md`](docs/lifetime-projection.md) | general lifetime reasoning (cross-device context; **not** the iphone-01 forecast) |
| [`docs/iphone17-forecast.md`](docs/iphone17-forecast.md) | **iphone-01-only future battery curve** — at current usage (1.30 cycles/day = 4801 mAh/day), with real mAh |
| `docs/iphone17-forecast.csv` / `.json` / `.svg` | forecast data and chart |
| [`docs/voltage-capacity-experiment.json`](docs/voltage-capacity-experiment.json) | A/B measurement: voltage limit vs reported capacity |
| [`scripts/forecast.py`](scripts/forecast.py) | regenerates the iphone-01-only forecast |
| [`scripts/params.py`](scripts/params.py) | derives every forecast parameter (base, usage rates, plateau, node step) from the published data; no hand-entered constants |
| [`scripts/update.sh`](scripts/update.sh) | one-command import → timeline → forecast → doc sync → verify |
| [`scripts/sync_docs.py`](scripts/sync_docs.py) | refills every data-dependent number in the docs, marked `<!--v:KEY-->…<!--/-->` (inline) or `<!--b:KEY-->…<!--/b-->` (generated table); `--check` is part of `verify.py` |
| [`scripts/check_links.py`](scripts/check_links.py) | fails on broken relative Markdown links |
| [`docs/predictions.json`](docs/predictions.json) | **pre-registered** 250-node predictions, scored automatically by `verify.py` |
| [`docs/voltage-nodes.md`](docs/voltage-nodes.md) | cycle-node voltage table and its provenance |
| [`docs/methodology.md`](docs/methodology.md) | field definitions, units, known limitations |
| [`docs/shallow-charging-accuracy.md`](docs/shallow-charging-accuracy.md) | **Charge Limit 80% on, but unplugged before 80%**: why the calibration full charge never runs, and which readings it affects |
| [`docs/corrections.md`](docs/corrections.md) | errors found and corrected during analysis |
| [`devices/iphone-01/ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.md) | raw analytics fields + confirmed voltage step |
| `devices/iphone-01/analytics/YYYY-MM-DD.json` | whitelisted extraction, one file per date |
| [`devices/iphone-01/analytics-timeline.csv`](devices/iphone-01/analytics-timeline.csv) | consolidated date / cycle / voltage / health timeline |
| [`docs/charging-summary.json`](docs/charging-summary.json) | computed aggregates |
| [`scripts/verify.py`](scripts/verify.py) | consistency checks |
| [`scripts/parse_charging_log.py`](scripts/parse_charging_log.py) | charging diary parser / de-identifier |
| [`scripts/extract_analytics.py`](scripts/extract_analytics.py) | analytics `.ips` parser / de-identifier |
| [`scripts/ingest_analytics.py`](scripts/ingest_analytics.py) | append plain-text health-table exports |

---

## Status of claims

The cycle-node voltage table is **third-party reverse-engineering**, not Apple
documentation. Apple's public material only states "80% capacity at 1000
cycles" and documents performance management / optimised charging. Everything
in this repo is labelled accordingly.

**Update (2026-11-16)**: the 200-cycle step is directly confirmed on this
device — `VacVoltageLimit = 4480 mV` at **exactly `CycleCount = 200`**
(2026-11-09 analytics), with <!--v:further_word-->eight<!--/--> further snapshots at <!--v:further_range-->202–212<!--/--> cycles all
showing 4480 mV. See
[`devices/iphone-01/ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.md).
The mid-SOC voltage test is no longer needed. iOS retains only ~7–8 days of
analytics, so a pre-200 snapshot (4500 mV) is **unobtainable**; the lifetime
peak `MaximumPackVoltage = 4496 mV` — impossible under the current 4480 mV
target — is a fossil from a full charge before 09-01 (≈101 cycles), when the
4.50 V ceiling was active. The charging diary never exceeds 81% SOC
(69/79% clustering: unplugged before the 80% Charge Limit), so the peak could not be refreshed
later. See
[`devices/iphone-01/ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.md).

## Feeding in new analytics files

Send any `.ips` / `.ips.ca.synced` daily analytics files, **one per date**.
NDJSON with a header line plus named aggregate records. Import any number at
once:

```sh
python3 scripts/extract_analytics.py --archive /path/Analytics-A.ips /path/Analytics-B.ips
```

For the full refresh use `scripts/update.sh` with the same arguments: it
also regenerates the forecast from the new latest snapshot and runs
`verify.py`. `sync_docs.py` refills the marked numbers in the docs
(base, rates, node dates, snapshot counts, timeline tables); unmarked text
such as dated corrections is left alone, and new findings still need writing by hand.

Each file is written to `devices/iphone-01/analytics/<header-date>.json`,
`analytics-timeline.csv` is rebuilt, and every snapshot is checked against
the cycle-node voltage table (4500 / 4480 / 4460 / 4440 / 4390 mV). A
mismatch prints `??` rather than silently passing. Re-importing the same date
updates it in place. `python3 scripts/verify.py` re-checks the whole archive;
GitHub Actions runs it, the link check and a raw-file / identifier scan on
every push.

Only a whitelist of numeric battery fields is emitted; the raw file (which
contains deviceId, UUIDs, carrier/country and incident IDs) must never be
committed. Snapshots from before cycle 200 are especially valuable. For the
plain-text health-table export, use `scripts/ingest_analytics.py`.

## License

Data and scripts: CC0-1.0 (public domain). See [`LICENSE`](LICENSE).
