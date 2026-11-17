# Analytics evidence — 2026-11-15 snapshot

Source: iOS daily analytics file (`bug_type 211`, NDJSON, generated 08:00
local). 863 records. Parsed with
[`scripts/extract_analytics.py`](../../scripts/extract_analytics.py) into
[`analytics/2026-11-15.json`](analytics/2026-11-15.json).

The raw `.ips` file is **not** published: it contains `deviceId`, UUIDs,
`incident_id`, carrier/country, SKU and other identifiers. Only a whitelist
of numeric battery fields is emitted.

---

## 1. The 200-cycle voltage step is CONFIRMED

| Field | Value | Meaning |
|-------|-------|---------|
| `last_value_VacVoltageLimit` | **4480 mV = 4.480 V** | currently effective charge-voltage ceiling |
| `last_value_CycleCount` | **200** (11-09 file) | the step is active at the node itself |
| `last_value_MaximumPackVoltage` | 4496 mV = 4.496 V | **lifetime** peak pack voltage |

The nameplate hardware ceiling is 4.50 V. The **live** software target is
**4.48 V**, exactly the −0.02 V step predicted for the 200-cycle node in
[`voltage-nodes.md`](../../docs/voltage-nodes.md). The 11-09 file shows this at
`CycleCount = 200` exactly, not 201 or later.

This resolves the open question in `docs/findings.md`: the pending
"charge to 100% and read the voltage" experiment is no longer needed. The
analytics file reports the configured limit directly.

### 1.1 The pre-200 voltage, without a pre-200 file

iOS retains only ~7–8 days of analytics, so no snapshot with
`CycleCount < 200` is obtainable — a direct 4500 mV reading is **not
available**. There is, however, independent physical evidence of the earlier
target:

| Quantity | Value | Relation |
|----------|-------|----------|
| `MaximumPackVoltage` (lifetime peak) | **4496 mV** | 16 mV **above** the current 4480 mV target |
| Nameplate / 1–199 band | 4500 mV | only 4 mV above the peak |
| Current software target | 4480 mV | cannot produce a 4496 mV pack voltage |

`MaximumPackVoltage` is a lifetime maximum (paired with
`MinimumPackVoltage = 2765`), constant across all <!--v:snap_word-->nine<!--/--> archived snapshots.
A pack cannot reach 4496 mV while the charge target is 4480 mV, so the peak
was necessarily recorded **before** the step, under the ~4.50 V target.

**When was that peak recorded?** The <!--v:span_days-->76<!--/-->-day charging diary (09-01…11-15)
never exceeds **81% SOC** — only 4 sessions reach ≥80% (80/80/80/81) and the
termination SOC piles up at 69% (45 sessions) and 79% (26 sessions),
consistent with **unplugging before the 80% Charge Limit** (enabled as a
safety net, as reported). A
near-full charge is required to reach ~4.50 V, so no session inside the log
window could have produced 4496 mV.

Back-projecting the cycle counter: the diary's 09-01…09-18 equivalent full
cycles are 21.26, and the 09-19 export reads `CycleCount = 122`, giving
**≈101 cycles on 09-01** (the 09-19→11-05 rate is 1.53/day). `DOFU =
2026-03-05`, so there are ~180 days before the diary starts. Conclusion:

> The 4496 mV peak was left by a **full charge before 09-01**, at roughly
> 100 cycles or fewer — well inside the 1–199 band (4500 mV). It is a
> fossil from the pre-limit era, not a recent event.

This is indirect evidence (the peak is a measured pack voltage, not a
configured target), but it closes the qualitative gap: the device did once
run at a voltage ceiling above 4.48 V, consistent with 4.50 → 4.48. It also
means a later full charge, including an iOS calibration charge, would not
refresh this peak under the current 4480 mV target.

