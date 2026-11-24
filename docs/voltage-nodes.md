# Cycle-node charge-voltage step-down (third-party claim)

> **Status: NOT Apple documentation.** This is reverse-engineered /
> repair-community knowledge. Apple's public material only promises "80%
> capacity retained at 1000 cycles" and documents performance management,
> optimised charging and the 80–95% charge-limit setting. No public Apple
> document describes a cycle-indexed voltage table.

## The claim

For iPhone 13 → 17 series, the **software** charge-voltage target is lowered
when the cycle counter reaches certain nodes: **200, 250, 300, 1000**. Each
step is −0.02 V; the ≥1000 step is −0.05 V. Reducing the target means less
charge is admitted at "100%", and the reduced full-charge capacity is
reflected in the reported battery-health percentage. This is the mechanism
commonly called 降压锁容 ("voltage step-down / capacity lock").

It is independent of AppleCare+.

## Reported voltage tables

**iPhone 13 series**

| Cycles | Limit |
|--------|-------|
| 1–199 | 4.47 V |
| 200–249 | 4.45 V |
| 250–299 | 4.43 V |
| 300–999 | 4.41 V |
| ≥1000 | 4.36 V |

**iPhone 17 series**

| Cycles | Limit |
|--------|-------|
| 1–199 | 4.50 V |
| 200–249 | 4.48 V |
| 250–299 | 4.46 V |
| 300–999 | 4.44 V |

