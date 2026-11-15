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
series 1–199 row. At 208 cycles it should be in the **4.48 V** row if the
table applies.

- The nameplate value (4.50 V) is the cell's **hardware ceiling**; the iOS
  software target is set at or below it. A nameplate reading of 4.50 V
  therefore does **not** contradict an active 4.48 V software target.
- The largest observed health step (194 → 208 cycles, −0.43 pp) straddles
  cycle 200.
- Order of magnitude: with a high-end OCV slope of ~0.020 V per SOC point,
  a 0.02 V reduction corresponds to ~1 pp of full-charge capacity. Observed
  0.43 pp — compatible once smoothing / re-baselining is allowed, but not a
  proof.

## How to verify

1. Charge to 100%, disconnect, rest 10–20 min, read terminal voltage.
   - **4.48 V** → the 200-cycle step is active → mechanism confirmed.
   - **4.50 V** → not active on this device → the November step needs
     another explanation (gauge recalibration / different node table).
2. Check whether `charge_limit_voltage_v` from the analytics is a static
   nameplate field or the live target. If it reads 4.46 V after cycle 250,
   the mechanism is directly observable without test 1.
3. Watch for another ~−0.4 pp step at 250 cycles (~2026-12-12) and 300
   (~2027-01-14), with flat plateaus between.

## References

- [Sina mirror of the blogger post — voltage tables and node list](https://www.sina.cn/news/detail/5333950868489740.html)
- [Sina — cycle-node analysis](https://www.sina.cn/news/detail/5337637240179019.html)
- [Apple Support — iPhone battery and performance](https://support.apple.com/zh-cn/101575) (official; performance management only)
- [Apple Support — charge and maintain your iPhone battery](https://support.apple.com/zh-cn/108371) (official; optimised charging, charge limit)
