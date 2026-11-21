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
  **Confirmed directly by consecutive analytics snapshots**: 11-14 → 11-15
  shows `AppleRawMaxCapacity` 3683 → 3692 (+9 mAh) while
  `NominalChargeCapacity` stays 3659 and health stays 99.106% — see
  [`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md).
  The convergence on the 3692 nameplate was coincidental. The 11-16 file
  reinforces it: `AppleRawMaxCapacity` 3692 → 3708 (+16 mAh) while NCC moves
  only 3659 → 3660 (+1 mAh, a rebound) — the two gauges are independent.
- Therefore the −0.43 pp drop is a real **−16 mAh** reduction in reported
  nominal capacity (3675→3659), not an artefact of a moving denominator or
  rounding noise. <!--v:snap_word_cap-->Twelve<!--/--> consecutive analytics snapshots (<!--v:first_md-->11-09<!--/-->…<!--v:base_md-->11-20<!--/-->,
  cycles <!--v:cycle_list-->200/202/203/203/205/207/208/209/212/212/213/215<!--/-->) all report NCC <!--v:ncc_range-->3658–3660<!--/-->, so the drop
  is bracketed to **cycles 194 → 200** — 6 cycles over 4 days (1.50
  cycles/day). **The 11-09 file shows `VacVoltageLimit = 4480 mV` at exactly
  cycle 200**, i.e. the step fires at the node itself. That file is
  independent (`UpdateTime` = **2026-11-08 17:08 local**), bounding the step
  to before that evening. The 11-11/11-12 files share the later `UpdateTime`
  (11-10 22:03) with identical payloads, so 11-12 is a stale re-report of
  the same gauge state, not an independent observation.
- **Noise scale**: over the <!--v:snap_word-->twelve<!--/--> archived files NCC is <!--v:ncc_range-->3658–3660<!--/--> mAh,
  i.e. 1 mAh = 0.027 pp of jitter (with rebounds 3658→3659→3660), while
  `AppleRawMaxCapacity` swings <!--v:raw_list-->3707 → 3708 → 3678 → 3678 → 3690 → 3683 → 3692 → 3708 → 3681 → 3681 → 3692 → 3667<!--/--> (<!--v:raw_range-->41<!--/--> mAh = <!--v:raw_range_pp-->1.111<!--/--> pp, **<!--v:raw_ratio-->41<!--/-->× noisier**). The −0.43 pp cliff is ~16× the daily
  NCC noise — a genuine step, not sampling jitter. NCC is *not* strictly
  monotonic day-to-day, even though the sparse <!--v:export_n-->6<!--/-->-row export is.
- The >100% readings early on are normal pre-calibration overshoot.

Nameplate energy: 3.887 V × 3.692 Ah = **14.351 Wh**; current nominal
14.223 Wh.

---

## 2. Degradation shape: steps, not a slope

> Every percentage in this section is the **export tool's
> NCC-derived ratio**. Apple's `MaximumCapacityPercent` remained 101 on all
> <!--v:snap_word-->twelve<!--/--> analytics files and shows no step. See
> [`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md) §6.

| Interval | Days | +Cycles | Δ health | %/day | %/cycle |
|----------|------|---------|----------|-------|---------|
| 09-19 → 09-23 | 4 | 4 | 0.02 | 0.0050 | 0.0050 |
| **09-23 → 10-13** | 20 | 26 | **0.41** | 0.0205 | 0.0158 |
| 10-13 → 10-26 | 13 | 24 | 0.03 | 0.0023 | 0.0013 |
| 10-26 → 11-05 | 10 | 18 | 0.05 | 0.0050 | 0.0028 |
| **11-05 → 11-15** | 10 | 14 | **0.43** | 0.0430 | 0.0307 |

Two ~0.4 pp cliffs separated by near-flat plateaus. Continuous chemical
ageing does not behave this way. Plateau mean: **0.0041 %/day**.

Full span: 57 days, +86 cycles (1.51 cycles/day over that historical
window), 100.05% → 99.11% (−0.94 pp, 0.0165 %/day, 0.0109 %/cycle).
Note this is a historical average, **not** the current usage rate used for
forecasts (<!--v:rate-->1.30<!--/--> cycles/day — see
[`iphone17-forecast.md`](iphone17-forecast.md)).

### The 200-cycle node — CONFIRMED

A widely circulated third-party account says iOS lowers its software
charge-voltage target at 200 / 250 / 300 / 1000 cycles by 0.02 V each
(0.05 V at ≥1000), which reduces the chargeable capacity and is reflected in
the reported health figure.

