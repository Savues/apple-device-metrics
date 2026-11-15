# Corrections

Record of errors found and corrected while building this dataset. Kept so
that anyone reusing the numbers knows which earlier statements are void.

## 1. Charging-session counts (superseded)

An earlier summary quoted **374 sessions / ~166 h / ~130 equivalent cycles /
1.74 %/min**. Those were eyeballed estimates, not parsed. Exact parsing gives:

| | Early estimate | Exact (old log, to 10-29) | Exact (final log, to 11-15) |
|---|---|---|---|
| Sessions | 374 | 260 | **325** |
| Total time | ~166 h | 78.29 h | **99.40 h** |
| Equivalent cycles | ~130 | 78.16 | **98.83** |
| Mean rate | 1.74 %/min | 1.665 %/min | **1.652 %/min** |
| No-gain sessions | ~24 | 15 | **18** |

The final log (received 2026-11-15) is a strict superset of the earlier one:
the first 260 sessions match field-for-field, plus 65 new sessions covering
10-29 → 11-15. Only the final numbers are used in `findings.md`.

## 2. Column names and semantics

The health export was initially described as "design capacity / actual
capacity", and later as "design/actual with both being recalculated". Both
were wrong. Actual source columns:

- `Raw Capacity` — drifting raw gauge estimate, **not** the denominator
- `Nominal Capacity` — the numerator
- `Nominal Health` = Nominal / **fixed 3692 mAh nameplate** (error ≤0.004 pp)
- `Min Soc` — minimum SOC in the snapshot period, **not** the SOC at read
  time (earlier advice to "sample at a fixed SOC" was based on this misreading)
- `Hrs Soc` — always 0, meaning unknown

Because the denominator is fixed, the −0.43 pp step on 2026-11-15 is a real
−16 mAh change, not a moving-baseline artefact. See `methodology.md`.

## 3. "Random gauge recalibration" → cycle-node policy

The stepwise shape was first attributed to random coulomb-counter
recalibration. After cross-checking the cycle numbers, the largest step
(194 → 208) **straddles cycle 200**, matching a reported iOS charge-voltage
step-down at 200/250/300/1000 cycles. The current interpretation is a
deterministic, cycle-triggered policy. **Confirmed on 2026-11-15** by the
analytics field `VacVoltageLimit = 4480 mV` at cycle 208.

## 4. Lifetime extrapolation

A linear fit of 0.0165 %/day was used to predict 90% at ~552 days and 80% at
~1159 days. That treats the two one-off policy steps as continuous loss. A
step model (0.0041 %/day plateau + two −0.43 pp nodes) gives ~96.1% at cycle
1000 before the ≥1000 step, vs 90.5% from the linear fit. The linear
extrapolation is **withdrawn** for mid-term prediction.

## 5. Linear OCV estimate

An early check assumed `3.887 V ≈ 50% SOC` and linearly extrapolated to
`4.132 V at 70%`, then invoked a 0.09 V load sag to explain the observed
4.04 V. The SOC–voltage curve is strongly non-linear near full charge; this
linear model is invalid. A typical 4.5 V-platform OCV curve maps 4.04 V to
≈68.8%, i.e. the reading is consistent with 70% SOC with only ~0.01 V
offset. No voltage abnormality was present.

## 6. "Design capacity was also recalculated"

An earlier reading claimed both the reported capacity columns were being
recomputed at the 2026-11-15 sample. In fact only `Raw Capacity` drifts
(throughout the whole series), while `Nominal Capacity` decreases and the
denominator stays fixed. The health percentage is a plain division.

---

All final numbers in `README.md`, `docs/findings.md` and
`docs/charging-summary.json` reflect these corrections and are reproducible
with `python3 scripts/verify.py`.
