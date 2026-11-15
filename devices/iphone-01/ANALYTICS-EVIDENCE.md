# Analytics evidence — 2026-11-15 snapshot

Source: iOS daily analytics file (`bug_type 211`, NDJSON, generated 08:00
local). 863 records. Parsed with
[`scripts/extract_analytics.py`](../scripts/extract_analytics.py) into
[`analytics/2026-11-15.json`](analytics/2026-11-15.json).

The raw `.ips` file is **not** published: it contains `deviceId`, UUIDs,
`incident_id`, carrier/country, SKU and other identifiers. Only a whitelist
of numeric battery fields is emitted.

---

## 1. The 200-cycle voltage step is CONFIRMED

| Field | Value | Meaning |
|-------|-------|---------|
| `last_value_VacVoltageLimit` | **4480 mV = 4.480 V** | currently effective charge-voltage ceiling |
| `last_value_CycleCount` | 208 | in the 200–249 band |
| `last_value_MaximumPackVoltage` | 4496 mV = 4.496 V | historical peak pack voltage |

The nameplate hardware ceiling is 4.50 V. The **live** software target is
**4.48 V**, exactly the −0.02 V step predicted for the 200-cycle node in
[`voltage-nodes.md`](../docs/voltage-nodes.md).

This resolves the open question in `docs/findings.md`: the pending
"charge to 100% and read the voltage" experiment is no longer needed. The
analytics file reports the configured limit directly.

`MaximumPackVoltage` 4496 mV is a *historical* aggregate (paired with
`MinimumPackVoltage` 2765 mV over the device lifetime), so it does not
contradict the current 4480 mV target.

---

## 2. The health-table columns are now identified exactly

| Published column | Actual analytics field | Value |
|------------------|------------------------|-------|
| `Cycl.` | `CycleCount` | 208 |
| `Raw Capacity` | `AppleRawMaxCapacity` | 3692 |
| `Nominal Capacity` | `NominalChargeCapacity` | 3659 |
| `Nominal Health` | derived: `NCC / 3692 × 100` | 99.106% |
| `Min Soc` | **`DailyMinSoc`** | 39 |
| `iOS` | header `os_version` | 26.4.2 |
| `Hrs Soc` | no matching field found | 0 in export |

`Min Soc` = **minimum SOC of that day**, not the SOC at read time — now
confirmed, not inferred. `Hrs Soc` remains unexplained; no field in the file
obviously corresponds to it.

Two corrections to earlier notes:

- `Raw Capacity` is `AppleRawMaxCapacity`, a gauge estimate that happened to
  equal the nameplate 3692 at this snapshot. It is **not** the health
  denominator; the denominator is the fixed nameplate rated capacity.
- `MaximumCapacityPercent` in the analytics is **101**, which does **not**
  equal the exported `Nominal Health` 99.11%. These are different quantities;
  the export tool computes its own ratio. Do not treat the two as the same.

---

## 3. The first cliff (126→152 cycles) has a candidate cause

`CycleCountLastQmax = 138` — the last Qmax (gauge chemical-capacity)
recalibration happened at cycle **138**, which falls *inside* the 126→152
interval where the first −0.41 pp step occurred.

Supporting gauge state at 208 cycles:

| Field | Value |
|-------|-------|
| `QmaxCell0` | 3824 mAh |
| `MaximumQmax` / `MinimumQmax` | 3901 / 3824 mAh |
| `NCCMax` / `NCCMin` | 3780 / 3657 mAh |
| `MaximumFCC` / `MinimumFCC` | 3837 / 3543 mAh |
| `CycleCountLastQmax` | 138 |

So the two cliffs plausibly have **different** causes:

| Interval | Cycles | Δ health | Likely cause |
|----------|--------|----------|--------------|
| 09-23 → 10-13 | 126→152, contains **138** | −0.41 pp | Qmax / gauge recalibration |
| 11-05 → 11-11 | 194→203, contains **200** | −0.43 pp | `VacVoltageLimit` 4500→4480 |

