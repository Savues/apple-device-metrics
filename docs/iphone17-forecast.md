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
| Cycle rate | **1.5386 /day** | linear regression on the 6-row health export |
| Plateau slope | **0.00476 pp/day** | mean of 3 non-step segments in that export |
| Step per 20 mV node | **−0.43 pp** | the 200-node step (3675→3659 mAh) |
| Voltage nodes | 250 / 300 / ≥1000 → 4460 / 4440 / 4390 mV | third-party table (≥1000 extrapolated) |

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
days = (cycle − 208) / 1.5386
```

Two curves are drawn:

- **Blue** — `NCC/nameplate`, the figure this repo tracks. Includes the
  node lock-in steps.
- **Green dashed** — chemical ageing only, i.e. the blue curve with the
  reversible lock-in removed. This is the closest thing to "real wear".

`MaximumCapacityPercent` (Apple's displayed health) is **not modelled**:
this device has shown a constant 101 across all seven analytics files,
including across the 200-cycle step. There is no observed change from which
to fit a curve. Do not assume it follows the blue line.

## 3. Result — future curve

| Date | Cycles | `VacVoltageLimit` | NCC health | of which lock-in | Chemical only |
|------|--------|-------------------|-----------|------------------|---------------|
| 2026-11-15 (now) | 208 | 4480 mV | **99.106%** | 0 | 99.106% |
| **2026-12-12** | 250 | 4460 mV | **98.546%** | 0.43 pp | 98.976% |
| **2027-01-13** | 300 | 4440 mV | **97.962%** | 0.86 pp | 98.822% |
| 2027-05 | ~400 | 4440 mV | 97.65% | 0.86 pp | 98.51% |
| 2027-11 | ~700 | 4440 mV | 96.68% | 0.86 pp | 97.54% |
| **2028-04-12** | 1000 | 4390 mV | **95.366%** | 1.29 pp | **96.656%** |
| 2029-03 | ~1500 | 4390 mV | 93.05% | 1.29 pp | 94.34% |

![forecast curve](iphone17-forecast.svg)

**Read it this way**: the blue line falls mainly in **small discrete steps**
at 250 and 300 cycles, then resumes a very shallow plateau. Between nodes
the device loses only ~0.0048 pp/day ≈ **0.14 pp/month**. By 1000 cycles
(≈ 17 months away) the NCC-derived figure is ~**95.4%**, of which only
~**3.4 pp** is genuine chemical ageing — and ~**1.3 pp** is reversible
lock-in.

The gap between blue and green is the accumulated lock-in. It never grows
large because this device's observed step is only −0.43 pp per node.

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
| Cycle rate, plateau slope, current NCC | **High** — measured on this device |
| 250 / 300 node dates | Medium — rate assumed constant |
| −0.43 pp per node | Medium — one node observed on this device; assumes later nodes same size |
| ≥1000 band (4390 mV) | **Low** — extrapolated from the iPhone 13 series |
| Long-term plateau staying linear | **Low** — real cells can accelerate with heat/high SOC; not modelled |
| Apple displayed health | **Not modelled** — no observed variation |

The model deliberately contains **no ageing acceleration term**. That makes
it optimistic beyond ~500 cycles. Treat everything past 1000 cycles as an
extrapolation, not a prediction.

Revisit at the 250-cycle node (~2026-12-12): one new analytics file will
confirm `VacVoltageLimit = 4460 mV`, show whether the step is again
−0.43 pp, and whether Apple's displayed 101 finally moves.
