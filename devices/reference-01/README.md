# Reference device — cross-check only

A second device's analytics file was supplied **for reference**. It is kept
in a separate directory and is deliberately **not** merged into the
`iphone-01` timeline, health CSV, or any of the findings' statistics.

| | `iphone-01` (main) | `reference-01` (this device) |
|---|---|---|
| iOS | 26.4.2 | **17.6.1** |
| Analytics date | 11-09 … 11-15 (7 files) | 2026-11-15 (1 file) |
| Cycles | 200 → 208 | **1420** |
| `VacVoltageLimit` | 4480 mV | **4340 mV** |
| `MaximumPackVoltage` (lifetime peak) | 4496 mV | **4450 mV** |
| `MaximumCapacityPercent` | 101 | **73** |
| `AppleRawMaxCapacity` | 3678–3708 mAh | 1650 mAh |
| `NominalChargeCapacity` | 3658–3659 mAh | 1623 mAh |
| `WeightedRa` | 75–77 | 468 |
| `TotalOperatingTime` | 4780–4928 h | 54014 h |

Only a whitelist of numeric fields is stored in
[`reference.json`](reference.json). The raw `.ips` contains deviceId, UUIDs,
incident_id, carrier/country and SKU, so it is not published.

---

## 1. Independent confirmation of the cycle-node voltage table

At 1420 cycles this device is in the **≥1000** band. Working backwards with
the third-party step sizes (−0.02 V at 200/250/300, −0.05 V at ≥1000):

| Band | Inferred limit |
|------|----------------|
| ≥1000 (**measured**) | **4340 mV** |
| 300–999 | 4390 mV |
| 250–299 | 4410 mV |
| 200–249 | 4430 mV |
| 1–199 | **4450 mV** |

The inferred first-band value **4450 mV exactly matches this device's
lifetime `MaximumPackVoltage = 4450 mV`** — a completely independent field.
Two devices on different iOS versions and different cell platforms both
land on a self-consistent ladder whose top rung equals the observed peak
pack voltage. This does not prove the table is Apple-official, but it makes
the step sizes (−0.02 V, −0.05 V at ≥1000) substantially more credible than
the single-device evidence alone.

Note the top rung differs between devices (4500 mV on `iphone-01`, 4450 mV
here), i.e. the table is **platform-relative**, not a universal absolute
voltage. This is consistent with the variant accounts in
[`docs/voltage-nodes.md`](../../docs/voltage-nodes.md).

## 2. Strong support for §6 (two different health numbers)

`reference-01` makes the distinction impossible to miss:

| Quantity | Value |
|----------|-------|
| `MaximumCapacityPercent` (Apple's displayed health) | **73** |
| `NCC / AppleRawMaxCapacity` | 1623/1650 = **98.36%** |
| Gap | **25 pp** |

On `iphone-01` the same gap is only 1.89 pp (101 vs 99.11), easy to dismiss
as calibration noise. On a heavily aged 1420-cycle battery it becomes 25 pp,
which confirms the two figures use **different baselines**, not just different
rounding. Apple's internal baseline here is roughly 1623/0.73 ≈ 2223 mAh,
far above `AppleRawMaxCapacity` (1650) and `QmaxCell0` (1975) — so it is not
any of the published mAh fields.

Also note `MaximumFCC = 2311` and `MinimumFCC = 64` are lifetime extremes,
not the current capacity; using either as a health denominator would be
wrong.

## 3. Ageing signals that `iphone-01` does not yet show

| Signal | `reference-01` | `iphone-01` |
|--------|----------------|-------------|
| `WeightedRa` (internal resistance) | **468** | 75–77 |
| `MinimumFCC` (lifetime low) | **64 mAh** | 3543 mAh |
| `CycleCountLastQmax` | 57 | 138 |

`WeightedRa` ~6× higher and the extreme `MinimumFCC` are consistent with a
1420-cycle / 73%-health battery. These are the quantities that would
eventually change on `iphone-01` as it ages; tracking them in future
analytics files is worthwhile.

---

## Status

Reference only. No conclusions in
[`docs/findings.md`](../../docs/findings.md) were computed from this device.
`scripts/verify.py` checks its whitelisted fields for consistency.