This is a hypothesis, not yet proven: the five analytics files we have all
sit at 203–208 cycles, i.e. after the step. An analytics snapshot from
**before 200 cycles** (and ideally one from around 138) would show whether
`VacVoltageLimit` was 4500 mV and
whether the Qmax update coincides with the first drop.

---

## 4. Other useful state

| Field | Value | Note |
|-------|-------|------|
| `AverageTemperature` | 29 | gauge-reported average |
| `BatteryHealthMetric` | 77 | opaque |
| `WeightedRa` / `ChemicalWeightedRa` | 75 / 75 | resistance metric |
| `TotalOperatingTime` | 4928 h | ≈205 days |
| `DailyMaxSoc` / `DailyMinSoc` | 63 / 39 | day's range |
| `SlowChargingReason` | 0 | no slow-charge flag that day |
| `BatteryCellDisconnectCount` | 0 | no disconnect |
| `DOFU` | 2026-03-05 | first-use date (not published in CSV) |

`BatteryTimeAtHighSocLast` bins 0–9: `[21, 12, 7, 0, 0, 18, 10, 7, 1, 0]`
— time spent in high-SOC bands, consistent with the log's shallow charging
pattern.

---

## 5. What to send next

Any `.ips.ca.synced` / `.ips` daily analytics file works, **one per date**.
The parser reads the first header line plus two named records
(`BatteryConfigValueHistogramFinal_V2`, `VacVoltageLimit`), so partial or
aggregated files are fine as long as those records are present. The header
timestamp determines the archive filename — no manual naming needed.

Most valuable for closing the remaining questions:

1. **A snapshot with `CycleCount` < 200** — expect `VacVoltageLimit = 4500`.
   Direct before/after proof of the step.
2. **A snapshot near cycle 138** — to test the Qmax-recalibration hypothesis
   for the first cliff.
3. Any snapshot after cycle 250 — expect `VacVoltageLimit = 4460`.

Import any number at once; the timeline CSV is rebuilt from the full archive:

```sh
python3 scripts/extract_analytics.py --archive \
    /path/Analytics-2026-09-19.ips /path/Analytics-2026-10-13.ips
python3 scripts/verify.py
```

### Current timeline

| Date (file) | Gauge `UpdateTime` (UTC) | Cycles | `VacVoltageLimit` | Band | `AppleRawMaxCapacity` | NCC | Health | DailyMinSoc |
|-------------|--------------------------|--------|-------------------|------|------------------------|-----|--------|-------------|
| 2026-11-11 | 11-10 14:03:43 | 203 | 4480 mV (4.48V) | 200–249 ✓ | 3678 | 3658 | 99.079% | 30 |
| 2026-11-12 | 11-10 14:03:43 (stale) | 203 | 4480 mV (4.48V) | 200–249 ✓ | 3678 | 3658 | 99.079% | 30 |
| 2026-11-13 | 11-12 06:04:09 | 205 | 4480 mV (4.48V) | 200–249 ✓ | 3690 | 3658 | 99.079% | 19 |
| 2026-11-14 | 11-13 15:15:07 | 207 | 4480 mV (4.48V) | 200–249 ✓ | 3683 | 3659 | 99.106% | 31 |
| 2026-11-15 | 11-14 14:40:15 | 208 | 4480 mV (4.48V) | 200–249 ✓ | 3692 | 3659 | 99.106% | 39 |

Full machine-readable version:
[`analytics-timeline.csv`](analytics-timeline.csv). Each import adds a row;
`verify.py` asserts every row's voltage matches its node band.

### 5.0 The 11-11 / 11-12 snapshots: the step is older than the files

The 2026-11-11 file reports `CycleCount = 203`, `VacVoltageLimit = 4480 mV`
and `NCC = 3658` (99.079%). Combined with the 11-05 export (cycle 194,
NCC 3675, 99.54%):

