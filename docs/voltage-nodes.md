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

`iphone-01` has a **4.50 V nameplate charge limit**, matching the iPhone 17
series 1–199 row. The 2026-11-09 analytics file reports
`VacVoltageLimit = 4480 mV` at **`CycleCount = 200` exactly** — the step is
active at the node itself, not after it. Six further snapshots (202–208
cycles) confirm 4480 mV throughout. This is direct device-level confirmation
of both the node and the −0.02 V magnitude.

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

1. ~~**Pre-200 snapshot**~~ **Unobtainable** — iOS retains only ~7 days of
   analytics; all seven files available sit at 200–208 cycles. A direct
   4500 mV reading cannot be recovered. Indirect evidence: lifetime
   `MaximumPackVoltage = 4496 mV`, 16 mV above the current 4480 mV target,
   which must have been recorded under the earlier ~4.50 V ceiling.
2. **Cycle 250 (~2026-12-12)**: expect `VacVoltageLimit = 4460` — the next
   node, fully observable with the rolling window.
3. ~~**Qmax hypothesis**~~ Also unobtainable: no snapshot near cycle 138.
4. Watch for another ~−0.4 pp health step at 250 (~2026-12-12) and 300
   (~2027-01-14), with flat plateaus between.

## References

- [Sina mirror of the blogger post — voltage tables and node list](https://www.sina.cn/news/detail/5333950868489740.html)
- [Sina — cycle-node analysis](https://www.sina.cn/news/detail/5337637240179019.html)
- [Apple Support — iPhone battery and performance](https://support.apple.com/zh-cn/101575) (official; performance management only)
- [Apple Support — charge and maintain your iPhone battery](https://support.apple.com/zh-cn/108371) (official; optimised charging, charge limit)
