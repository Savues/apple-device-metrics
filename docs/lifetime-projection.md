# Lifetime projection after the voltage step-down

This document replaces the linear extrapolation that was withdrawn in
[`corrections.md`](corrections.md) §4. It separates three things that are
easy to conflate: **displayed health**, **usable capacity per charge**, and
**chemical ageing rate**.

> ⚠️ **For the main device's future curve, use
> [`iphone17-forecast.md`](iphone17-forecast.md) instead.** Per the owner,
> the two reference devices had irregular usage and must not be used to fit
> `iphone-01`'s trajectory. The cross-device anchors in §1A below are kept
> as general context only, **not** as a prediction for this device.
>
> ⚠️ **Correction (2026-11-15)**: an earlier version of this document used
> Apple's "80% at 1000 cycles" specification as a straight ageing anchor.
> That was wrong — see §0 and [`corrections.md`](corrections.md) §8. The
> displayed health figure already contains a **reversible voltage-lock**
> component, so it is not a pure chemical-ageing curve.

All figures are projections, not measurements. Ranges are given where the
underlying relationship is uncertain.

---

## 0. Why the official 1000-cycle / 80% must not be applied directly

Two screenshots of a diagnostic tool show **the same original iPhone 16 Pro
Max battery, at cycle 0**, measured twice with only the configured charge
voltage limit changed. Full data:
[`voltage-capacity-experiment.json`](voltage-capacity-experiment.json).

| | A | B | Δ |
|---|---|---|---|
| Voltage limit | 4500 mV | **4390 mV** | −110 mV |
| Actual capacity | 4799 mAh (103.6%) | 4428 mAh (95.6%) | **−371 mAh / −8.0 pp** |
| Full-charge capacity | 4761 mAh | 4391 mAh | −370 mAh |
| **Qmax (chemical capacity)** | **4939 mAh** | **4939 mAh** | **0** |
| Cycles / voltage / current / temp | 0 / 3.938 V / 0 / 23.3 °C | identical | — |

**Qmax does not move.** Changing the voltage limit alone removed 8.0 pp from
the reported capacity without any chemical change — it is a **reversible
charge-limit effect**, not ageing. A 4.08 V reading also appears in both
screenshots; per the owner it is the battery's current level/voltage and is
irrelevant to the comparison (the independent variable is the configured
voltage limit: 4500 vs 4390 mV).

Critically, 4500 mV → 4390 mV is exactly the span from `iphone-01`'s top
band to the extrapolated ≥1000 band. So this is a directly relevant
empirical calibration, not a generic guess.

**Consequence for the 80% figure.** If a 1000-cycle battery has accumulated
−110 mV of derating, then of the ~20 pp drop from 100% to 80%:

| Component | Magnitude | Share |
|-----------|-----------|-------|
| Reversible voltage lock | ≈ **8.0 pp** | ~40% |
| Genuine chemical ageing | ≈ **12.0 pp** | ~60% |

So **"80% at 1000 cycles" is a displayed-number commitment, not a
measurement of cell wear**. Treating it as an ageing anchor overstates real
degradation by roughly two thirds, and treating 80% as an end-of-life
threshold is wrong: a meaningful part of that loss can be restored by
raising the limit (BU-808 explicitly notes the capacity returns).

This is also why the three-device "concave curve" below must be read with
care — its later anchors include accumulated lock-in, not just chemistry.

---

## 1. Three different curves

### A. Displayed health (`MaximumCapacityPercent`)

Measured anchors (different platforms, different usage — indicative only,
**not** a fitted ageing curve):

| Cycles | Apple health | Device |
|--------|--------------|--------|
| 208 | 101 | `iphone-01` (measured) |
| 1420 | 73 | `reference-01` (measured) |
| 2919 | 67 | `reference-02` (measured) |

Apple's **80% at 1000 cycles** is shown separately as a *design target for
the displayed figure*, not as an interpolation point — see §0.

Raw slopes between anchors (include both ageing and lock-in):

| Interval | Slope |
|----------|-------|
| 208 → 1420 | −2.31 pp / 100 cycles |
| 1420 → 2919 | **−0.40 pp / 100 cycles** |

