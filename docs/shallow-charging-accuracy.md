# Charge Limit 80% enabled, but always unplugged before 80% — what the gauge can and cannot know

**Status**: methodological boundary note, revised 2026-11-16 (second
correction, see [`corrections.md` §11](corrections.md)). No repository
conclusions are overturned; several gain an explicit condition.

## 1. The actual charging method

Two facts, neither of them visible in the data:

1. iOS **Charge Limit is enabled and set to 80%**. It is a safety net, not
   the normal stopping point.
2. In practice the session ends **before 80%** on essentially every charge.

The data agree. The <!--v:span_days-->85<!--/-->-day diary (<!--v:sessions-->357<!--/--> sessions since 2026-09-01)
never exceeds 81% SOC, and only 4 sessions end at ≥80% (80/80/80/81). Those
four are consistent with the limit catching a late unplug. Termination piles
up at <!--v:top_a-->69<!--/-->% (<!--v:top_a_n-->46<!--/--> sessions) and <!--v:top_b-->75<!--/-->% (<!--v:top_b_n-->28<!--/--> sessions).

The date Charge Limit was switched on is **not recorded**. The analytics
whitelist has no charge-limit configuration field, so the setting itself
rests on the configuration as reported, not on a bit in the data.

An earlier revision of this note said Charge Limit was **not** enabled. That
was wrong and is withdrawn ([`corrections.md` §11](corrections.md)).

## 2. What Apple actually promises

