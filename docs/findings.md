# Findings — iphone-01

All computations are reproducible with `python3 scripts/verify.py`.
Datasets: [`health-samples.csv`](../devices/iphone-01/health-samples.csv),
[`charging-sessions.csv`](../devices/iphone-01/charging-sessions.csv).

---

## 1. What the health percentage actually is

`device.json` gives the nameplate rated capacity **3692 mAh**. For every one of
the 6 snapshots:

```
nominal_health_pct = nominal_capacity_mah / 3692 × 100
```

| Date | Cycles | Raw (mAh) | Nominal (mAh) | Nominal/3692 | Reported | Δ (pp) |
|------|--------|-----------|---------------|--------------|----------|--------|
| 2026-09-19 | 122 | 3742 | 3694 | 100.054% | 100.05% | −0.004 |
| 2026-09-23 | 126 | 3750 | 3693 | 100.027% | 100.03% | +0.003 |
| 2026-10-13 | 152 | 3727 | 3678 | 99.621% | 99.62% | −0.001 |
| 2026-10-26 | 176 | 3744 | 3677 | 99.594% | 99.59% | −0.004 |
| 2026-11-05 | 194 | 3698 | 3675 | 99.540% | 99.54% | +0.000 |
| 2026-11-15 | 208 | 3692 | 3659 | 99.106% | 99.11% | +0.004 |

Max error **0.004 pp** — this is an exact definition, not a correlation.

Consequences:

- The denominator is **fixed**. `raw_capacity_mah` drifts 3742→3692 over 57
  days and happens to converge on 3692 at the last sample; it is a separate
  gauge estimate and does **not** enter the health figure.
- Therefore the 2026-11-15 drop of −0.43 pp is a real **−16 mAh** reduction in
  reported nominal capacity (3675→3659), not an artefact of a moving
  denominator or rounding noise.
- The >100% readings early on are normal pre-calibration overshoot.

Nameplate energy: 3.887 V × 3.692 Ah = **14.351 Wh**; current nominal
14.223 Wh.

---

## 2. Degradation shape: steps, not a slope

| Interval | Days | +Cycles | Δ health | %/day | %/cycle |
|----------|------|---------|----------|-------|---------|
| 09-19 → 09-23 | 4 | 4 | 0.02 | 0.0050 | 0.0050 |
| **09-23 → 10-13** | 20 | 26 | **0.41** | 0.0205 | 0.0158 |
| 10-13 → 10-26 | 13 | 24 | 0.03 | 0.0023 | 0.0013 |
| 10-26 → 11-05 | 10 | 18 | 0.05 | 0.0050 | 0.0028 |
| **11-05 → 11-15** | 10 | 14 | **0.43** | 0.0430 | 0.0307 |

Two ~0.4 pp cliffs separated by near-flat plateaus. Continuous chemical
ageing does not behave this way. Plateau mean: **0.0041 %/day**.

Full span: 57 days, +86 cycles (1.51 cycles/day), 100.05% → 99.11%
(−0.94 pp, 0.0165 %/day, 0.0109 %/cycle).

### The 200-cycle node

The largest step (194 → 208 cycles) **straddles cycle 200**. A widely
circulated third-party account says iOS lowers its software charge-voltage
target at 200 / 250 / 300 / 1000 cycles by 0.02 V each (0.05 V at ≥1000),
which reduces the chargeable capacity and is reflected in the reported
health figure. Details and provenance: [`voltage-nodes.md`](voltage-nodes.md).

Order-of-magnitude check with a typical 4.5V-platform OCV curve: high-end
slope ≈ 0.020 V per SOC point, so 0.02 V ⇒ ~1 pp of full-charge capacity.
Observed 0.43 pp. Same order of magnitude; the reported value is smoothed /
re-baselined, so this is consistency, **not proof**.

The earlier cliff (126 → 152 cycles) does **not** contain any of 200/250/300.
Possible explanations: an earlier node in some accounts (150), an iOS
26.4.2 first-calibration event, or analytics sampling at different SOC
(18% vs 20%). Six points cannot separate these.

### Two competing models

| | Method | Health at cycle 1000 (before the ≥1000 step) |
|---|---|---|
| Naive linear | 0.0165 %/day over 525 days | **90.5%** |
| Step model | plateau 0.0041 %/day + two −0.43 pp nodes at 250/300 | **~96.1%** |

The linear fit counts the two one-off policy steps as ongoing loss and
substantially overstates mid-term degradation. The real cliff is at ≥1000
cycles.