- The −17 mAh / −0.46 pp drop happened **within cycles 194 → 203** — 9
  cycles over 7 days (1.29 cycles/day). The window contains the 200 node.
- The 4480 mV target was already active at cycle 203, so the voltage step
  also occurred no later than cycle 203 — consistent with a 200-cycle node.
- Five consecutive snapshots (203/203/205/207/208) all show NCC 3658–3659
  and 4480 mV: the state is stable after the step, not a transient.

**11-11 and 11-12 are the same gauge snapshot.** Their
`BatteryConfigValueHistogramFinal_V2` payloads are byte-identical except for
the aggregate `Count` (5 vs 2), and both carry
`UpdateTime = 2026-11-10T14:03:43Z` = **2026-11-10 22:03 local (+0800)**.
The gauge did not refresh during the 11-11 08:00 → 11-12 08:00 window; the
state seen at 203 cycles was last written on the evening of 11-10. So the
step occurred **no later than 2026-11-10 22:03 local**, and the 11-12 file
is not an independent observation. `verify.py` flags (but does not fail on)
consecutive files with identical battery state.

`gauge_update_time_utc` is now a whitelisted field in
`analytics-timeline.csv`, so each row records when its battery state was
actually written rather than when the file was generated.

- A snapshot from 11-06 … 11-10 would pin the exact step time; a snapshot
  below cycle 200 should show 4500 mV.

**Noise scale.** Over the five archived files NCC varies by only **1 mAh =
0.027 pp** (including a +1 mAh rebound), while `AppleRawMaxCapacity` swings
**3678 → 3678 → 3690 → 3683 → 3692 mAh = 14 mAh = 0.379 pp**. The raw
estimate is
**14× noisier** than the nominal capacity, which is exactly why it is not
used for the health figure. The −0.43 pp cliff is **~16×** the daily NCC
noise, so it is a real step, not sampling jitter.

### 5.1 Two findings from the 11-14 snapshot

**(a) `AppleRawMaxCapacity` moves while `NominalChargeCapacity` does not.**
Between consecutive daily snapshots (207 → 208 cycles):

| Field | 11-14 | 11-15 | Δ |
|-------|-------|-------|---|
| `AppleRawMaxCapacity` | 3683 | 3692 | **+9 mAh** |
| `NominalChargeCapacity` | 3659 | 3659 | 0 |
| `Nominal Health` | 99.106% | 99.106% | 0 |
| `VacVoltageLimit` | 4480 | 4480 | 0 |

This is direct evidence that `Raw Capacity` is a drifting gauge estimate
that does **not** enter the health percentage — previously inferred only from
the 6-row export. All FCC/Qmax/NCC aggregates are also identical across the
two days; only the raw estimate moved.

**(b) The nameplate convergence was coincidental.** At the 11-15 sample,
`AppleRawMaxCapacity` happened to equal 3692 (the nameplate). The 11-14 file
shows it was 3683 the day before. It is not a fixed design-capacity field.

**(c) The −0.43 pp cliff is bracketed, not dated.** See §5.0 above: the window
is cycles 194 → 203, with 4480 mV already active at cycle 203 and the shared
`UpdateTime` bounding the step to no later than 2026-11-10 22:03 local. A
file from 11-06 … 11-10 would pin the day.

### 5.2 Aggregation window (why the cross-check is not exactly 1.00)

Each file's header timestamp is `YYYY-MM-DD 08:00:00 +0800`, while its
metadata `startTimestamp` is the **previous day** at `00:00:00Z` (=
08:00 +0800). `rolloverReason: scheduled`. So a file dated D covers the
24 h window D−1 08:00 → D 08:00 local. Health-table rows are keyed by the
file's generation date, whereas the charging diary uses calendar days —
this offset, plus cumulative-discharge-based cycle counting, explains the
0.93–1.10 ratios in `docs/findings.md`.
