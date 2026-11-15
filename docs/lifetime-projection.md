# Lifetime projection after the voltage step-down

This document replaces the linear extrapolation that was withdrawn in
[`corrections.md`](corrections.md) §4. It separates three things that are
easy to conflate: **displayed health**, **usable capacity per charge**, and
**chemical ageing rate**.

All figures are projections, not measurements. Ranges are given where the
underlying relationship is uncertain.

---

## 1. Three different curves

### A. Displayed health (`MaximumCapacityPercent`)

Apple's public specification is **80% at 1000 cycles** for this device
class. This repo's `iphone-01` reads **101 at 208 cycles**. Two reference
devices give later anchors (different platforms, different usage —
indicative only, not a fitted curve):

| Cycles | Apple health | Device |
|--------|--------------|--------|
| 208 | 101 | `iphone-01` (measured) |
| 1000 | 80 | Apple design target (not measured on this device) |
| 1420 | 73 | `reference-01` (measured) |
| 2919 | 67 | `reference-02` (measured) |

Implied slope between anchors:

| Interval | Slope |
|----------|-------|
| 208 → 1000 | −2.65 pp / 100 cycles |
| 1000 → 1420 | −1.67 pp / 100 cycles |
| 1420 → 2919 | **−0.40 pp / 100 cycles** |

**The curve is strongly concave: fast early loss, then a long flat tail.**
This is the single most important point for lifetime. A linear fit through
the first 208 cycles dramatically overstates long-term degradation — that is
exactly why the 0.0165 %/day extrapolation was withdrawn.

At ~1.51 cycles/day from 208 cycles on 2026-11-15:

| Node | Expected date | Note |
|------|---------------|------|
| 250 cycles | ~2026-12-12 | 2nd voltage step (4460 mV), health ~98.6% on the NCC ratio |
| 300 cycles | ~2027-01-14 | 3rd step (4440 mV) |
| 500 cycles | ~2027-05-27 | — |
| **1000 cycles** | **~2028-04-22** | ~80% design target; ≥1000 step (extrapolated 4390 mV) |

### B. Usable capacity per full charge

Each −0.02 V step lowers the charge ceiling, so a "100%" charge holds
slightly less energy. Two published/derived slopes disagree by ~3×, so this
is a **range**, not a point estimate:

| Basis | −110 mV total (at ≥1000) ⇒ capacity cost |
|-------|------------------------------------------|
| OCV slope 0.020 V per SOC point (used earlier in this repo) | ≈ −5.5% |
| [Battery University BU-808](https://batteryuniversity.com/article/bu-808-how-to-prolong-lithium-based-batteries): *every 70 mV ≈ 10% capacity* | ≈ −15.7% |

BU-808's guideline is for conventional 4.20 V cobalt-based Li-ion; this
device is a 4.50 V high-voltage / silicon-carbon platform whose upper OCV
slope is steeper. So the true value is plausibly at the **lower** end, but
we cannot resolve it without a measured OCV–SOC curve for this cell.
Honest statement: **by 1000 cycles, each full charge holds roughly 5–16%
less than a hypothetical never-derated cell.**

Crucially, this is **reversible**: BU-808 notes "applying the peak charge
voltage on a subsequent charge will restore the full capacity". It is a
charge-limit choice, not chemical damage.

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
for a substantially slower ageing rate**. That is how Apple reaches the
1000-cycle / 80% design target — the derating is part of the mechanism, not
a penalty on top of it.

---

## 2. So what happens to this battery?

**Short term (next 2 months).** Two more small steps at 250 and 300 cycles,
each ~−0.4 pp on the NCC-derived ratio, with flat plateaus between. Apple's
displayed `MaximumCapacityPercent` may not move at all — it stayed at 101
through the 200-cycle step. Per-charge runtime drops by ~1–3% cumulatively.
Nothing the user will notice.

**Medium term (500–1000 cycles, ~2027–2028).** Ageing slows markedly. The
concave shape from the reference devices suggests the health figure loses
only ~0.4 pp per 100 cycles late in life. Realistically this device reaches
the 1000-cycle / ~80% region around **2028-04**, and 80% is a service
recommendation, not a failure point.

**Long term (>1000 cycles).** Reference devices at 1420 and 2919 cycles
still report 73% and 67%. A battery is usable well beyond 1000 cycles. With
this owner's **~80% charge limit and shallow 20–70% top-ups** (documented in
`findings.md` §3), the effective stress is lower still — the log shows the
device never once reached a full charge in 76 days, which is itself a
strong life-extension factor (BU-808 Table 2: shallower depth of discharge
gives dramatically more cycles).

**Bottom line: the observed behaviour is protective, not deteriorating.**
The step-down costs a few percent of runtime per charge and buys a flatter
ageing curve. At 208 cycles / 99.11% (NCC ratio) / 101 (Apple health), the
battery is in excellent condition and is not the limiting factor for the
device's useful life.

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
| Usable-capacity cost per step | **Low** — 5–16% range at 1000 cycles, no cell-specific OCV curve |
| Ageing curve is concave | Medium — three devices, but different platforms and habits; 1000/80 is a design target, not a measurement |
| Derating slows chemical ageing | **High (direction)** — well-established electrochemistry; magnitude not quantified for this cell |
| Dates for future nodes | Medium — assumes 1.51 cycles/day continues |

Revisit after the 250-cycle node (~2026-12-12): a new analytics snapshot
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
- [`docs/corrections.md`](corrections.md) §4 — withdrawn linear extrapolation.
