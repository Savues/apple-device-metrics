# 参考设备 2 — 铭牌 + 电量计快照

[English](README.md) · **中文**

> 本文为英文原文的中文翻译；数值、字段名与结论以[英文版](README.md)为准。

第三台设备提供了厂商铭牌和两个 analytics 文件。其中一个（`Analytics-Daily-*`）
没有电量计记录；另一个（`Analytics-Never-*`）包含一份完整的
`BatteryConfigValueHistogram_Final` 快照。本设备单独保存，**不**并入
`iphone-01` 或任何统计数据。

> ⚠️ 电量计记录中出现了 `OriginalBattery = 0`。公开资料只记载了该字段的
> `null` / `1` 取值，因此 **`0` 没有已证实的含义**；本仓库早先的一条说明将其解读为
> "更换过的电池"，那是一个没有依据的推断。本设备使用的是**原装、从未更换过的电池**，
> 与 `BatterySerialChanged = False` 一致。参见
> [`docs/corrections.md`](../../docs/corrections.zh.md)。

## 厂商铭牌

| 字段 | 数值 |
|-------|-------|
| 电芯能量 | 12.02 Wh |
| 电池能量 | 11.91 Wh |
| 标称电压 | 3.83 V |
| 额定容量 | 3110 mAh |
| 充电电压上限 | 4.45 V |
| iOS（取自 analytics 文件头） | 15.1 |

能量核对：`3.83 V × 3110 mAh = 11.911 Wh` ≈ 11.91 Wh ✓。
电芯能量 / 容量 = `12.02/3.110 = 3.865 V`，即比标称电压高 **+0.035 V**。

## 两个 analytics 文件

| 文件 | 记录数 | 电量计数据 |
|------|---------|------------|
| `Analytics-Daily-*`（27.6 KB） | 70 | **无** — JetsamV3、WlpFixAps、HomeKit、Health、CableTypeChangedV2 |
| `Analytics-Never-*`（93.7 KB） | 355 | **一条** `BatteryConfigValueHistogram_Final` 记录 |

电量计快照来自第二个文件。注意记录名为 `BatteryConfigValueHistogram_Final`
（没有 `_V2`），即较旧的 iOS 15.1 结构。`scripts/extract_analytics.py` 期望的是
`BatteryConfigValueHistogramFinal_V2` 以及 `VacVoltageLimit`，因此会**拒绝这两个文件**；
这在意料之中，因为两者都没有 `VacVoltageLimit`。以下数值为手工提取并列入白名单。

### 电量计快照（2026-11-15，iOS 15.1）

| 字段 | 数值 |
|-------|-------|
| `CycleCount` | **2919** |
| `MaximumCapacityPercent` | **67** |
| `NominalChargeCapacity` | 2212 mAh |
| `AppleRawMaxCapacity` | 2272 mAh |
| `MaximumPackVoltage` | **4449 mV** |
| `MinimumPackVoltage` | 2541 mV |
| `QmaxCell0` | 2488 mAh |
| `MaximumFCC` / `MinimumFCC` | 3265 / 617 mAh |
| `NCCMax` / `NCCMin` | 3211 / 2037 mAh |
| `WeightedRa` | 338 |
| `CycleCountLastQmax` | 87 |
| `TotalOperatingTime` | 61934 h |
| `OriginalBattery` | **0**（含义未证实） |
| `BatterySerialChanged` | False（与原装电池一致） |
| `BatterySerialChanged` | False |
| 电量计 `UpdateTime` | 2026-11-13 18:10:56 UTC |

这套 iOS 15.1 聚合数据中**不存在 `VacVoltageLimit`**。唯一的电压证据是
`MaximumPackVoltage = 4449 mV`，它是生命周期峰值，而不是配置的目标值。

## 本设备的贡献

### 1. 极高循环次数下的 4.45 V 平台

`MaximumPackVoltage = 4449 mV` ≈ 4450 mV，与 4.45 V 铭牌的顶档吻合，
正如 `reference-01`（4450 mV）和 `iphone-01`（4496 mV ≈ 4500 mV）一样。
三台设备、三个铭牌、三个吻合的电池包峰值电压。