From [Apple Support 108055 — About Charge Limit and Optimized Battery
Charging on iPhone](https://support.apple.com/en-us/108055):

> If you have Charge Limit set to less than 100 percent, your iPhone will
> occasionally charge to 100 percent to maintain accurate battery
> **state-of-charge** estimates.

Two precise readings:

- The compensation is bound to the configured state `Charge Limit < 100%`.
  On this device that state **is set**, so the mechanism is armed.
- Its stated purpose is **SOC accuracy** (the remaining-charge percentage),
  not capacity, Qmax, FCC or the displayed health figure. Apple makes no
  claim about those.

Apple does not say *when* or *how* the occasional 100% charge happens. It
can only happen while the phone is on the charger. A charge that is always
ended below 80% leaves the system no session in which to run
past the limit.

| Method | Calibration mechanism | Can it complete? |
|---|---|---|
| Charge Limit 80%, left plugged in | armed | yes, occasionally reaches 100% by design |
| **Charge Limit 80%, unplugged before 80% (this device)** | **armed** | **no observed instance in <!--v:span_days-->85<!--/--> days**: every session ends before the limit is reached |
| No Charge Limit, unplugged before 80% | not armed | no |

So the practical outcome matches the "no calibration" case even though the
configuration matches the "calibrated" case. Physically this is the
gentlest pattern for the cell. Metrologically, the calibration Apple designed
is configured but pre-empted.

## 3. Device evidence: no full charge, no calibration, in the <!--v:span_days-->85<!--/-->-day window

| Evidence | Value | Weight |
|---|---|---|
| `DailyMaxSoc` in all <!--v:snap_n-->16<!--/--> analytics files | <!--v:maxsoc_list-->`42, 72, 72, 72, 74, 59, 63, 71, 69, 69, 75, 74, 77, 75, 41, 58`<!--/-->: **max <!--v:maxsoc_max-->77<!--/-->%, never ≥80%** | strongest: written by iOS itself, but covers <!--v:snap_n-->16<!--/--> days only |
| Charging diary, <!--v:sessions-->357<!--/--> sessions / <!--v:span_days-->85<!--/--> days | `soc_end` max **81%**; only **4** sessions ≥80% | covers the whole window |
| `MaximumPackVoltage` | **4496 mV**, constant, lifetime peak from before 09-01 under the ~4.50 V ceiling | confirms a full charge once existed before the window; a lifetime max cannot by itself prove none happened later |
| `CycleCountLastQmax` | **138**, identical in all <!--v:snap_n-->16<!--/--> files; `QmaxCell0 = 3824` unchanged | no Qmax learning event during the <!--v:snap_n-->16<!--/--> analytics days |

Caveats kept explicit:

- The Charge Limit setting and its start date are reported, not recorded in the data.
- `CycleCountLastQmax` semantics are **not publicly documented**. Cycle 138
  maps to roughly 2026-09-29 … 10-01, *inside* the diary window where no full
  charge occurred. So either Qmax learning does not require 100%, or the
  field means something else. Neither reading supports the stronger claim
  "the 80% cap stopped Qmax learning".
- iOS might recalibrate SOC by means other than a 100% charge (for example
  resting OCV). Nothing in the data shows whether it does.

## 4. Layered impact

| Layer | Driven by | Effect of always stopping below 80% |
|---|---|---|
| `CycleCount` | accumulated charge throughput, not "full charges" | **unaffected**: 121→<!--v:base_cycle-->220<!--/--> with no full charge |
| `VacVoltageLimit` step table | CycleCount | **unaffected**: 4500→4480 fired exactly at cycle 200 |
| `NominalChargeCapacity` | slow model value | noise stays small (±1 mAh), but a **bias** cannot be excluded |
| `AppleRawMaxCapacity` | instantaneous voltage/SOC estimate | **precision degraded**: 3678→3708 (30 mAh), 30× NCC jitter |
| SOC percentage itself | coulomb count + OCV | **no observed calibration anchor**: the layer Apple's compensation exists for |
| `MaximumCapacityPercent` | policy/rounded value | constant 101; **cannot be attributed** to shallow charging vs. deliberate freeze |

Mechanism for the degraded precision: on this device's OCV table the
**50→70%** slope is `8.1 mV/%` while **80→100%** is `18.0 mV/%`, so the high
segment carries more than twice the information per volt. Never charging
above 80% removes the segment a voltage-based capacity fit relies on most.
The 30 mAh Raw jitter and `MaximumFCC/MinimumFCC = 3837/3543` (294 mAh
spread) are consistent with this, but **correlation is not causation**: those
are lifetime aggregates mixed with real ageing and temperature.

## 5. What stays reliable, and what needs a qualifier

**Unaffected**: `CycleCount`, the 200/250/300/≥1000 voltage nodes and their
timing, `NCC/3692` as a definition, the A/B proof that derating is reversible
lock-in, and the *shape* of the iphone-01 forecast curve (plateau + node
steps). None of them needs a full charge or a calibrated SOC readout. The
`MaximumPackVoltage = 4496 mV` fossil interpretation is strengthened: with
the target now 4480 mV, even a future calibration full charge cannot exceed
it.

**Needs an explicit qualifier**:

- `AppleRawMaxCapacity`, `QmaxCell0`, `CycleCountLastQmax` and the constant
  `MaximumCapacityPercent = 101` as ground truth. All were observed with **no
  completed calibration** in the window.
- **The usage rate `<!--v:rate-->1.29<!--/--> cycles/day = <!--v:mah_day-->4769<!--/--> mAh/day`, and therefore the
  forecast's calendar dates.** It comes from `sum(charged_pct) = <!--v:charged_sum-->10980<!--/-->%`.
  `charged_pct` is a difference of *displayed* SOC integers, so a **gain
  error** in SOC estimation scales it proportionally (a pure offset error
  cancels in the difference). The analytics regression gave 1.233
  cycles/day (5% lower) on 8 files, and **1.324 (2% higher)** after the
  11-17 file added +3 cycles in one gauge write. The sign flipped with one
  data point, so the gap is within sampling noise and gives **no evidence**
  of an SOC gain error either way. It was never a clean test: `CycleCount` is also based on
  coulomb counting and may share the same error source, and the two cover
  different windows. Recorded as a hypothesis, not a finding.

## 6. Honest boundary

Precision (scatter) is measurable; **accuracy (bias) is not measurable from
this dataset**. Detecting it requires a full-charge reference event, which
this usage pattern never produces. Nothing here proves the health figures are
wrong. It says only that the calibration Apple configured is not observed to
run.

## 7. Decisive experiment

Charge Limit is already on, so the cheapest test uses Apple's own path:

- **Let the system calibrate (preferred)**: on a few nights, leave the phone
  on the charger instead of unplugging before 80%. Charge Limit normally stops
  it at 80%; if iOS schedules its occasional 100% charge, `DailyMaxSoc` will
  show it. This tests the real mechanism, but timing is up to iOS and may take
  many nights.
- **Manual A/B (fast, controlled)**: temporarily set the limit to 100%, run
  one session to full and rest, export analytics before and after, then set
  80% again.

Fields to compare: `DailyMaxSoc`, `CycleCountLastQmax`, `QmaxCell0`,
`AppleRawMaxCapacity`, `NominalChargeCapacity`, `MaximumCapacityPercent`,
`MaximumFCC/MinimumFCC`, and a displayed-SOC vs. known-charge check.
`MaximumPackVoltage` is **expected to stay 4496**: it is a lifetime maximum
and the current 4480 mV target cannot exceed it.

Cost: one high-SOC event and a break in the clean below-80% baseline. The A/B
experiment in this repo showed Qmax does not change with charge-limit
voltage, so the cell-level effect is reversible. Stamp the date and keep the
event out of the forecast fit. `verify.py` will fail on import (no session
≥95%, no `DailyMaxSoc` >81%) so the break cannot go unnoticed.
