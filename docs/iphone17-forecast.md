# iphone-01 (iPhone 17) — battery curve forecast

**Owner instruction**: compute the main device's future curve from its own
data only. The two reference devices are **excluded** from this forecast
(irregular usage; their ageing anchors must not be fitted to this device).
Apple's "80% at 1000 cycles" is likewise not used as an anchor.

Reproduce: `python3 scripts/forecast.py` →
[`iphone17-forecast.csv`](iphone17-forecast.csv),
[`iphone17-forecast.json`](iphone17-forecast.json),
[`iphone17-forecast.svg`](iphone17-forecast.svg).

---

## 1. Every parameter comes from this device

| Parameter | Value | Source on `iphone-01` |
|-----------|-------|------------------------|
| Base date / cycle | 2026-11-15 / 208 | 11-15 analytics |
| Base NCC / health | 3659 mAh / **99.106%** | 11-15 analytics, `NCC/3692` |
| Apple `MaximumCapacityPercent` | **101** | all 7 analytics files |
| Cycle rate (current) | **1.30 /day = 4801 mAh/day** | 76-day charging diary (9883% = 364,880 mAh); independently confirmed by analytics `CycleCount` +8 over 6.23 days = 1.284/day |
| Plateau slope | **0.00476 pp/day = 0.176 mAh/day** | mean of 3 non-step segments in that export |
| Step per 20 mV node | **−0.43 pp = −15.9 mAh** | the 200-node step (3675→3659 mAh) |
| Voltage nodes | 250 / 300 / ≥1000 → 4460 / 4440 / 4390 mV | third-party table (≥1000 extrapolated) |

**Rate correction**: an earlier version used **1.5386 cycles/day** from a
57-day regression on sparse export rows. That is *not* current usage — it
was pulled up by a heavy 30-day stretch. Measured current usage is
~1.28–1.30 cycles/day, cross-checked two ways on this device. The old rate
is kept only as a sensitivity case in §3.1.

Not used: `reference-01` (1420/73%), `reference-02` (2919/67%), the
cross-device concave curve in
[`lifetime-projection.md`](lifetime-projection.md) §1A, and the official
1000/80 specification. That earlier concave curve described *other* devices
and is **not** a prediction for this one.

## 2. Model

```
health(cycle) = 99.106
              − 0.00476 × days                 (plateau / chemical ageing)
              − 0.43  × (# of future nodes)   (reversible lock-in)
chemical_only(cycle) = 99.106 − 0.00476 × days
days = (cycle − 208) / 1.30                 (CURRENT usage)
mAh  = pct / 100 × 3692                     (fixed nameplate)
```

Two curves are drawn:

- **Blue** — `NCC/nameplate`, the figure this repo tracks. Includes the
  node lock-in steps.
- **Green dashed** — chemical ageing only, i.e. the blue curve with the
  reversible lock-in removed. This is the closest thing to "real wear".

The SVG's **right axis is mAh**, so both curves can be read as real capacity.

`MaximumCapacityPercent` (Apple's displayed health) is **not modelled**:
this device has shown a constant 101 across all seven analytics files,
including across the 200-cycle step. There is no observed change from which
to fit a curve. Do not assume it follows the blue line.

## 3. Result — future curve, in real mAh

| Date | Cycles | Voltage | NCC health | **NCC mAh** | Lock-in mAh | Chemical-only mAh |
|------|--------|---------|-----------|-------------|-------------|-------------------|
| 2026-11-15 (now) | 208 | 4480 mV | **99.106%** | **3659** | 0 | 3659 |
| **2026-12-17** | 250 | 4460 mV | **98.522%** | **3637** | 16 | 3653 |
| **2027-01-24** | 300 | 4440 mV | **97.909%** | **3615** | 32 | 3647 |
| **2028-07-16** | 1000 | 4390 mV | **94.916%** | **3504** | 48 | **3552** |

![forecast curve](iphone17-forecast.svg)

At 1000 cycles: **NCC ≈ 3504 mAh**, of which **48 mAh is reversible
lock-in**; genuine chemical wear is only **140 mAh** (3659 → 3552, −3.8%).

**Read it this way**: the blue line falls mainly in **small discrete steps**
at 250 and 300 cycles, then resumes a very shallow plateau. Between nodes
the cell loses just **0.176 mAh/day ≈ 5.3 mAh/month**. Each voltage node
costs ~**16 mAh** of displayed capacity, reversibly.

### 3.1 Sensitivity to daily usage rate

All rates below were measured on this device in different windows; the
health at a given cycle barely changes, but the **dates** move a lot.

| Usage window | cycles/day | mAh/day | 250 node | 1000 node | NCC mAh @1000 |
|--------------|-----------|---------|----------|-----------|---------------|
| recent 7 days | 0.99 | 3655 | 2026-12-27 | 2029-01-23 | 3471 |
| recent 14 days | 1.21 | 4467 | 2026-12-19 | 2028-08-30 | 3496 |
| independent gauge snapshots | 1.284 | 4741 | 2026-12-17 | 2028-07-23 | 3503 |
| **full 76-day diary (primary)** | **1.30** | **4801** | **2026-12-17** | **2028-07-16** | **3504** |
| recent 30 days | 1.53 | 5649 | 2026-12-12 | 2028-04-15 | 3520 |
| old 57-day regression (withdrawn) | 1.5386 | 5681 | 2026-12-12 | 2028-04-12 | 3521 |

So the earlier "1000 cycles ≈ 2028-04" was an artefact of the inflated rate;
at current usage it is **~2028-07**, three months later.

## 4. What this says about lifetime

- The step-down is **protective**. Lowering the upper cut-off voltage slows
  degradation (BU-808 direction, high confidence); the small capacity cost
  is reversible.
- On this device's own numbers there is **no sign of accelerating wear**.
  The plateau slope is measured from its own data and is tiny.
- That is why the earlier cross-device concave curve should not be applied:
  it was shaped by `reference-01/02`, whose usage the owner describes as
  irregular.
- **80% is not a deadline here.** With ~0.0048 pp/day plateau plus three
  remaining node steps, this curve does not reach 80% within the modelled
  window (to 1500 cycles). The official 1000/80 figure is a displayed-value
  commitment that contains lock-in, not a wear measurement (see
  [`corrections.md`](corrections.md) §8).

## 5. Confidence and caveats

| Aspect | Confidence |
|--------|------------|
| Current usage rate (4801 mAh/day) | **High** — 76-day diary + independent gauge deltas agree |
| Plateau slope, current NCC (3659 mAh) | **High** — measured on this device |
| 250 / 300 node dates | Medium — assumes 1.30/day continues; see §3.1 sensitivity |
| −0.43 pp (−15.9 mAh) per node | Medium — one node observed; assumes later nodes same size |
| ≥1000 band (4390 mV) | **Low** — extrapolated from the iPhone 13 series |
| Long-term plateau staying linear | **Low** — real cells can accelerate with heat/high SOC; not modelled |
| Apple displayed health | **Not modelled** — no observed variation |

The model deliberately contains **no ageing acceleration term**. That makes
it optimistic beyond ~500 cycles. Treat everything past 1000 cycles as an
extrapolation, not a prediction.

Revisit at the 250-cycle node (~2026-12-17 at current usage): one new
analytics file will confirm `VacVoltageLimit = 4460 mV`, show whether the
step is again −0.43 pp / −15.9 mAh, and whether Apple's displayed 101
finally moves.
