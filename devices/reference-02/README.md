# Reference device 2 — nameplate + gauge snapshot

A third device was supplied with its manufacturer nameplate and two
analytics files. One (`Analytics-Daily-*`) has no gauge records; a second
(`Analytics-Never-*`) contains a full `BatteryConfigValueHistogram_Final`
snapshot. This device is kept separate and is **not** merged into
`iphone-01` or any statistics.

> ⚠️ `OriginalBattery = 0` appears in the gauge record. Public references
> only document `null` / `1` for this field, so **`0` has no confirmed
> meaning**; an earlier note in this repo read it as "replacement battery"
> and that was an unfounded inference. The owner confirms this device has
> its **original, never-replaced battery**, consistent with
> `BatterySerialChanged = False`. See
> [`docs/corrections.md`](../../docs/corrections.md).

## Manufacturer nameplate

| Field | Value |
|-------|-------|
| Cell energy | 12.02 Wh |
| Battery energy | 11.91 Wh |
| Nominal voltage | 3.83 V |
| Rated capacity | 3110 mAh |
| Charge limit voltage | 4.45 V |
| iOS (from analytics header) | 15.1 |

Energy check: `3.83 V × 3110 mAh = 11.911 Wh` ≈ 11.91 Wh ✓.
Cell energy / capacity = `12.02/3.110 = 3.865 V`, i.e. **+0.035 V**
above nominal.

## The two analytics files

| File | Records | Gauge data |
|------|---------|------------|
| `Analytics-Daily-*` (27.6 KB) | 70 | **none** — JetsamV3, WlpFixAps, HomeKit, Health, CableTypeChangedV2 |
| `Analytics-Never-*` (93.7 KB) | 355 | **one** `BatteryConfigValueHistogram_Final` record |

The second file supplies the gauge snapshot. Note the record name is
`BatteryConfigValueHistogram_Final` (no `_V2`), i.e. an older iOS 15.1
schema. `scripts/extract_analytics.py` expects
`BatteryConfigValueHistogramFinal_V2` plus `VacVoltageLimit` and will
**reject both files** — expected, since neither has `VacVoltageLimit`. The
values below were extracted manually and whitelisted.

### Gauge snapshot (2026-11-15, iOS 15.1)

| Field | Value |
|-------|-------|
| `CycleCount` | **2919** |
| `MaximumCapacityPercent` | **67** |
| `NominalChargeCapacity` | 2212 mAh |
| `AppleRawMaxCapacity` | 2272 mAh |
| `MaximumPackVoltage` | **4449 mV** |
| `MinimumPackVoltage` | 2541 mV |
| `QmaxCell0` | 2488 mAh |
| `MaximumFCC` / `MinimumFCC` | 3265 / 617 mAh |
| `NCCMax` / `NCCMin` | 3211 / 2037 mAh |
| `WeightedRa` | 338 |
| `CycleCountLastQmax` | 87 |
| `TotalOperatingTime` | 61934 h |
| `OriginalBattery` | **0** (meaning unconfirmed) |
| `BatterySerialChanged` | False (consistent with an original battery) |
| `BatterySerialChanged` | False |
| gauge `UpdateTime` | 2026-11-13 18:10:56 UTC |

**No `VacVoltageLimit`** exists in this iOS 15.1 aggregate set. The only
voltage evidence is `MaximumPackVoltage = 4449 mV`, which is a lifetime peak
and not a configured target.

## What this device contributes

### 1. A 4.45 V platform at very high cycle count

`MaximumPackVoltage = 4449 mV` ≈ 4450 mV matches the 4.45 V nameplate top
rung, just as `reference-01` (4450 mV) and `iphone-01` (4496 mV ≈ 4500 mV)
do. Three devices, three nameplates, three matching peak pack voltages.

At 2919 cycles this device is deep in the ≥1000 band, so the step table
predicts a current target near 4340 mV — but **this cannot be verified**
without a `VacVoltageLimit` record. Older iOS versions may use a different
aggregate set entirely.

