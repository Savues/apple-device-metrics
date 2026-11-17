# 方法

[English](methodology.md) · **中文**

> 本文为英文原文的中文翻译；数值、字段名与结论以[英文版](methodology.md)为准。

## 数据来源

### 健康度快照

`devices/iphone-01/health-samples.csv` —— 6 行数据，提取自每个采样日期**本地时间 08:00 生成的 iOS
analytics 快照**。这些是系统生成的每日汇总，既不是手工读数，也不是实时电量计查询。源导出中的列名：

```
Date  Cycl.  Raw Capacity  Nominal Capacity  Nominal Health  iOS  Hrs Soc  Min Soc
```

| 字段 | 单位 | 含义 |
|-------|------|---------|
| `date` | DD-MM-YYYY | 08:00 analytics 快照的日期 |
| `cycle_count` | 循环 | 累计等效满充循环次数 |
| `raw_capacity_mah` | mAh | 电量计原始容量估计；会漂移（3742→3692） |
| `nominal_capacity_mah` | mAh | 用于计算健康度百分比的标称容量 |
| `nominal_health_pct` | % | 上报的最大容量 |
| `ios_version` | — | 快照时的系统版本（全程为 26.4.2） |
| `hrs_soc` | — | 源数据列；始终为 0；**含义未知** |
| `min_soc_pct` | % | 源导出中的 `Min Soc`（18–39%）。解读为该快照周期内的最低 SOC —— **根据列名推断，无文档说明**；肯定**不是**读取时的 SOC |

由于这些是 08:00 的汇总，其日界与充电日志的自然日并不对齐 —— 这也是
`findings.md` 中循环交叉校验结果落在 0.93–1.10 而非恰好 1.00 的原因之一。

准确地说（已由两个连续文件证实）：文件头为
`YYYY-MM-DD 08:00:00 +0800` 的文件，其元数据 `startTimestamp` 为**前一天**的 `00:00:00Z`（= 08:00 +0800），且
`rolloverReason: scheduled`。因此它覆盖本地时间 D−1 08:00 → D 08:00 的 24 h 窗口。健康度表的行按生成日期
D 标注，而充电日志使用自然日。

### 充电日志

`devices/iphone-01/charging-sessions.csv` —— <!--v:sessions-->336<!--/--> 个充电会话，2026-09-01 至
2026-11-15（<!--v:span_days-->78<!--/--> 天）。来源是纯文本日志，每个充电会话三行：

```
开始充电：<date> <time> | 结束充电：<date> <time>
充电时长：<h/m/s> | 充入电量：<n>%
电池电量：<a>% → <b>%  | 每分钟充入：<r>%
```

原始日志**不在仓库里**。其首行包含设备标识符，并带有秒级精度的挂钟时间戳，会暴露睡眠、起床和出行规律。

### 每日 analytics 文件（`.ips.ca.synced`）

`devices/iphone-01/analytics/2026-11-15.json` —— 由
`scripts/extract_analytics.py` 从 2026-11-15 的每日文件（NDJSON，`bug_type 211`，863 条记录）按白名单提取。原始文件**不公开**：其中含有 `deviceId`、UUID、`incident_id`、运营商/国家、SKU 及其他标识符。脚本只输出
`BatteryConfigValueHistogramFinal_V2` 和 `VacVoltageLimit` 中的数值型电池字段，并且一旦出现任何类似标识符的键就拒绝写出。

该文件证实了健康度表每一列的确切来源：

| 导出列 | Analytics 字段 |
|---------------|-----------------|
| `Cycl.` | `CycleCount` |
| `Raw Capacity` | `AppleRawMaxCapacity` |
| `Nominal Capacity` | `NominalChargeCapacity` |
| `Min Soc` | `DailyMinSoc` |
| `Nominal Health` | 推导值 `NCC / 3692` |
| `iOS` | 文件头 `os_version` |
| `Hrs Soc` | 未找到对应字段 |

注意 analytics 中的 `MaximumCapacityPercent` 为 **101**，而不是 99.11 —— 导出工具的 `Nominal Health` 是它自己计算的比值，并非该系统字段。
见 [`ANALYTICS-EVIDENCE.md`](../devices/iphone-01/ANALYTICS-EVIDENCE.zh.md) §6：
本仓库中所有阶跃式衰减的结论描述的都是基于 NCC 推导的比值，而 Apple 自己的健康度字段在跨越 200 循环阶跃时始终保持 101。

### 单次电压读数

