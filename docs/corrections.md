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

## 7. "OriginalBattery = 0 means a replacement battery" (withdrawn)

The `reference-02` gauge record has `OriginalBattery = 0`. It was read as
"battery has been replaced" and used to explain why the
`NCC / nameplate` vs `MaximumCapacityPercent` gap reversed sign (−4.13 pp).

That inference was **unfounded**: public sources only document `null` / `1`
for this field, and the device owner confirms the battery is **original and
never replaced** (`BatterySerialChanged = False` is consistent with that).
The field's `0` value is now recorded with **unconfirmed semantics**.

Consequences:

- The "replacement battery" explanation for the sign reversal is withdrawn;
  the reversal is now labelled **unexplained**.
- The claim in §6 that the health gap "grows with age" is withdrawn too.
  With three devices the gap is +1.89 / +15.34 / −4.13 pp — clearly
  device-dependent, not monotonic in age.
- Apple's implied baseline on `reference-02` is 3301 mAh, **6% above** its
  3110 mAh nameplate, while it sits below the nameplate on the other two
  devices. The core §6 conclusion (Apple's health figure is not
  `NCC / nameplate`) is unaffected and in fact strengthened.

## 8. Using Apple's "80% at 1000 cycles" as an ageing anchor (withdrawn)

An earlier `lifetime-projection.md` interpolated the measured 101% at 208
cycles against Apple's **80% at 1000 cycles** specification to derive a
chemical-ageing slope (−2.65 pp/100 cycles), and treated 80% as the point
where the cell is worn out.

That was wrong. A supplied A/B measurement
([`voltage-capacity-experiment.json`](voltage-capacity-experiment.json))
shows the **same original battery at cycle 0** with only the voltage limit
changed from 4500 to 4390 mV: reported capacity falls 4799 → 4428 mAh
(−8.0 pp) while **Qmax stays at 4939 mAh**. So a large part of the
displayed capacity/health figure is a **reversible charge-limit effect**,
not chemical wear.

Consequences:

- 1000/80 is a commitment about the **displayed value**, not a measurement
  of cell wear. Of its ~20 pp drop, ≈8 pp (40%) is estimated to be
  reversible lock-in and only ≈12 pp genuine ageing.
- The 1000-cycle point is removed as an interpolation anchor; slopes are
  now computed only between measured devices (208, 1420, 2919).
- The concave displayed curve is retained but explicitly labelled as
  including lock-in, not a pure ageing law.
- The 5–16% generic range for the capacity cost of derating is replaced by
  the measured **1.46 pp per 20 mV node** (8.0 pp for −110 mV) from the A/B
  pair, with a transfer caveat (different cell capacity).

---

All final numbers in `README.md`, `docs/findings.md` and
`docs/charging-summary.json` reflect these corrections and are reproducible
with `python3 scripts/verify.py`.