### 2. An unexplained sign reversal in the health gap

| Device | Cycles | `NCC / nameplate` | Apple `MaximumCapacityPercent` | Gap |
|--------|--------|-------------------|--------------------------------|-----|
| `iphone-01` | 208 | 99.11% | 101 | +1.89 pp |
| `reference-01` | 1420 | 57.66% | 73 | +15.34 pp |
| **`reference-02`** | **2919** | **71.13%** | **67** | **−4.13 pp** |

The gap **reverses sign** on this device. An earlier version of this repo
attributed that to a replacement battery; **that explanation was withdrawn**
— the owner confirms an original, never-replaced battery. The sign reversal
is currently **unexplained**.

What can be computed is the baseline implied by Apple's figure
(`NCC / (MaximumCapacityPercent/100)`):

| Device | Nameplate | Implied baseline | Baseline / nameplate |
|--------|-----------|------------------|----------------------|
| `iphone-01` | 3692 mAh | 3623 mAh | 0.981 |
| `reference-01` | 2815 mAh | 2223 mAh | 0.790 |
| **`reference-02`** | **3110 mAh** | **3301 mAh** | **1.062** |

On the first two devices Apple's baseline sits **below** the nameplate;
here it sits **6% above** it. That is why the sign flips. Note the implied
3301 mAh is close to `MaximumFCC = 3265 mAh` and `NCCMax = 3211 mAh`, but
with only aggregate values we cannot establish the exact formula — and we
do not guess one.

This still **supports §6** rather than contradicting it: Apple's health
figure is demonstrably not `NCC / nameplate`, and its internal baseline is
not even consistently on the same side of the nameplate across devices.
What it removes is the tidy claim that the gap simply "grows with age" —
with three devices it is clearly device-dependent.

Note also `NCC / AppleRawMaxCapacity = 2212/2272 = 97.36%` while Apple says
67 — another demonstration that Raw is a drifting gauge estimate, not a
health denominator.

### 3. Third confirmation of the +0.04 V cell-vs-pack offset

| Device | Nominal V | Cell energy / mAh | Offset |
|--------|-----------|-------------------|--------|
| `iphone-01` | 3.887 | 3.9271 V | +0.0401 V |
| `reference-01` | 3.83 | 3.8721 V | +0.0421 V |
| **`reference-02`** | **3.83** | **3.8650 V** | **+0.0350 V** |

Three independent nameplates show the cell-energy figure implies a
reference voltage ≈0.04 V above the pack nominal voltage. This is a
consistent specification convention, not a data error.

### 4. Same voltage platform, different capacity

`reference-01` and `reference-02` share **3.83 V / 4.45 V** but differ in
capacity (2815 vs 3110 mAh):

| Ratio | Value |
|-------|-------|
| Capacity | 3110/2815 = **1.1048×** |
| Battery energy | 11.91/10.78 = **1.1048×** |
| Absolute difference | 295 mAh ↔ 1.13 Wh (= 295 mAh at 3.83 V) |

The ratios agree to 4 decimal places, confirming these are the same cell
chemistry at different sizes and that the nameplate energy figures are
internally consistent across the platform.

### 5. Predicted (not measured) voltage ladder

With a 4.45 V nameplate, the same −0.02 V / −0.05 V step table predicts:
4450 / 4430 / 4410 / 4390 / 4340 mV across the 1–199 / 200–249 / 250–299 /
300–999 / ≥1000 bands. `reference-01` measured 4340 mV at 1420 cycles on
this exact platform, so the prediction is well grounded — but **it has not
been measured on this device**: neither supplied file contains a
`VacVoltageLimit` record, even in the larger `Analytics-Never-*` file.

## Status

Nameplate + one gauge snapshot, reference only. No findings were computed
from this device. [`reference.json`](reference.json) holds the whitelisted
values; the raw `.ips` files are not published.