**The displayed curve is strongly concave: fast early loss, then a long flat
tail.** But part of that early loss is the voltage-lock steps (§0), not
chemistry. A linear fit through the first 208 cycles still overstates
long-term degradation — that is why the 0.0165 %/day extrapolation was
withdrawn — but the "concavity" must not be interpreted as a pure ageing
law either.

At **1.30 cycles/day** from 212 cycles on 2026-11-17 (this document is
general context, not the iphone-01 forecast — see
[`iphone17-forecast.md`](iphone17-forecast.md) for that):

| Node | Expected date | Note |
|------|---------------|------|
| 250 cycles | ~2026-12-16 | 2nd voltage step (4460 mV) |
| 300 cycles | ~2027-01-23 | 3rd step (4440 mV) |
| 500 cycles | ~2027-06 | — |
| **1000 cycles** | **~2028-07-15** | ≥1000 step (extrapolated 4390 mV) |

### B. Usable capacity per full charge

Each −0.02 V step lowers the charge ceiling, so a "100%" charge holds
slightly less energy. The A/B experiment in §0 now **measures** this slope
on the same 4.50 V platform, replacing the earlier generic range:

| Basis | −110 mV total ⇒ capacity cost |
|-------|-------------------------------|
| OCV slope 0.020 V/SOC point (earlier rough estimate) | ≈ −5.5 pp |
| [BU-808](https://batteryuniversity.com/article/bu-808-how-to-prolong-lithium-based-batteries) 70 mV ≈ 10% (conventional 4.20 V Li-ion) | ≈ −15.7 pp |
| **Measured A/B (§0), 4.50 V platform** | **−8.0 pp** |
| → measured slope | **1.46 pp per 20 mV node** (3.37 mAh/mV on that cell) |

BU-808's guideline is for conventional 4.20 V cobalt-based cells, so its
−15.7 pp is not applicable; the measured value lands between the two
earlier estimates, closer to the rough one. Applied to `iphone-01`:

| Node | Cumulative derating | Lock-in cost |
|------|---------------------|--------------|
| 200 | −20 mV | −1.46 pp |
| 250 | −40 mV | −2.91 pp |
| 300 | −60 mV | −4.37 pp |
| 1000 | −110 mV | **−8.01 pp** |

Caveat: the A/B used a 4630 mAh iPhone 16 Pro Max cell; the slope is
transferred as a **percentage**, assuming a similar OCV shape on the same
4.50 V platform. Single measurement, no error bars.

Crucially, this is **reversible**: Qmax was identical in A and B, and BU-808
notes that restoring the peak charge voltage restores the capacity. It is a
charge-limit choice, not chemical damage — so it should not be counted as
"lost battery life".

### C. Chemical ageing rate — the reason for the step-down

Lowering the upper cut-off voltage **reduces** degradation; it does not
accelerate it. BU-808: *every 0.10 V reduction below 4.20 V/cell roughly
doubles cycle life*, and voltage above 4.10 V is "high voltage" stress.
Academic work agrees (e.g. "Flexible upper cut-off voltage regulation for
life extension of lithium-ion batteries", *Journal of Energy Storage*,
2025). Applying the exponential relation to the cumulative derating:

| Cycles | Cumulative −V | Theoretical cycle-life multiplier |
|--------|---------------|-----------------------------------|
| 200 | 0.02 V | ×1.15 |
| 300 | 0.06 V | ×1.52 |
| 1000 | 0.11 V | **×2.14** |

These multipliers apply to conventional Li-ion and are **indicative of
direction, not a quantitative prediction** for this cell. But the sign is
unambiguous: the step-down **trades a small amount of per-charge runtime
for a substantially slower ageing rate**. The derating is part of how Apple
keeps the displayed figure within its 1000-cycle commitment — it is not a
penalty on top of ageing.

---

## 2. So what happens to this battery?

**Short term (next 2 months).** Two more small steps at 250 and 300 cycles,
each ~−0.4 pp on the NCC-derived ratio, with flat plateaus between. Apple's
displayed `MaximumCapacityPercent` may not move at all — it stayed at 101
through the 200-cycle step. Cumulative reversible lock-in reaches ≈ −4.4 pp
by 300 cycles; per-charge runtime drops only a few percent. Nothing the
user will notice.

**Medium term (500–1000 cycles, ~2027–2028).** Note this section draws on
cross-device context only. The iphone-01-only forecast
([`iphone17-forecast.md`](iphone17-forecast.md)) puts NCC health at ~94.9%
(3506 mAh) at 1000 cycles and does **not** reach 80% in the modelled window.
Where a displayed 80% does occur, per §0 a large part of it is reversible
lock-in rather than wear, so it is neither a pure wear measure nor an
end-of-life threshold.

**Long term (>1000 cycles).** Reference devices at 1420 and 2919 cycles
still report 73% and 67%. A battery is usable well beyond 1000 cycles. With
this owner's habit of **unplugging before the 80% Charge Limit, with shallow 20–70% top-ups** (documented in
`findings.md` §3), the effective stress is lower still — the log shows the
device never once reached a full charge in 76 days, which is itself a
strong life-extension factor (BU-808 Table 2: shallower depth of discharge
gives dramatically more cycles).