`devices/iphone-01/voltage-reading.md` —— 在给定 SOC 下对端电压的一次手工读数。这是带载端电压，不是静置 OCV。

---

## 去标识化规则

由 `scripts/parse_charging_log.py` 执行：

| 保留 | 删除 |
|------|---------|
| `session_id`（顺序编号 1..<!--v:sessions-->336<!--/-->） | 设备标识符 / 日志首行 |
| `day_offset`（距首条记录的天数） | 绝对日历日期 |
| `duration_sec` | 开始/结束时刻 |
| `soc_start`, `soc_end` | 时区、区域设置 |
| `charged_pct` | 任何自由文本 |
| `rate_pct_per_min` | |
| `anomaly` 标记 | |

`day_offset` 是相对整数，因此每日充电会话数和时间序列形态仍可分析，但无法还原任何绝对日期或时刻。健康度快照的日期予以保留（6 个粗粒度数据点，不含行为细节）。`device.json` 包含铭牌电气参数以及机型系列（`iPhone 17`，有意公开）——
不含序列号、UDID、确切型号标识或 analytics 文件名。

## 推导字段

- `duration_sec` 由中文 `<h>小时<m>分钟<s>秒` 字符串解析得到。
- `charged_pct` 取日志中记录的值；带符号（有一个充电会话为 −19%）。
- `anomaly`：以分号连接的标记 —— `soc_dropped` (charged_pct < 0 或 SOC
  下降), `no_charge`, `soc_delta_mismatch` (`soc_end − soc_start ≠
  charged_pct`), `rate_mismatch` (`|charged_pct/(duration/60) − rate| >
  0.06`)。
- `equivalent_full_cycles` = Σ `charged_pct` / 100。

## 校验

`python3 scripts/verify.py` 断言：

1. 健康度百分比等于 `nominal_capacity_mah / 3692 × 100`，误差在 0.01 pp 以内；
2. 充电会话数和汇总总量与 `docs/charging-summary.json` 一致；
3. 所有行均满足 `soc_end − soc_start = charged_pct`（0 处不一致）；
4. 记录的速率与时长/充入量一致，误差在 0.06 %/min 以内；
5. CSV 不含任何绝对日期、时刻或设备标识符字符串；
6. 每个归档的 analytics JSON 均不含标识符、日期正确，且其
   `VacVoltageLimit` 与循环节点区间相符；
7. `analytics-timeline.csv` 是归档数据的精确投影；
8. 每个归档快照都记录了 `gauge_update_time_utc`，电池状态完全相同的连续文件会被标记为重复上报的旧快照（仅作提示，不算失败）。

`gauge_update_time_utc` 来自 `last_value_UpdateTime`（Unix 秒），并规范化为 ISO-8601 UTC。它记录的是**电量计状态实际写入的时间**，可能早于文件的生成日期 —— 例如
11-11 和 11-12 两个文件都带有 `2026-11-10T14:03:43Z`（本地 22:03），说明 11-12 的文件只是重复上报了旧快照；而 11-10
文件带有 `2026-11-09T13:58:20Z`（本地 11-09 21:58），是独立的。

源日志完整性：<!--v:sessions-->336<!--/-->/<!--v:sessions-->336<!--/--> 个充电会话解析成功，0 个解析错误。

## 已知局限

- 57 天内仅六个健康度快照，样本量小；在没有 250 循环节点处观测的情况下，两次断崖无法被完全归因。
- `min_soc_pct` 在各快照间于 18–39% 之间变化，因此采样条件不受控。建议今后在固定 SOC 下采样。
- 电压核对中使用的 OCV 曲线是 4.5 V 级电芯的典型曲线，而非该电芯的实测曲线。该映射仅供参考。
- 循环节点电压表来自第三方，且不同来源之间相互矛盾；见 `voltage-nodes.md`。
- 最终分析中明确**不**使用 SOC 与电压之间的线性假设 —— 曲线在接近满充时很陡。早先对 70% 处 4.132 V 的线性估计是错误的（见 `corrections.md`）。
- **保留期上限**：iOS 只保留约 7–8 天的每日 analytics。归档（<!--v:first_md-->11-09<!--/--> … <!--v:base_md-->11-17<!--/-->）已是可获取的完整窗口；不存在 200 循环之前或约 138 循环时的快照。直接的 4500 mV 读数和阶跃的确切时间戳均无法恢复。改为以生命周期内的 `MaximumPackVoltage = 4496 mV`
  作为此前上限的间接证据。
