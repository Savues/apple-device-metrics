# Reference device — cross-check only

A second device's analytics file was supplied **for reference**. It is kept
in a separate directory and is deliberately **not** merged into the
`iphone-01` timeline, health CSV, or any of the findings' statistics.

| | `iphone-01` (main) | `reference-01` (this device) |
|---|---|---|
| iOS | 26.4.2 | **17.6.1** |
| **Rated capacity (nameplate)** | **3692 mAh** | **2815 mAh** |
| **Nominal voltage** | **3.887 V** | **3.83 V** |
| **Charge limit (nameplate)** | **4.50 V** | **4.45 V** |
| **Cell / battery energy** | **14.499 / 14.351 Wh** | **10.90 / 10.78 Wh** |
| Analytics date | 11-09 … 11-15 (7 files) | 2026-11-15 (1 file) |
| Cycles | 200 → 208 | **1420** |
| `VacVoltageLimit` | 4480 mV | **4340 mV** |
| `MaximumPackVoltage` (lifetime peak) | 4496 mV | **4450 mV** |
| `MaximumCapacityPercent` | 101 | **73** |
| `AppleRawMaxCapacity` | 3678–3708 mAh | 1650 mAh |
| `NominalChargeCapacity` | 3658–3659 mAh | 1623 mAh |
| `WeightedRa` | 75–77 | 468 |
| `TotalOperatingTime` | 4780–4928 h | 54014 h |

Both nameplates satisfy `battery_energy = nominal_voltage × rated_capacity`
exactly (14.351 Wh and 10.781 Wh). The cell-energy figures imply a voltage
~0.04 V above nominal on both devices, i.e. the cell rating uses a higher
reference voltage than the pack rating.

Only a whitelist of numeric fields is stored in
[`reference.json`](reference.json). The raw `.ips` contains deviceId, UUIDs,
incident_id, carrier/country and SKU, so it is not published.

---

## 1. Independent confirmation of the cycle-node voltage table

The manufacturer nameplate for this device gives a charge limit of
**4.45 V**. Applying the third-party node steps (−0.02 V at 200/250/300 and
an extra −0.05 V at ≥1000):

| Band | Limit |
|------|-------|
| 1–199 (nameplate) | **4450 mV** |
| 200–249 | 4430 mV |
| 250–299 | 4410 mV |
| 300–999 | 4390 mV |
| ≥1000 (**predicted**) | **4340 mV** |

The predicted ≥1000 value **equals the measured `VacVoltageLimit = 4340 mV`
exactly**. And 4450 mV also equals this device's lifetime
`MaximumPackVoltage = 4450 mV` — a separate field. So the ladder is
validated in **both directions** from a known nameplate, not merely
back-projected.

On `iphone-01` the same arithmetic holds with its 4.50 V nameplate:
4.50 → 4.48 V at cycle 200, matching the measured 4480 mV at exactly
`CycleCount = 200`, and 4496 mV lifetime peak sits just below 4500 mV.

**Two nameplates, two independent iOS versions, two cell platforms, one
consistent step table.** This substantially strengthens the −0.02 V /
−0.05 V step sizes. Note the absolute voltages are platform-relative
(4.50 V vs 4.45 V top rung), so the table must be applied per device, not
as a universal absolute ladder. It is still not Apple-official
documentation — the node boundaries and step sizes remain third-party
reverse-engineering that happens to fit both devices exactly.

## 2. Strong support for §6 (two different health numbers)

`reference-01` makes the distinction impossible to miss. With its
manufacturer nameplate (2815 mAh / 3.83 V / 4.45 V), the comparison against
`iphone-01` (3692 mAh / 3.887 V / 4.50 V) is now apples-to-apples:

| Quantity | `reference-01` | `iphone-01` |
|----------|----------------|-------------|
| `NCC / rated capacity` | 1623/2815 = **57.66%** | 3659/3692 = **99.11%** |
| `MaximumCapacityPercent` (Apple) | **73** | **101** |
| Gap | **+15.34 pp** | **+1.89 pp** |

The gap is not a fixed offset: it grows ~8× as the battery ages. That rules
out "different rounding" and confirms Apple's health figure uses its own
calibrated baseline (and likely a different ageing model), not a plain
division by the nameplate rated capacity.

`NCC / AppleRawMaxCapacity` here is 1623/1650 = 98.36%, which is *not* the
health figure either — Raw is a drifting gauge estimate (§5-6 of the main
evidence doc), so that ratio is meaningless as health.

Also note `MaximumFCC = 2311` and `MinimumFCC = 64` are lifetime extremes,
not the current capacity; using either as a health denominator would be
wrong. An `AppleRawMaxCapacity`-derived "design capacity" of ~2223 mAh
(1623/0.73) has no counterpart among the published nameplate fields.

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