**Bottom line: the observed behaviour is protective, not deteriorating.**
The step-down costs a few percent of runtime per charge and buys a flatter
ageing curve; most of the *displayed* health loss is reversible lock-in, not
wear. At 212 cycles / 99.13% (NCC ratio) / 101 (Apple health), the battery
is in excellent condition and is not the limiting factor for the device's
useful life. The official 1000-cycle / 80% number should be read as a
displayed-value commitment, not a prediction of when the cell is worn out.

---

## 3. What would actually shorten its life

Per BU-808 Tables 3–4, the dominant stressors are **high temperature at
high state of charge** and **full-depth cycling**, not cycle count alone:

| Stress | Example impact (BU-808 Table 3, 1 year storage) |
|--------|--------------------------------------------------|
| 25 °C, 40% charge | 96% retained |
| 25 °C, 100% charge | **80% retained** |
| 40 °C, 100% charge | **65% retained** |

Current habits avoid the worst case. Things that would matter more than the
voltage nodes: leaving the phone hot while charging, sustained 100% SOC in
a hot environment, and high-current fast charging.

---

## 4. Confidence and open items

| Claim | Confidence |
|-------|------------|
| Step-down is active at exactly cycle 200 (−0.02 V) | **High** — direct analytics measurement |
| Next nodes at 250 / 300 | Medium — third-party table, platform now confirmed (iPhone 17) |
| ≥1000 step to 4390 mV | **Low** — extrapolated from the iPhone 13 series; no 17-series ≥1000 value published |
| Usable-capacity cost per step | **Medium** — measured A/B slope 1.46 pp / 20 mV node (§0), transferred as a percentage from a 4630 mAh cell; no error bars |
| 80% at 1000 cycles contains ~8 pp reversible lock-in | Medium — combines measured slope with the extrapolated 4390 mV ≥1000 band |
| Displayed curve is concave | Medium — two measured anchors (1420, 2919), but different platforms; partially lock-in, not pure ageing |
| Derating slows chemical ageing | **High (direction)** — well-established electrochemistry; magnitude not quantified for this cell |
| Dates for future nodes | Medium — assumes 1.30 cycles/day (current measured usage) continues |

Revisit after the 250-cycle node (~2026-12-16): a new analytics snapshot
will show whether `VacVoltageLimit = 4460 mV` and whether displayed health
moves at all.

## References

- [Battery University BU-808: How to Prolong Lithium-based Batteries](https://batteryuniversity.com/article/bu-808-how-to-prolong-lithium-based-batteries) — Tables 2–4, 70 mV ≈ 10% capacity, 0.10 V ≈ 2× cycle life.
- *Flexible upper cut-off voltage regulation for life extension of
  lithium-ion batteries*, Journal of Energy Storage (2025), and *Upper
  cut-off voltage regulation to balance battery lifespan and energy* (2026)
  — both report that lowering UCV extends cycle life at the cost of usable
  energy. Search by title; no direct PII is asserted here.
- [`docs/voltage-nodes.md`](voltage-nodes.md) — node table and its third-party status.
- [`docs/voltage-capacity-experiment.json`](voltage-capacity-experiment.json) — A/B measurement of voltage limit vs reported capacity (§0).
- [`docs/corrections.md`](corrections.md) §4 (withdrawn linear extrapolation) and §8 (withdrawn use of the 80% specification as an ageing anchor).