**Confirmed on this device**: `iphone-01` is an **iPhone 17** (model family
confirmed, exact variant unknown), so the iPhone 17 series table is the applicable
one rather than a coincidental voltage match. The 2026-11-09 analytics
file reports `last_value_VacVoltageLimit = 4480 mV` at
**`CycleCount = 200`** — the step is already active at the node itself, not
after it. The 4.50 V nameplate is the hardware ceiling, so the software
target is exactly 0.02 V below it, matching the 200–249 row. <!--v:further_word_cap-->Eleven<!--/--> further
snapshots (<!--v:further_range-->202–215<!--/--> cycles) all show 4480 mV. The earliest independent gauge
write is 2026-11-08 17:08 local; the latest is <!--v:gauge_last_local-->2026-11-19 11:29<!--/--> local.
See [`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md)
and [`voltage-nodes.md`](voltage-nodes.md).

The health cliff is now bracketed to cycles 194 → 200 (6 cycles / 4 days),
coincident with the voltage step. Order-of-magnitude check with a typical
4.5V-platform OCV curve: high-end slope ≈ 0.020 V per SOC point, so 0.02 V
⇒ ~1 pp of full-charge capacity; observed 0.43 pp. Same order of magnitude,
with the reported value smoothed / re-baselined.

**Data boundary**: iOS retains only ~7–8 days of analytics, so no pre-200
snapshot exists and a direct 4500 mV reading is unobtainable. Indirect
evidence fills the gap: the lifetime `MaximumPackVoltage = 4496 mV` exceeds
the current 4480 mV target by 16 mV, so it must have been recorded under a
higher ceiling (~4.50 V). The diary never exceeds 81% SOC (termination piles
up at 69/79%: sessions end before the 80% Charge Limit), so the peak must come from a full
charge **before 09-01**, at ≈101 cycles or fewer — well inside the 1–199
band. See
[`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md) §1.1.

### The first cliff — Qmax recalibration candidate

The earlier cliff (126 → 152 cycles) does **not** contain any of 200/250/300.
The analytics file reports `CycleCountLastQmax = 138`, i.e. the last Qmax
(gauge chemical-capacity) recalibration happened **inside** that interval.
This is a plausible alternative cause for the −0.41 pp step, meaning the two
cliffs may have different mechanisms.

Unconfirmed: needs an analytics snapshot from before 200 cycles (to see
`VacVoltageLimit = 4500`) and one near cycle 138 (to see the Qmax update).

### Two competing models

| | Method | Health at cycle 1000 (before the ≥1000 step) |
|---|---|---|
| Naive linear | 0.0165 %/day over 525 days | **90.5%** |
| Step model | plateau 0.0041 %/day + two −0.43 pp nodes at 250/300 | **~96.1%** |

Both figures describe the **NCC-derived export ratio**, not Apple's
`MaximumCapacityPercent`. The linear fit counts the two one-off policy steps
as ongoing loss and substantially overstates mid-term degradation.

Both are superseded for lifetime purposes by the empirical concave ageing
curve from three devices in
[`lifetime-projection.md`](lifetime-projection.md): displayed health loss
falls from ~−2.31 pp/100 cycles early to ~−0.40 pp/100 cycles late (both
include reversible voltage lock-in, not just chemistry). Apple's 80% at
1000 cycles is a displayed-value commitment, not a wear measurement — see
[`lifetime-projection.md`](lifetime-projection.md) §0. The ≥1000 voltage
value (4390 mV) is extrapolated.

### Predicted upcoming nodes

At the **current measured usage of <!--v:rate-->1.30<!--/--> cycles/day = <!--v:mah_day-->4803<!--/--> mAh/day** (<!--v:span_days-->80<!--/-->-day
charging diary, cross-checked by <!--v:gauge_n-->10<!--/--> non-stale gauge writes = <!--v:gauge_rate-->1.362<!--/-->/day) from <!--v:base_cycle-->215<!--/-->
cycles on <!--v:base_date-->2026-11-20<!--/-->. Full forecast with mAh and rate sensitivity:
[`iphone17-forecast.md`](iphone17-forecast.md).

| Node | Expected date | Expected effect |
|------|---------------|-----------------|
| 250 | ~<!--v:date_next-->2026-12-16<!--/--> | another ~−0.43 pp / −15.9 mAh step |
| 300 | ~<!--v:date_after-->2027-01-24<!--/--> | another ~−0.43 pp / −15.9 mAh step |
| 1000 | ~<!--v:date_kilo-->2028-07-15<!--/--> | ≥1000 step (extrapolated 4390 mV) |

The earlier 1.51–1.54 cycles/day estimate came from a regression on sparse
export rows and was inflated by a heavy 30-day stretch; see the sensitivity
table in the forecast document.

---

## 3. Charging behaviour (<!--v:sessions-->341<!--/--> sessions, <!--v:span_days-->80<!--/--> days)

From [`charging-summary.json`](charging-summary.json):

