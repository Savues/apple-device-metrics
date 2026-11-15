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

## Decisive follow-up

Charge to 100%, disconnect, rest 10–20 minutes, then read terminal voltage:

| Reading | Interpretation |
|---------|----------------|
| **4.48 V** | 200-cycle step-down is active → cycle-node mechanism confirmed |
| **4.50 V** | step-down not active on this device → the 2026-11-15 −0.43 pp step needs another explanation |

Also worth checking whether `charge_limit_voltage_v` in the analytics is a
static nameplate field or the live software target: if it becomes 4.46 V
after cycle 250, that is direct evidence without the 100% test.

See [`docs/voltage-nodes.md`](../docs/voltage-nodes.md).