### Predicted upcoming nodes

At 1.51 cycles/day from 208 cycles on 2026-11-15:

| Node | Expected date | Expected effect |
|------|---------------|-----------------|
| 250 | ~2026-12-12 | another ~−0.4 pp step |
| 300 | ~2027-01-14 | another ~−0.4 pp step |
| 1000 | ~2028-04-22 | large step, battery replacement territory |

---

## 3. Charging behaviour (325 sessions, 76 days)

From [`charging-summary.json`](charging-summary.json):

| Metric | Value |
|--------|-------|
| Sessions | 325 (306 clean, 19 anomalous) |
| Total time | 99.40 h |
| Total charged | 9883 % = **98.83 equivalent full cycles** |
| Mean duration | 18.35 min |
| Mean charge per session | 30.41 % |
| Mean rate | 1.652 %/min (1.757 excluding anomalies) |
| Sessions/day | 4.28 (min 2, max 15) |
| No net gain | 18 sessions (5.5%) |
| SOC dropped while plugged in | 1 session |
| Longest | 2.25 h for +30% (low-power / pass-through charging) |
| Fastest | 3.75 %/min (short 17→19% burst) |

Speed distribution: >2.0 27.1% · 1.5–2.0 44.0% · 1.0–1.5 17.2% ·
0–1.0 5.8% · ≤0 5.8%.

By starting SOC:

| Start SOC | Sessions | Mean charged | Mean rate |
|-----------|----------|--------------|-----------|
| 0–20% | 58 | 45.3% | 1.98 %/min |
| 20–40% | 166 | 33.3% | 1.77 %/min |
| 40–60% | 92 | 18.3% | 1.35 %/min |
| 60–80% | 9 | 3.7% | 0.45 %/min |

Charging is dominated by shallow 20–60% top-ups; sessions ending above 80%
are rare. Charge rate falls monotonically with starting SOC, consistent with
CC/CV taper.

**Integrity checks on the source log**: 0 parse errors, 0 SOC-delta
mismatches, 0 rate mismatches >0.06 %/min. The declared durations, SOC deltas
and per-minute rates are mutually consistent throughout.

### Cross-check: log cycles vs system cycle counter

| Window | Log equivalent full cycles | System Δ cycles | Ratio |
|--------|---------------------------|-----------------|-------|
| 09-19 → 10-13 | 28.51 | 26 | 1.10 |
| 10-13 → 10-26 | 22.69 | 24 | 0.95 |
| 09-19 → 10-26 | 50.34 | 54 | 0.93 |

Ratio ~0.93–1.10, i.e. the two independent datasets agree within ~10%.
Not exact because the analytics snapshot is generated at 08:00 (so a day's
boundary does not align with the log's calendar day) and because a "cycle"
is counted by cumulative discharge, not simply by charge percentage.

---

## 4. Voltage reading

A single reading of **4.04 V at 70% SOC** was taken. On a typical 4.5 V
high-voltage OCV curve this maps to ≈68.8% — agreement within 0.01 V of the
expected ~4.05 V, the small negative offset being normal load sag. No voltage
collapse or abnormal internal resistance is indicated.

Caveat: this is a **loaded terminal voltage**, not resting OCV, and a single
mid-SOC point cannot distinguish a 4.50 V from a 4.48 V full-charge target.
See [`voltage-reading.md`](../devices/iphone-01/voltage-reading.md).

---

## 5. Open questions

1. **Decisive test**: charge to 100%, rest 10–20 min, read terminal voltage.
   4.48 V ⇒ the 200-cycle step-down is active (confirming the mechanism);
   4.50 V ⇒ it is not active on this device and the November step needs a
   different explanation.
2. Is the reported `charge_limit_voltage_v = 4.5` a static nameplate value or
   the currently effective target? If it changes to 4.46 V after cycle 250,
   it is itself direct evidence and the 100% test becomes unnecessary.
3. Sample at a fixed SOC (e.g. ~20%) to separate node steps from sampling
   noise. `min_soc_pct` in the analytics varies 18–39% across snapshots.
4. Meaning of the `hrs_soc` column (always 0) is unknown.

---

## 6. Bottom line

At 208 cycles / 99.11%, the cell is in excellent condition and is not the
bottleneck. The November drop is best explained by a cycle-node policy
adjustment rather than sudden chemical failure. Mid-term linear lifetime
extrapolation is invalid here; the next verifiable event is the 250-cycle
node around 2026-12-12.