在 2919 次循环时，本设备已深入 ≥1000 区间，因此阶跃表预测当前目标值接近 4340 mV，
但在没有 `VacVoltageLimit` 记录的情况下**这一点无法验证**。较旧的 iOS 版本可能使用完全不同的聚合数据集。

### 2. 健康度差值中一个无法解释的符号反转

| 设备 | 循环次数 | `NCC / nameplate` | Apple `MaximumCapacityPercent` | 差值 |
|--------|--------|-------------------|--------------------------------|-----|
| `iphone-01` | 208 | 99.11% | 101 | +1.89 pp |
| `reference-01` | 1420 | 57.66% | 73 | +15.34 pp |
| **`reference-02`** | **2919** | **71.13%** | **67** | **−4.13 pp** |

在本设备上差值**符号反转**。本仓库早先版本将其归因于更换过的电池；
**该解释已撤回**：电池是原装、从未更换过的。该符号反转目前**无法解释**。

能够计算的是 Apple 数字所隐含的基准（`NCC / (MaximumCapacityPercent/100)`）：

| 设备 | 铭牌 | 隐含基准 | 基准 / 铭牌 |
|--------|-----------|------------------|----------------------|
| `iphone-01` | 3692 mAh | 3623 mAh | 0.981 |
| `reference-01` | 2815 mAh | 2223 mAh | 0.790 |
| **`reference-02`** | **3110 mAh** | **3301 mAh** | **1.062** |

在前两台设备上，Apple 的基准**低于**铭牌；而在这里它**高出**铭牌 6%。这就是符号翻转的原因。
注意隐含的 3301 mAh 接近 `MaximumFCC = 3265 mAh` 和 `NCCMax = 3211 mAh`，
但仅凭聚合值无法确定确切的公式，此处也不做猜测。

这仍然是**支持 §6**，而非与之矛盾：Apple 的健康度数字可证明不是 `NCC / nameplate`，
而且其内部基准在不同设备间甚至不总是位于铭牌的同一侧。它推翻的是"差值只是随老化增大"这一简洁说法：
有了三台设备，差值显然取决于设备。

另一处：`NCC / AppleRawMaxCapacity = 2212/2272 = 97.36%`，而 Apple 给出的是 67，
这再次表明 Raw 是一个会漂移的电量计估计值，而不是健康度分母。

### 3. 电芯与电池包 +0.04 V 偏移的第三次证实

| 设备 | 标称电压 V | 电芯能量 / mAh | 偏移 |
|--------|-----------|-------------------|--------|
| `iphone-01` | 3.887 | 3.9271 V | +0.0401 V |
| `reference-01` | 3.83 | 3.8721 V | +0.0421 V |
| **`reference-02`** | **3.83** | **3.8650 V** | **+0.0350 V** |

三个相互独立的铭牌都显示，电芯能量数值意味着一个比电池包标称电压高 ≈0.04 V 的参考电压。
这是一种一致的规格标注惯例，而不是数据错误。

### 4. 相同电压平台，不同容量

`reference-01` 和 `reference-02` 同为 **3.83 V / 4.45 V**，但容量不同（2815 对 3110 mAh）：

| 比值 | 数值 |
|-------|-------|
| 容量 | 3110/2815 = **1.1048×** |
| 电池能量 | 11.91/10.78 = **1.1048×** |
| 绝对差 | 295 mAh ↔ 1.13 Wh（= 3.83 V 下的 295 mAh） |

两个比值在小数点后 4 位上一致，证实它们是同一种电芯化学体系的不同尺寸，
且铭牌能量数值在该平台内部是一致的。

### 5. 预测（而非实测）的电压阶梯

对于 4.45 V 铭牌，同一张 −0.02 V / −0.05 V 阶跃表预测：
在 1–199 / 200–249 / 250–299 / 300–999 / ≥1000 各区间分别为
4450 / 4430 / 4410 / 4390 / 4340 mV。`reference-01` 在这一完全相同的平台上于 1420 次循环时实测为 4340 mV，
因此该预测依据充分，但**尚未在本设备上实测**：两个提供的文件都不包含
`VacVoltageLimit` 记录，即便是较大的 `Analytics-Never-*` 文件也没有。

## 状态

铭牌 + 一份电量计快照，仅供参考。没有任何结论是根据本设备计算得出的。
[`reference.json`](reference.json) 保存白名单内的数值；原始 `.ips` 文件不予公开。