**What remains impossible to recover**: the exact 4500 mV configuration
reading and the precise timestamp of the step. The upper bound is
2026-11-08 17:08 local (the 11-09 file's gauge `UpdateTime`).

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
  equal the exported `Nominal Health` 99.11%. See **§6** for the full
  distinction — these are different quantities and the gap matters.

---

## 6. Two different "battery health" numbers

There are **two** percentages in this dataset. conflating them is wrong.

| | `Nominal Health` (export) | `MaximumCapacityPercent` (analytics) |
|---|---|---|
| Source | third-party export tool | Apple's own gauge field (`last_value_MaximumCapacityPercent`) |
| Formula | `NominalChargeCapacity / 3692 × 100` (verified ≤0.005 pp over 6 rows) | Apple internal algorithm, uses its own design-capacity / calibration baseline — **not** a simple division by 3692 |
| <!--v:base_md-->11-17<!--/--> value | **<!--v:base_health_two-->99.13<!--/-->%** | **<!--v:apple-->101<!--/-->** (integer) |
| <!--v:first_md-->11-09<!--/--> … <!--v:base_md-->11-17<!--/--> | 99.079 → <!--v:base_health-->99.133<!--/--> (and 99.54 → 99.11 across the 6-row export) | **101 on all <!--v:snap_word-->nine<!--/--> days, unchanged** |
| Granularity | 0.01 pp, derived from mAh | coarse integer, only moves on recalibration |
| What it is | a ratio of two published numbers | the value Apple's battery-health feature uses (per multiple iOS analytics references) |

**Why the 1.89 pp gap?** With the nameplate 3692 as denominator, NCC 3659
gives 99.11%. Apple's 101 implies a different baseline (roughly
3659/1.01 ≈ 3623 mAh), i.e. its internal design capacity / calibration
reference is lower than the nameplate rated capacity. `QmaxCell0 = 3824`
and `MaximumFCC = 3837` are yet other quantities (cell chemical capacity and
full-charge-capacity extremes), neither of which is that baseline. We do
**not** know Apple's exact formula and do not guess one.

A second, 1420-cycle device makes this unmistakable. With its 2815 mAh
nameplate: `NCC / rated = 57.66%` but Apple reports **73** — a **15.34 pp**
gap, versus only 1.89 pp on `iphone-01`. Two devices show the gap is not a
fixed offset or rounding; Apple uses its own calibrated baseline. See
[`devices/reference-01/README.md`](../reference-01/README.md).
**Third device — sign reversal, unexplained.** `reference-02` (2919
cycles, **original battery**, confirmed on the device) gives `NCC/nameplate =
71.13%` vs Apple **67**, a **−4.13 pp** gap. So the "gap grows with age"
statement above does **not** generalise — with three devices the gap is
clearly device-dependent. Apple's implied baseline there is 3301 mAh,
**6% above** the 3110 mAh nameplate, whereas it is below the nameplate on
the other two devices. We do not know why and do not guess. See
[`devices/reference-02/README.md`](../reference-02/README.md) §2. What
remains firm: `MaximumCapacityPercent` is not `NCC / nameplate`.

**Consequence for this repo's conclusions**: the −0.43 pp "cliff", the
stepwise-decay model and the 16×-noise argument all describe the **export
tool's NCC-derived ratio**, not `MaximumCapacityPercent`. Apple's own
health field stayed at 101 throughout the 200-cycle step — so the step is
**not visible in Apple's displayed battery health**. It is visible in the
gauge's `NominalChargeCapacity` (3675 → 3658 mAh) and in
`VacVoltageLimit` (4500 → 4480 mV).

Which is "accurate"? Both are internally consistent for their own
definitions. `Nominal Health` is exactly reproducible from published mAh,
which makes it the better **measurement signal** for this analysis;
`MaximumCapacityPercent` is what the OS reports to the user. Neither is a
direct laboratory measurement of cell capacity. Both are exposed in
[`analytics-timeline.csv`](analytics-timeline.csv) side by side.

### References for field semantics

