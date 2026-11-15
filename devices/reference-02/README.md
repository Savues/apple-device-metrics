# Reference device 2 — nameplate only

A third device was supplied with its manufacturer nameplate. Its analytics
file is an `Analytics-Daily-*` report that contains **no battery gauge
records**, so this device contributes nameplate data only. It is kept
separate and is not merged into `iphone-01` or any statistics.

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

## What the analytics file contains

70 NDJSON records of `bug_type 211`: `JetsamAggregationV3` (17),
`WlpFixApsCountPerScanType1` (17), `HomeKitDailyErrorAggregationV5` (13),
Health/menstrual-cycle aggregates, `CableTypeChangedV2` and
`PowerlogTaskingReport`. **Zero** occurrences of `CycleCount`,
`NominalChargeCapacity`, `MaximumCapacityPercent`, `AppleRawMaxCapacity`,
`VacVoltageLimit` or `PackVoltage`.

`scripts/extract_analytics.py` will refuse such a file with
`missing required records` — that is expected and correct. Do not treat
this as a parse failure.

## Value despite having no gauge data

### 1. Third confirmation of the +0.04 V cell-vs-pack offset

| Device | Nominal V | Cell energy / mAh | Offset |
|--------|-----------|-------------------|--------|
| `iphone-01` | 3.887 | 3.9271 V | +0.0401 V |
| `reference-01` | 3.83 | 3.8721 V | +0.0421 V |
| **`reference-02`** | **3.83** | **3.8650 V** | **+0.0350 V** |

Three independent nameplates show the cell-energy figure implies a
reference voltage ≈0.04 V above the pack nominal voltage. This is a
consistent specification convention, not a data error.

### 2. Same voltage platform, different capacity

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

### 3. Predicted (not measured) voltage ladder

With a 4.45 V nameplate, the same −0.02 V / −0.05 V step table predicts:
4450 / 4430 / 4410 / 4390 / 4340 mV across the 1–199 / 200–249 / 250–299 /
300–999 / ≥1000 bands. `reference-01` measured 4340 mV at 1420 cycles on
this exact platform, so the prediction is well grounded — but **it has not
been measured on this device**. A full `Analytics-*` file (not
`Analytics-Daily-*`) with `BatteryConfigValueHistogramFinal_V2` and
`VacVoltageLimit` would be needed.

## Status

Nameplate reference only. No findings were computed from this device.
[`reference.json`](reference.json) holds the whitelisted values; the raw
`.ips` is not published.
