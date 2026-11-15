# Analytics evidence — 2026-11-15 snapshot

Source: iOS daily analytics file (`bug_type 211`, NDJSON, generated 08:00
local). 863 records. Parsed with
[`scripts/extract_analytics.py`](../scripts/extract_analytics.py) into
[`analytics/2026-11-15.json`](analytics/2026-11-15.json).

The raw `.ips` file is **not** published: it contains `deviceId`, UUIDs,
`incident_id`, carrier/country, SKU and other identifiers. Only a whitelist
of numeric battery fields is emitted.

---

## 1. The 200-cycle voltage step is CONFIRMED

| Field | Value | Meaning |
|-------|-------|---------|
| `last_value_VacVoltageLimit` | **4480 mV = 4.480 V** | currently effective charge-voltage ceiling |
| `last_value_CycleCount` | 208 | in the 200–249 band |
| `last_value_MaximumPackVoltage` | 4496 mV = 4.496 V | historical peak pack voltage |

The nameplate hardware ceiling is 4.50 V. The **live** software target is
**4.48 V**, exactly the −0.02 V step predicted for the 200-cycle node in
[`voltage-nodes.md`](../docs/voltage-nodes.md).

This resolves the open question in `docs/findings.md`: the pending
"charge to 100% and read the voltage" experiment is no longer needed. The
analytics file reports the configured limit directly.

`MaximumPackVoltage` 4496 mV is a *historical* aggregate (paired with
`MinimumPackVoltage` 2765 mV over the device lifetime), so it does not
contradict the current 4480 mV target.

---

## 2. The health-table columns are now identified exactly

| Published column | Actual analytics field | Value |
|------------------|------------------------|-------|
| `Cycl.` | `CycleCount` | 208 |
| `Raw Capacity` | `AppleRawMaxCapacity` | 3692 |
| `Nominal Capacity` | `NominalChargeCapacity` | 3659 |
| `Nominal Health` | derived: `NCC / 3692 × 100` | 99.106% |
| `Min Soc` | **`DailyMinSoc`** | 39 |
| `iOS` | header `os_version` | 26.4.2 |
| `Hrs Soc` | no matching field found | 0 in export |

`Min Soc` = **minimum SOC of that day**, not the SOC at read time — now
confirmed, not inferred. `Hrs Soc` remains unexplained; no field in the file
obviously corresponds to it.

Two corrections to earlier notes:

- `Raw Capacity` is `AppleRawMaxCapacity`, a gauge estimate that happened to
  equal the nameplate 3692 at this snapshot. It is **not** the health
  denominator; the denominator is the fixed nameplate rated capacity.
- `MaximumCapacityPercent` in the analytics is **101**, which does **not**
  equal the exported `Nominal Health` 99.11%. These are different quantities;
  the export tool computes its own ratio. Do not treat the two as the same.

---

## 3. The first cliff (126→152 cycles) has a candidate cause

`CycleCountLastQmax = 138` — the last Qmax (gauge chemical-capacity)
recalibration happened at cycle **138**, which falls *inside* the 126→152
interval where the first −0.41 pp step occurred.

Supporting gauge state at 208 cycles:

| Field | Value |
|-------|-------|
| `QmaxCell0` | 3824 mAh |
| `MaximumQmax` / `MinimumQmax` | 3901 / 3824 mAh |
| `NCCMax` / `NCCMin` | 3780 / 3657 mAh |
| `MaximumFCC` / `MinimumFCC` | 3837 / 3543 mAh |
| `CycleCountLastQmax` | 138 |

So the two cliffs plausibly have **different** causes:

| Interval | Cycles | Δ health | Likely cause |
|----------|--------|----------|--------------|
| 09-23 → 10-13 | 126→152, contains **138** | −0.41 pp | Qmax / gauge recalibration |
| 11-05 → 11-15 | 194→208, contains **200** | −0.43 pp | `VacVoltageLimit` 4500→4480 |

This is a hypothesis, not yet proven: we have one analytics file at 208
cycles. An analytics snapshot from **before 200 cycles** (and ideally one
from around 138) would show whether `VacVoltageLimit` was 4500 mV and
whether the Qmax update coincides with the first drop.

---

## 4. Other useful state

| Field | Value | Note |
|-------|-------|------|
| `AverageTemperature` | 29 | gauge-reported average |
| `BatteryHealthMetric` | 77 | opaque |
| `WeightedRa` / `ChemicalWeightedRa` | 75 / 75 | resistance metric |
| `TotalOperatingTime` | 4928 h | ≈205 days |
| `DailyMaxSoc` / `DailyMinSoc` | 63 / 39 | day's range |
| `SlowChargingReason` | 0 | no slow-charge flag that day |
| `BatteryCellDisconnectCount` | 0 | no disconnect |
| `DOFU` | 2026-03-05 | first-use date (not published in CSV) |

`BatteryTimeAtHighSocLast` bins 0–9: `[21, 12, 7, 0, 0, 18, 10, 7, 1, 0]`
— time spent in high-SOC bands, consistent with the log's shallow charging
pattern.

---

## 5. What to send next

Any `.ips.ca.synced` / `.ips` daily analytics file works, **one per date**.
The parser reads the first header line plus two named records
(`BatteryConfigValueHistogramFinal_V2`, `VacVoltageLimit`), so partial or
aggregated files are fine as long as those records are present. The header
timestamp determines the archive filename — no manual naming needed.

Most valuable for closing the remaining questions:

1. **A snapshot with `CycleCount` < 200** — expect `VacVoltageLimit = 4500`.
   Direct before/after proof of the step.
2. **A snapshot near cycle 138** — to test the Qmax-recalibration hypothesis
   for the first cliff.
3. Any snapshot after cycle 250 — expect `VacVoltageLimit = 4460`.

Import any number at once; the timeline CSV is rebuilt from the full archive:

```sh
python3 scripts/extract_analytics.py --archive \
    /path/Analytics-2026-09-19.ips /path/Analytics-2026-10-13.ips
python3 scripts/verify.py
```

### Current timeline

| Date | Cycles | `VacVoltageLimit` | Expected band | NCC | Health |
|------|--------|-------------------|---------------|-----|--------|
| 2026-11-15 | 208 | 4480 mV (4.48V) | 200–249 ✓ | 3659 | 99.106% |

Full machine-readable version:
[`analytics-timeline.csv`](analytics-timeline.csv). Each import adds a row;
`verify.py` asserts every row's voltage matches its node band.