Source: a Weibo-verified digital-hardware blogger's post mirrored at
[Sina (2026-08-20)](https://www.sina.cn/news/detail/5333950868489740.html).
The same node set is repeated in Chinese repair-forum and Q&A material
(Baidu Wenku, NGA, Tieba, Zhihu, Bilibili repair channels).

## Independent cross-check on a second device

A second device (`reference-01`, iOS 17.6.1, **1420 cycles**) has a
manufacturer nameplate charge limit of **4.45 V**. Applying the step table
forward: `4.45 − 0.02×3 − 0.05 = 4.34 V`, which **exactly equals** its
measured `VacVoltageLimit = 4340 mV`. Its lifetime
`MaximumPackVoltage = 4450 mV` also matches the 4.45 V top rung. See
[`devices/reference-01/README.md`](../devices/reference-01/README.md).

`iphone-01` validates the first step from its own 4.50 V nameplate: 4.48 V
measured at exactly cycle 200, with a 4496 mV lifetime peak just under
4.50 V. Two nameplates, two iOS versions, two cell platforms, one consistent
ladder — verified in both directions.

The **absolute** voltages differ (4.50 V vs 4.45 V), so the table is
platform-relative and must be applied per device. This materially
strengthens the −0.02 V / −0.05 V step sizes, though the node boundaries
remain third-party reverse-engineering rather than Apple documentation.

A third device ([`reference-02`](../devices/reference-02/README.md), iOS
15.1, 3110 mAh) shares the same 3.83 V / **4.45 V** nameplate platform as
`reference-01`. A second analytics file for it (`Analytics-Never-*`) supplies
a gauge snapshot at **2919 cycles** with `MaximumPackVoltage = 4449 mV` —
matching the 4450 mV top rung — but no `VacVoltageLimit` record, so its
ladder (4450 → … → 4340 mV) remains **predicted, not measured**. iOS 15.1
uses an older aggregate set (`BatteryConfigValueHistogram_Final`) that does
not include the voltage-limit aggregate. Its nameplate energy figures are
internally consistent with `reference-01`: capacity ratio 3110/2815 =
1.1048× equals the battery-energy ratio 11.91/10.78 = 1.1048×.

## Variant accounts (important)

The community is **not** consistent:

- Some report the first step at **250** cycles, not 200.
- Older threads (2016, NGA) say 1000 cycles for iPhone 5s and earlier,
  500 cycles from iPhone 6 onward.
- A Zhihu answer states "4% capacity locked at 300 cycles, 9% at >1000".
- Some repair videos explicitly dispute the claim that a full discharge /
  recharge cycle can undo the lock.

So the node set is model- and possibly iOS-version-dependent, and the exact
numbers should be treated as an empirical hypothesis, not a specification.

## Relation to this dataset

`iphone-01` is an **iPhone 17** (model family confirmed, exact variant unknown), so the
**iPhone 17 series** table above is the applicable one, not merely a table
that happens to share the same 4.50 V limit. Its 1–199 row (4.50 V) matches
the nameplate, and the 200–249 row (4.48 V) is what the 2026-11-09 analytics
file reports at **`CycleCount = 200` exactly** — the step is active at the
node itself, not after it. <!--v:further_word_cap-->Fifteen<!--/--> further snapshots (<!--v:further_range-->202–220<!--/--> cycles) confirm
4480 mV throughout. This is direct device-level confirmation of both the
applicable table and the −0.02 V magnitude.

The 250 / 300 / ≥1000 rows (4.46 / 4.44 / ~4.39 V) remain **predictions for
this model** — the third-party post gives no ≥1000 value for the iPhone 17
series; the 4390 mV figure here is extrapolated from the iPhone 13 series'
−0.05 V final step.

- The nameplate value (4.50 V) is the cell's **hardware ceiling**; the iOS
  software target is set at or below it. A nameplate reading of 4.50 V
  therefore does **not** contradict an active 4.48 V software target.
- The health cliff is bracketed to **cycles 194 → 200** (6 cycles / 4 days),
  coincident with the voltage step. The earliest independent gauge write is
  2026-11-08 17:08 local.
- Order of magnitude: with a high-end OCV slope of ~0.020 V per SOC point,
  a 0.02 V reduction corresponds to ~1 pp of full-charge capacity. Observed
  0.43 pp — compatible once smoothing / re-baselining is allowed, but not a
  proof.

## How to verify

**Confirmed on `iphone-01`.** The daily analytics `VacVoltageLimit` aggregate
gives `last_value_VacVoltageLimit = 4480` (mV) at `CycleCount = 200`, exactly
the −0.02 V step predicted by the 200–249 row. No 100% charge test is needed.
See [`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.md).

Extract the same field from any other daily analytics file:

```sh
python3 scripts/extract_analytics.py /path/to/Analytics-YYYY-MM-DD.ips
```

Remaining checks:

1. ~~**Pre-200 snapshot**~~ **Unobtainable** — iOS retains only ~7–8 days of
   analytics; all <!--v:snap_word-->sixteen<!--/--> files available sit at <!--v:cycle_range-->200–220<!--/--> cycles. A direct
   4500 mV reading cannot be recovered. Indirect evidence: lifetime
   `MaximumPackVoltage = 4496 mV`, 16 mV above the current 4480 mV target,
   which must have been recorded under the earlier ~4.50 V ceiling.
2. **Cycle 250 (~<!--v:date_next-->2026-12-17<!--/--> at current usage)**: expect `VacVoltageLimit =
   4460` — the next node, fully observable with the rolling window.
3. ~~**Qmax hypothesis**~~ Also unobtainable: no snapshot near cycle 138.
4. Watch for another ~−0.43 pp / −15.9 mAh health step at 250 and 300
   (~<!--v:date_after-->2027-01-25<!--/-->), with flat plateaus between. See
   [`iphone17-forecast.md`](iphone17-forecast.md) for the rate basis.

## References

- [Sina mirror of the blogger post — voltage tables and node list](https://www.sina.cn/news/detail/5333950868489740.html)
- [Sina — cycle-node analysis](https://www.sina.cn/news/detail/5337637240179019.html)
- [Apple Support — iPhone battery and performance](https://support.apple.com/zh-cn/101575) (official; performance management only)
- [Apple Support — About Charge Limit and Optimized Battery Charging on iPhone](https://support.apple.com/en-us/108055) (official; states the conditional periodic full charge that maintains SOC accuracy — see [`shallow-charging-accuracy.md`](shallow-charging-accuracy.md))
