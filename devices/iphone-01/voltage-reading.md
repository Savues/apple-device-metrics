# Voltage reading — 2026-11-15

| Quantity | Value |
|----------|-------|
| Terminal voltage | **4.04 V** |
| Reported SOC | **70%** |
| Cycle count (same day, 08:00 snapshot) | 208 |
| Conditions | single manual reading; loaded terminal voltage, not resting OCV |
| Nameplate | 3.887 V nominal / 3692 mAh / 4.50 V charge limit |

## OCV consistency check

Typical OCV–SOC points for a 4.5 V-class high-voltage cell (indicative, not
measured for this cell):

| SOC | OCV |
|-----|-----|
| 50% | 3.887 V |
| 60% | 3.97 V |
| **70%** | **4.05 V** |
| 80% | 4.14 V |
| 90% | 4.30 V |
| 100% | 4.50 V |

Interpolated: **4.04 V ≈ 68.8% SOC**. Expected ~4.05 V at 70%; offset
−0.01 V, consistent with a light load sag. No voltage collapse or elevated
internal resistance is indicated — the cell itself looks healthy.

## What this reading cannot tell us

- It is a **loaded terminal voltage**, not a resting OCV.
- A mid-SOC point cannot distinguish a 4.50 V from a 4.48 V full-charge
  target: the difference is absorbed by SOC re-baselining well below 100%.
- A single point cannot establish an OCV curve for this cell.

## Follow-up status (resolved)

**The 100% test is no longer needed.** The 2026-11-15 analytics file reports
`VacVoltageLimit = 4480 mV` at cycle 208, directly confirming the 200-cycle
step-down. See [`ANALYTICS-EVIDENCE.md`](ANALYTICS-EVIDENCE.md).

This mid-SOC reading remains useful only as a sanity check that the cell has
no voltage collapse or elevated internal resistance.

The **before** value cannot be read directly: iOS keeps only ~7–8 days of
analytics, so no pre-200 snapshot exists. As indirect evidence, the lifetime
`MaximumPackVoltage = 4496 mV` is 16 mV above the current 4480 mV target and
can only have been recorded under the earlier ~4.50 V ceiling. See
[`ANALYTICS-EVIDENCE.md`](ANALYTICS-EVIDENCE.md) §1.1.