| Metric | Value |
|--------|-------|
| Sessions | <!--v:sessions-->341<!--/--> (<!--v:clean_sessions-->322<!--/--> clean, <!--v:anom_sessions-->19<!--/--> anomalous) |
| Total time | <!--v:dur_hours_2-->102.66<!--/--> h |
| Total charged | <!--v:charged_sum-->10408<!--/--> % = **<!--v:efc-->104.08<!--/--> equivalent full cycles** |
| Mean duration | <!--v:avg_dur-->18.42<!--/--> min |
| Mean charge per session | <!--v:avg_charge-->30.52<!--/--> % |
| Mean rate | <!--v:rate_mean_3-->1.652<!--/--> %/min (<!--v:rate_clean_3-->1.757<!--/--> excluding anomalies) |
| Sessions/day | <!--v:sess_day-->4.26<!--/--> (min <!--v:sess_day_min-->1<!--/-->, max <!--v:sess_day_max-->15<!--/-->) |
| No net gain | <!--v:zero_sessions-->18<!--/--> sessions (<!--v:zero_pct-->5.3<!--/-->%) |
| SOC dropped while plugged in | 1 session |
| Longest | <!--v:longest_h-->2.25<!--/--> h for +<!--v:longest_pct-->30<!--/-->% (low-power / pass-through charging) |
| Fastest | <!--v:fastest-->3.75<!--/--> %/min (short <!--v:fastest_lo-->17<!--/-->→<!--v:fastest_hi-->19<!--/-->% burst) |

Speed distribution: >2.0 <!--v:speed_gt2-->27.1<!--/-->% · 1.5–2.0 <!--v:speed_15_2-->43.8<!--/-->% · 1.0–1.5 <!--v:speed_1_15-->17.9<!--/-->% ·
0–1.0 <!--v:speed_0_1-->5.7<!--/-->% · ≤0 <!--v:speed_le0-->5.7<!--/-->%.

By starting SOC:

<!--b:soc_bands_en-->

| Start SOC | Sessions | Mean charged | Mean rate |
|-----------|----------|--------------|-----------|
| 0–20% | 59 | 45.3% | 1.98 %/min |
| 20–40% | 175 | 33.6% | 1.77 %/min |
| 40–60% | 96 | 18.8% | 1.35 %/min |
| 60–80% | 11 | 4.5% | 0.60 %/min |

<!--/b-->

Charging is dominated by shallow 20–60% top-ups; sessions ending above 80%
are rare (<!--v:ge80_n-->4<!--/--> of <!--v:sessions-->341<!--/-->). Charge rate falls monotonically with starting SOC,
consistent with CC/CV taper.

Termination SOC is strongly clustered: **<!--v:top_a-->69<!--/-->% (<!--v:top_a_n-->46<!--/--> sessions)** and **<!--v:top_b-->79<!--/-->%
(<!--v:top_b_n-->27<!--/--> sessions)** are the two most common end points, with <!--v:end_mid_n-->215<!--/-->/<!--v:sessions-->341<!--/--> sessions ending
in 65–81%. This is the signature of **unplugging before the 80% Charge
Limit** (the limit is on as a safety net), and it explains why the device never reached a full
charge during the <!--v:span_days-->80<!--/-->-day window. Consequence: the lifetime
`MaximumPackVoltage = 4496 mV` cannot have been produced inside this window —
it is a fossil from a full charge before 09-01, when the 4.50 V target was
still in effect (see
[`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md) §1.1).

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
Not exact because the analytics snapshot is generated at 08:00 and covers
the **previous** 24 h (file dated D covers D−1 08:00 → D 08:00 local, per
`startTimestamp` / `rolloverReason`), so its day boundary does not align
with the log's calendar day; and because a "cycle" is counted by cumulative
discharge, not simply by charge percentage.

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

1. ~~**Decisive test**: charge to 100%, rest 10–20 min, read terminal voltage.~~
   **Resolved**: analytics report `VacVoltageLimit = 4480 mV` at exactly
   cycle 200 — the step fires at the node. See
   [`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md).
2. ~~**Pre-200 snapshot**~~ **Unobtainable**: iOS keeps only ~7–8 days of
   analytics, so no `CycleCount < 200` file exists. A direct 4500 mV reading
   cannot be recovered. Substituted by the lifetime `MaximumPackVoltage =
   4496 mV` argument (see §3 above and `ANALYTICS-EVIDENCE.md` §1.1).
3. ~~**Qmax hypothesis**~~ Also unobtainable: no snapshot near cycle 138 can
   be recovered. `CycleCountLastQmax = 138` remains a plausible but untestable
   explanation for the first cliff.
4. **Next observable node — cycle 250 (~<!--v:date_next-->2026-12-16<!--/--> at current usage)**: expect
   `VacVoltageLimit = 4460 mV` and another ~−0.43 pp / −15.9 mAh step. This is
   fully within reach of the rolling 7-day window.
5. Meaning of the `hrs_soc` column (always 0) is still unknown — no matching
   field found in the analytics file.
6. `MaximumCapacityPercent = 101` in analytics vs exported `Nominal Health`
   99.11% — different baselines; the former is Apple's displayed health and
   stayed constant across the 200-cycle step. All decay analysis here uses
   the NCC-derived ratio. See
   [`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md) §6.

---

## 6. Bottom line

At <!--v:base_cycle-->215<!--/--> cycles / <!--v:base_health_two-->99.13<!--/-->%, the cell is in excellent condition and is not the
bottleneck. The November drop is best explained by a cycle-node policy
adjustment rather than sudden chemical failure. Mid-term linear lifetime
extrapolation is invalid here; the next verifiable event is the 250-cycle
node around <!--v:date_next-->2026-12-16<!--/--> (at the measured current usage of <!--v:rate-->1.30<!--/--> cycles/day).