- [How to check Battery Health on iPadOS/macOS (DEV)](https://dev.to/tetra2000/how-to-check-battery-health-on-ipadosmacos-154) — `last_value_MaximumCapacityPercent` "seems to be 'Battery Health' which [is] available on iPhone"; `NominalChargeCapacity` is the normalized value used to calculate it.
- [iPad Battery Health (Lei Mao)](https://leimao.github.io/blog/iPad-Battery-Health/) — uses `MaximumCapacityPercent` to obtain battery health on iPad, where Settings has no such page.
- [Apple StackExchange: interpreting iPhone analytics battery data](https://apple.stackexchange.com/questions/458960/how-to-interpret-the-very-rich-iphone-analytics-data-about-battery-use-health) — discussion showing `MaximumCapacityPercent` can exceed 100 (e.g. 103 after a battery swap), confirming it is a calibrated relative figure, not a simple mAh ratio.


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
| 11-05 → 11-09 | 194→200, ends at the **200** node | −0.43 pp | `VacVoltageLimit` 4500→4480 |

This is a hypothesis, not yet proven: the <!--v:snap_word-->nine<!--/--> analytics files available all
sit at <!--v:cycle_range-->200–212<!--/--> cycles, i.e. at or after the step. An analytics snapshot from
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

**Retention limit**: iOS keeps only about 7 days of analytics. The <!--v:snap_word-->nine<!--/-->
files archived here (<!--v:first_md-->11-09<!--/--> … <!--v:base_md-->11-17<!--/-->) are the complete obtainable window. No
pre-200 snapshot exists, so a direct `VacVoltageLimit = 4500 mV` reading is
unobtainable; see §1.1 for the indirect evidence that replaces it. Snapshots
near cycle 138 (the Qmax hypothesis) are likewise out of reach.

Still worth sending as new files appear:

1. **Cycle 250 (~2026-12-12)** — expect `VacVoltageLimit = 4460 mV`; this is
   fully observable with the rolling 7-day window and would confirm the
   node table's next step.
2. **Cycle 300 (~2027-01-14)** — expect 4440 mV.
3. Any intermediate dates — to keep the health/cycle timeline continuous.

Import any number at once; the timeline CSV is rebuilt from the full archive:

```sh
python3 scripts/extract_analytics.py --archive \
    /path/Analytics-2026-09-19.ips /path/Analytics-2026-10-13.ips
python3 scripts/verify.py
```

### Current timeline

<!--b:timeline_en-->

| Date (file) | Gauge `UpdateTime` (UTC) | Cycles | `VacVoltageLimit` | Band | `AppleRawMaxCapacity` | NCC | Health | DailyMinSoc |
|-------------|--------------------------|--------|-------------------|------|------------------------|-----|--------|-------------|
| 2026-11-09 | 11-08 09:08:37 | **200** | 4480 mV (4.48V) | 200–249 ✓ | 3707 | 3658 | 99.079% | 33 |
| 2026-11-10 | 11-09 13:58:20 | 202 | 4480 mV (4.48V) | 200–249 ✓ | 3708 | 3658 | 99.079% | 17 |
| 2026-11-11 | 11-10 14:03:43 | 203 | 4480 mV (4.48V) | 200–249 ✓ | 3678 | 3658 | 99.079% | 30 |
| 2026-11-12 | 11-10 14:03:43 (stale) | 203 | 4480 mV (4.48V) | 200–249 ✓ | 3678 | 3658 | 99.079% | 30 |
| 2026-11-13 | 11-12 06:04:09 | 205 | 4480 mV (4.48V) | 200–249 ✓ | 3690 | 3658 | 99.079% | 19 |
| 2026-11-14 | 11-13 15:15:07 | 207 | 4480 mV (4.48V) | 200–249 ✓ | 3683 | 3659 | 99.106% | 31 |
| 2026-11-15 | 11-14 14:40:15 | 208 | 4480 mV (4.48V) | 200–249 ✓ | 3692 | 3659 | 99.106% | 39 |
| 2026-11-16 | 11-15 15:48:23 | 209 | 4480 mV (4.48V) | 200–249 ✓ | 3708 | 3660 | 99.133% | 15 |
| 2026-11-17 | 11-16 18:08:15 | **212** | 4480 mV (4.48V) | 200–249 ✓ | 3681 | 3660 | 99.133% | 15 |

<!--/b-->

Full machine-readable version:
[`analytics-timeline.csv`](analytics-timeline.csv). Each import adds a row;
`verify.py` asserts every row's voltage matches its node band.

### 5.0 The 11-09 snapshot: the step fires exactly at cycle 200

The 2026-11-09 file reports **`CycleCount = 200`** together with
`VacVoltageLimit = 4480 mV` and `NCC = 3658` (99.079%). The software target
has **already stepped down at exactly 200 cycles** — not at 201 or later.
This is the strongest device-level confirmation of the cycle-node rule in
this dataset.

Combined with the 11-05 export (cycle 194, NCC 3675, 99.54%):

- The −17 mAh / −0.46 pp drop happened **within cycles 194 → 200** — 6
  cycles over 4 days (1.50 cycles/day). The window ends exactly at the 200
  node, so the voltage step and the capacity cliff are coincident with it.
- The 11-09 file is **independent**: its gauge state was written at
  `UpdateTime = 2026-11-08T09:08:37Z` = **2026-11-08 17:08 local (+0800)**,
  and `CycleCount`, `TotalOperatingTime`, SOC range and Raw all differ from
  11-10. So the step is bounded to **no later than 2026-11-08 17:08 local**.
- <!--v:snap_word_cap-->Nine<!--/--> consecutive snapshots (<!--v:cycle_list-->200/202/203/203/205/207/208/209/212<!--/-->) all show NCC
  <!--v:ncc_range-->3658–3660<!--/--> and 4480 mV: a stable post-step state, not a transient.
- Note 11-09 was a light-use day: `DailyMinSoc = 33`, `DailyMaxSoc = 42`
  (only a 9-point SOC band), consistent with the cycle counter sitting at
  exactly 200 all day.

**11-11 and 11-12 are the same gauge snapshot.** Their
`BatteryConfigValueHistogramFinal_V2` payloads are byte-identical except for
the aggregate `Count` (5 vs 2), and both carry
`UpdateTime = 2026-11-10T14:03:43Z` = **2026-11-10 22:03 local (+0800)**.
The gauge did not refresh during the 11-11 08:00 → 11-12 08:00 window, so
the 11-12 file is not an independent observation. `verify.py` flags (but
does not fail on) consecutive files with identical battery state.

`gauge_update_time_utc` is now a whitelisted field in
`analytics-timeline.csv`, so each row records when its battery state was
actually written rather than when the file was generated.

- A snapshot from 11-06 … 11-08 would show 4500 mV, but iOS retains only
  ~7–8 days of analytics, so none is obtainable. See §1.1 for the indirect
  evidence that substitutes for it.

**Noise scale.** Over the <!--v:snap_word-->nine<!--/--> archived files NCC varies by only **1 mAh =
0.027 pp** (including a +1 mAh rebound), while `AppleRawMaxCapacity` swings
**<!--v:raw_list-->3707 → 3708 → 3678 → 3678 → 3690 → 3683 → 3692 → 3708 → 3681<!--/--> mAh = <!--v:raw_range-->30<!--/--> mAh = <!--v:raw_range_pp-->0.813<!--/--> pp**.
The raw estimate is ~**<!--v:raw_ratio-->30<!--/-->× noisier** than the nominal capacity, which is
exactly why it is not used for the health figure. The −0.43 pp cliff is ~16×
the daily NCC noise, so it is a real step, not sampling jitter.

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
is cycles 194 → 200, with 4480 mV already active at exactly cycle 200 and the
11-09 file's `UpdateTime` bounding the step to no later than 2026-11-08 17:08
local. No file from 11-06 … 11-08 survives the 7-day retention, so the exact
day cannot be determined.

### 5.2 Aggregation window (why the cross-check is not exactly 1.00)

Each file's header timestamp is `YYYY-MM-DD 08:00:00 +0800`, while its
metadata `startTimestamp` is the **previous day** at `00:00:00Z` (=
08:00 +0800). `rolloverReason: scheduled`. So a file dated D covers the
24 h window D−1 08:00 → D 08:00 local. Health-table rows are keyed by the
file's generation date, whereas the charging diary uses calendar days —
this offset, plus cumulative-discharge-based cycle counting, explains the
0.93–1.10 ratios in `docs/findings.md`.
