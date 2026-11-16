# Shallow charging *without* a Charge Limit — what the gauge can and cannot know

**Status**: methodological boundary note, 2026-11-16. No repository conclusions
are overturned; several gain an explicit condition.

## 1. The actual charging method (owner-reported)

The `iphone-01` charging diary (325 sessions, 2026-09-01 … 2026-11-15) never
exceeds 81% SOC. This is **not** iOS's built-in *Charge Limit* feature. The
owner interrupts charging manually with a timer before it reaches 80%.

This distinction matters more than it first appears.

## 2. What Apple actually promises

From [Apple Support 108055 — About Charge Limit and Optimized Battery
Charging on iPhone](https://support.apple.com/en-us/108055):

> If you have Charge Limit set to less than 100 percent, your iPhone will
> occasionally charge to 100 percent to maintain accurate battery
> **state-of-charge** estimates.

Two precise readings:

- It is a **conditional compensation**, bound to the *configured* state
  (`Charge Limit < 100%`). A timer that physically cuts power at ~80% sets no
  such state, so the compensation is **not scheduled**.
- Its stated purpose is **SOC / state-of-charge accuracy** (the remaining-
  charge percentage shown to the user), not capacity, Qmax, FCC or the
  displayed battery-health figure. Apple makes no claim here about those.

An earlier analysis in this repo assumed "firmware must know the device may
never reach full, so it has a general fallback". That is **withdrawn** — see
[`corrections.md` §10](corrections.md). What is true is the weaker statement:
a gauge must tolerate charging being interrupted (anyone can unplug at any
time). What is *not* true is that the periodic full-charge calibration is a
general fallback. It is a feature of Charge Limit mode.

The practical asymmetry:

| Method | High-SOC exposure | Gauge calibration |
|---|---|---|
| iOS Charge Limit 80% | occasional full charges by design | **scheduled compensation full charges** |
| Manual timer cut at ~80% (this device) | **none** | **no scheduled compensation at all** |

The owner's method is physically optimal for cell ageing but metrologically
the least supported: the system believes 100% is allowed, yet every charge is
cut short by an external event.

## 3. Device evidence: no full charge, no calibration, in the 76-day window

Two independent sources, one of them the system's own:

| Evidence | Value | Weight |
|---|---|---|
| `DailyMaxSoc` in all 8 analytics files | `42, 72, 72, 72, 74, 59, 63, 71` — **max 74%, never ≥80%** | strongest: written by iOS itself |
| Charging diary, 325 sessions / 76 days | `soc_end` max **81%**; only **4** sessions ≥80%; longest 8060 s; `anomaly` column empty | covers the whole window |
| `MaximumPackVoltage` | **4496 mV**, constant, lifetime peak from the pre-9/1 era under the ~4.50 V ceiling | confirms a full charge *once existed* before the window; a lifetime max cannot by itself prove none happened later |
| `CycleCountLastQmax` | **138**, identical in all 8 files; `QmaxCell0 = 3824` unchanged | no Qmax learning event during the window |

Caveats kept explicit:

- The extracted analytics whitelist contains **no charge-limit configuration
  field**, so "no Charge Limit is set" rests on the owner's report, not on a
  bit in the data.
- `CycleCountLastQmax` semantics are **not publicly documented**. Note that
  cycle 138 maps to roughly 2026-09-29 … 10-01, *inside* the diary window
  where no full charge occurred — so either Qmax learning does not require
  100%, or the field means something else. Neither reading supports the
  stronger claim "the 80% cap stopped Qmax learning".
- `DailyMaxSoc` covers 8 days only; the diary covers 76.

## 4. Layered impact

| Layer | Driven by | Effect of manual 80% cut |
|---|---|---|
| `CycleCount` | accumulated charge throughput, not "full charges" | **unaffected** — 121→209 with no full charge |
| `VacVoltageLimit` step table | CycleCount | **unaffected** — 4500→4480 fired exactly at cycle 200 |
| `NominalChargeCapacity` | slow model value | noise stays small (±1 mAh), but a **bias** cannot be excluded |
| `AppleRawMaxCapacity` | instantaneous voltage/SOC estimate | **precision degraded**: 3678→3708 (30 mAh), 30× NCC jitter |
| SOC percentage itself | coulomb count + OCV | **no calibration anchor** — this is the layer Apple's compensation exists for |
| `MaximumCapacityPercent` | policy/rounded value | constant 101; **cannot be attributed** to shallow charging vs. deliberate freeze |

Mechanism for the degraded precision: on this device's OCV table the
**50→70%** slope is `8.1 mV/%` while **80→100%** is `18.0 mV/%` — the high
segment carries >2× the information per volt. Permanently capping below 80%
removes the segment a voltage-based capacity fit relies on most. The 30 mAh
Raw jitter and `MaximumFCC/MinimumFCC = 3837/3543` (294 mAh spread) are
consistent with this, but **correlation is not causation**: those are
lifetime aggregates mixed with real ageing and temperature.

## 5. What stays reliable, and what needs a qualifier

**Unaffected** — the whole voltage-step finding and the iphone-01 forecast:
`CycleCount`, the 200/250/300/≥1000 nodes, `NCC/3692`, the A/B proof that
derating is reversible lock-in, and the 1.30 cycles/day curve. None of them
requires a full charge or a calibrated SOC readout. The
`MaximumPackVoltage = 4496 mV` fossil interpretation is actually strengthened.

**Needs an explicit qualifier** — any inference that treats
`AppleRawMaxCapacity`, `QmaxCell0`, `CycleCountLastQmax` or the constant
`MaximumCapacityPercent = 101` as ground truth. All were observed in a
76-day window with **no full charge and no scheduled calibration**.

**Newly flagged risk — propagation into the usage rate.** The primary usage
figure `4801 mAh/day = 1.30 cycles/day` comes from `sum(charged_pct) = 9883%`
over the diary. `charged_pct` is a difference of *displayed* SOC integers, so
a **gain error** in SOC estimation would scale it proportionally (a pure
offset error cancels in the difference). The independent analytics regression
gives 1.233 cycles/day, ~5% lower. That gap is consistent with a small SOC
gain error — but it is **not a clean test**: `CycleCount` is also coulomb-
count based and may share the same error source, and the two cover different
windows. Recorded as a hypothesis, not a finding.

## 6. Honest boundary

Precision (scatter) is measurable; **accuracy (bias) is not measurable from
this dataset**. Detecting it requires a full-charge reference event — exactly
the thing this usage pattern never produces. Nothing here proves the health
figures are wrong. It says only that the mechanism Apple designed to keep SOC
estimates accurate is not running.

## 7. Decisive experiment

Two options, both requiring one deliberate full charge:

- **Manual A/B (fast, controlled)**: let one session run to 100% and rest,
  export analytics before/after.
- **Enable Charge Limit 80% temporarily (uses Apple's own mechanism)**: wait
  for the system-scheduled compensation full charge. Slower (days), and
  changes the configuration state, but exercises the real calibration path.

Fields to compare: `DailyMaxSoc`, `CycleCountLastQmax`, `QmaxCell0`,
`AppleRawMaxCapacity`, `NominalChargeCapacity`, `MaximumCapacityPercent`,
`MaximumFCC/MinimumFCC`, and a displayed-SOC vs. known-charge check.
`MaximumPackVoltage` is **expected to stay 4496**: it is a lifetime maximum
and the current 4480 mV target cannot exceed it.

Cost: one high-voltage stress event and a break in the 76-day clean baseline.
The A/B experiment in this repo showed Qmax does not change with charge-limit
voltage, so the cell-level effect is reversible — but stamp the date and keep
it out of the forecast curve.
