<div align="center">

# apple-device-metrics

[English](README.md) · **中文** · [网站](https://savues.github.io/apple-device-metrics/)

[![verify](https://github.com/Savues/apple-device-metrics/actions/workflows/verify.yml/badge.svg)](https://github.com/Savues/apple-device-metrics/actions/workflows/verify.yml)
[![pages](https://github.com/Savues/apple-device-metrics/actions/workflows/pages.yml/badge.svg)](https://savues.github.io/apple-device-metrics/)
[![license: CC0-1.0](https://img.shields.io/badge/license-CC0--1.0-blue.svg)](LICENSE)
![device: iPhone 17](https://img.shields.io/badge/device-iPhone%2017-30a46c.svg)

</div>

这是我自己的几台 iPhone 的电池与充电测量数据，去标识化后公开。数字来自 iOS
analytics 文件和充电日志，不来自宣传材料；把这些文件变成下面这些表格的脚本也
在仓库里。

### 速览（`iphone-01`，最新快照 <!--v:base_date-->2026-11-17<!--/-->）

| 循环 | NCC | NCC ÷ 3692 | 苹果显示值 | 充电电压上限 | 用量 |
|:-:|:-:|:-:|:-:|:-:|:-:|
| **<!--v:base_cycle-->212<!--/-->** | **<!--v:base_ncc-->3660<!--/--> mAh** | **<!--v:base_health_two-->99.13<!--/-->%** | **<!--v:apple-->101<!--/-->%** | **<!--v:vac-->4480<!--/--> mV** | **<!--v:rate-->1.30<!--/--> 次循环/天** |

下一个节点：250 次循环 → 4460 mV，点估计约 <!--v:date_next-->2026-12-16<!--/-->；按我能测到的几种用量口径，落在
<!--v:date_next_lo-->2026-12-11<!--/--> … <!--v:date_next_hi-->2026-12-25<!--/-->（已事前登记在
[`docs/predictions.json`](docs/predictions.json)）。1000 次循环那一行同样是 <!--v:date_kilo-->2028-07-15<!--/-->，区间也一样宽：
<!--v:date_kilo_lo-->2028-04-15<!--/--> … <!--v:date_kilo_hi-->2029-01-20<!--/-->。单个日期只是点估计，不是承诺
（见 [`docs/iphone17-forecast.md`](docs/iphone17-forecast.zh.md)）。

<p align="center"><img src="docs/iphone17-forecast.svg" alt="iphone-01 预测曲线" width="760"></p>

> 这台机器的充电上限（Charge Limit）设在 80% 兜底，但我几乎每次在 80% 之前就拔线，
> 所以苹果偶尔进行的满充校准，在这 <!--v:span_days-->76<!--/--> 天里一次也没轮到。依赖循环次数的结论（降压节点、预测）
> 不受影响；由电量计推算的容量和显示的 SOC 带有偏差，我无法量化。细节见
> [`docs/shallow-charging-accuracy.md`](docs/shallow-charging-accuracy.zh.md)。

---

## 设备

| ID | 平台 | 数据 | 覆盖 |
|----|------|------|------|
| [`iphone-01`](devices/iphone-01/) | **iPhone 17**，iOS 26.4.2，3.887V / 3692mAh / 4.50V 上限 | <!--v:snap_n-->9<!--/--> 份 analytics 快照 + 6 行健康导出，<!--v:sessions-->325<!--/--> 次充电会话，1 次电压读数 | 2026-09-01 → <!--v:base_date-->2026-11-17<!--/-->（<!--v:span_days-->76<!--/--> 天充电日志） |
| [`reference-01`](devices/reference-01/README.zh.md) | iOS 17.6.1，1420 次循环，3.83V / 2815mAh / 4.45V | 单份 analytics 快照，仅作参考 | 2026-11-15 |
| [`reference-02`](devices/reference-02/README.zh.md) | iOS 15.1，3.83V / 3110mAh / 4.45V | 铭牌 + 一份电量计快照（2919 次循环，67%）；没有 `VacVoltageLimit` | 2026-11-15 |

这两台参考机器本来就在手上，我用它们核对降压节点表、两种健康度算法和铭牌能量的
算术。它们不进入 `iphone-01` 的统计，也不进入它的预测。唯一作为数据出现的地方是
[`docs/lifetime-projection.md`](docs/lifetime-projection.zh.md) 里的跨设备锚点，那处
标注了它们是参考点。

更多设备可以作为 `devices/` 下的同级目录加进来。

---

## 主要发现

1. "电池健康度"有两个不同的数字。`nominal_health_pct`（<!--v:base_health_two-->99.13<!--/-->%）是
   `NominalChargeCapacity / 3692`，导出工具按固定铭牌算出的比值；苹果自己的
   `MaximumCapacityPercent` 读数是 101，而且跨过 200 次循环的阶跃时没有动。下面
   所有衰减数字说的都是 NCC 比值，不是 iOS 显示的值。见
   [`ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.zh.md) §6。

2. 衰减是阶梯式的。中间是 ~0.004%/天的平台期，属于真实的化学老化；另有两次一次性
   下降：126→152 次循环约 −0.41pp，194→208 次循环约 −0.43pp。

3. 194→208 这次下降跨过了第 200 次循环。这与一个流传较广（非官方）的机制吻合：
   iOS 在循环节点下调软件充电电压上限，200 / 250 / 300 每档 0.02V，1000 时 0.05V。
   4.50V 铭牌是电芯的硬件上限，软件目标设在它下面。见
   [`docs/voltage-nodes.md`](docs/voltage-nodes.zh.md)。

4. analytics 证实了 200 这个节点。`VacVoltageLimit` 恰好在第 200 次循环时为
   4480 mV，不是之后。另一台 4.45V 铭牌、1420 次循环的机器落在 4340 mV，正好是同
   一张表的预测：4.45 − 0.02×3 − 0.05 = 4.34 V。两个铭牌、两个 iOS 版本、一张表。

5. 这部分损失有一部分是可逆的。同一 4.50V 平台的 A/B 测试显示，把上限从 4500 降到
   4390 mV，报告容量少 8.0 pp，而 Qmax 不变；也就是说苹果"1000 次循环剩 80%"里
   大约 40% 是锁容，不是磨损。把目标电压降下来是保护性的。完整曲线见
   [`docs/lifetime-projection.md`](docs/lifetime-projection.zh.md)。

6. 充电行为：<!--v:sessions-->325<!--/--> 次会话、<!--v:span_days-->76<!--/--> 天、<!--v:efc-->98.83<!--/--> 次等效完整循环，平均速率
   <!--v:rate_mean-->1.65<!--/-->%/min（剔除异常后 <!--v:rate_mean_clean-->1.76<!--/-->%/min）。<!--v:zero_sessions-->18<!--/--> 次会话（<!--v:zero_pct-->5.5<!--/-->%）净充入为零，
   有一次插着电 SOC 反而下降；异常行共 <!--v:anom_sessions-->19<!--/--> 条（<!--v:anom_pct-->5.8<!--/-->%）。

7. `Raw Capacity` 是个会漂移的估计值，连续两份快照就能看出来：11-14 → 11-15 它从
   3683 走到 3692 mAh，而 `NominalChargeCapacity` 和健康度都没动。它最后正好落在
   3692 铭牌上，是巧合。

8. −0.43 pp 这个断崖是日常噪声的 16 倍。<!--v:snap_zh-->九<!--/-->份连续快照给出的 NCC 是
   <!--v:ncc_range-->3658–3660<!--/--> mAh（抖动 0.027 pp，回弹也算在内），而 `AppleRawMaxCapacity` 摆动了
   <!--v:raw_range-->30<!--/--> mAh（噪声大 <!--v:raw_ratio-->30<!--/--> 倍）。这把阶跃限定在 194→200 次循环之间，速率
   1.50 次循环/天。11-09 那份在第 200 次循环就已经是 4480 mV，说明阶跃在节点上发生；
   它的 `UpdateTime`（本地时间 2026-11-08 17:08）把变化推早到那天傍晚之前。11-12 是
   11-11 的过期重复上报，不是新的观测。

完整分析在 [`docs/findings.md`](docs/findings.zh.md)；
[`docs/corrections.md`](docs/corrections.zh.md) 记录了我在过程中搞错的地方，以及哪些
早先的说法现在已经作废。

---

## 数据与隐私

原始日志带有精确到秒的墙钟时间戳，这些不发布。公开的会话行只有 `session_id`、
`day_offset`（距首条记录的天数，没有日历日期）、`duration_sec`、`soc_start`、
`soc_end`、`charged_pct`、`rate_pct_per_min`、`anomaly`。发布原始时间戳会暴露
作息和出行规律，所以在解析时就去掉了。

有两个确实带行为信息的字段是公开的，与其不提，不如点名：每份 analytics 快照里的
`gauge_update_time_utc`（精确到秒；它正是用来区分"过期的重复上报"和"新的一次电量
计写入"），以及每日的 `daily_min_soc_pct` / `daily_max_soc_pct` 区间。健康导出表保留
日期，6 行，不含行为细节。序列号、UDID、具体机型变体和 analytics 文件名都不发布。
机型系列（`iPhone 17`）发布，具体变体不发布。

---

## 复现

```sh
# Import new analytics files, regenerate the forecast and run every check
scripts/update.sh /path/Analytics-A.ips /path/Analytics-B.ips

# Or only re-run the checks (also confirms the committed forecast equals a
# fresh regeneration, and scores pre-registered predictions)
python3 scripts/verify.py
python3 scripts/check_links.py

# Re-parse a private raw diary into the de-identified CSV
# (the raw diary is not in this repository)
python3 scripts/parse_charging_log.py /path/to/private/raw.txt \
    devices/iphone-01/charging-sessions.csv docs/charging-summary.json
```

| 路径 | 内容 |
|------|------|
| [`devices/iphone-01/health-samples.csv`](devices/iphone-01/health-samples.csv) | 6 行第三方健康导出，与 analytics 快照是两回事 |
| [`devices/iphone-01/charging-sessions.csv`](devices/iphone-01/charging-sessions.csv) | <!--v:sessions-->325<!--/--> 次去标识化会话 |
| [`devices/iphone-01/device.json`](devices/iphone-01/device.json) | 铭牌参数 |
| [`devices/iphone-01/voltage-reading.md`](devices/iphone-01/voltage-reading.zh.md) | 一次 4.04V @ 70% 读数与 OCV 核对 |
| [`docs/findings.md`](docs/findings.zh.md) | 完整分析 |
| [`docs/lifetime-projection.md`](docs/lifetime-projection.zh.md) | 跨设备的寿命推理，不是 iphone-01 的预测 |
| [`docs/iphone17-forecast.md`](docs/iphone17-forecast.zh.md) | 仅用 iphone-01 数据的曲线，按当前用量（<!--v:rate-->1.30<!--/--> 次循环/天 = <!--v:mah_day-->4801<!--/--> mAh/天） |
| `docs/iphone17-forecast.csv` / `.json` / `.svg` | 预测数据与图表 |
| [`docs/voltage-capacity-experiment.json`](docs/voltage-capacity-experiment.json) | A/B 测量：电压上限与报告容量 |
| [`scripts/forecast.py`](scripts/forecast.py) | 重新生成 iphone-01 的预测 |
| [`scripts/params.py`](scripts/params.py) | 从公开数据推导每一个预测参数 |
| [`scripts/update.sh`](scripts/update.sh) | 导入 → 时间线 → 预测 → 文档同步 → 校验 |
| [`scripts/sync_docs.py`](scripts/sync_docs.py) | 重填文档里带标记的数字（`<!--v:KEY-->…<!--/-->`、`<!--b:KEY-->…<!--/b-->`）；`--check` 在 `verify.py` 里跑 |
| [`scripts/check_links.py`](scripts/check_links.py) | 断链检查 |
| [`docs/predictions.json`](docs/predictions.json) | 事前登记的 250 节点预测，由 `verify.py` 打分 |
| [`docs/voltage-nodes.md`](docs/voltage-nodes.zh.md) | 循环节点电压表，以及它的出处 |
| [`docs/methodology.md`](docs/methodology.zh.md) | 字段定义、单位、已知局限 |
| [`docs/shallow-charging-accuracy.md`](docs/shallow-charging-accuracy.zh.md) | 满充校准为什么一次也没跑，以及影响哪些读数 |
| [`docs/corrections.md`](docs/corrections.zh.md) | 分析过程中发现的错误，附当前状态 |
| [`devices/iphone-01/ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.zh.md) | analytics 原始字段与已确认的降压阶跃 |
| `devices/iphone-01/analytics/YYYY-MM-DD.json` | 白名单抽取结果，每天一个文件 |
| [`devices/iphone-01/analytics-timeline.csv`](devices/iphone-01/analytics-timeline.csv) | 日期 / 循环 / 电压 / 健康度，每份快照一行 |
| [`docs/charging-summary.json`](docs/charging-summary.json) | 汇总统计 |
| [`scripts/verify.py`](scripts/verify.py) | 一致性检查 |
| [`scripts/parse_charging_log.py`](scripts/parse_charging_log.py) | 充电日志解析 / 去标识化 |
| [`scripts/extract_analytics.py`](scripts/extract_analytics.py) | analytics `.ips` 解析 / 去标识化 |
| [`scripts/ingest_analytics.py`](scripts/ingest_analytics.py) | 追加纯文本健康表导出 |

## 那张表的出处

循环节点电压表是第三方逆向出来的，不是苹果文档。苹果公开的只有"1000 次循环剩
80%"以及性能管理与优化充电的行为，没有任何降压阶梯的说法；仓库里所有相关表述都
按这个前提标注。

200 次循环这个阶跃在本机得到了确认：2026-11-09 的 analytics 里，`VacVoltageLimit = 4480 mV`
恰好出现在 `CycleCount = 200`；之后 <!--v:further_zh-->八<!--/-->份快照覆盖 <!--v:further_range-->202–212<!--/--> 次循环，读到的都是
4480 mV。见 [`devices/iphone-01/ANALYTICS-EVIDENCE.md`](devices/iphone-01/ANALYTICS-EVIDENCE.zh.md)。

iOS 只保留大约 7–8 天的 analytics，所以 200 次循环之前的快照（4500 mV 那档）已经
拿不到了。生命周期峰值 `MaximumPackVoltage = 4496 mV` 是 09-01 之前那次满充留下的
化石（≈101 次循环时 4.50V 上限还有效）；现在充电停在 81% SOC，峰值也不会再被刷新。

## 喂入新的 analytics 文件

任何 `.ips` / `.ips.ca.synced` 每日 analytics 文件都可以，一天一份：NDJSON，第一行
是 header，后面是带名字的聚合记录。可以一次导入多份。

```sh
python3 scripts/extract_analytics.py --archive /path/Analytics-A.ips /path/Analytics-B.ips
```

`scripts/update.sh` 做同样的事，之后还会重算预测并跑检查。`sync_docs.py` 负责重填
文档里带标记的数字（基点、速率、节点日期、快照数、时间线表），未标记的文字不动，
新的发现仍然要手写。

每份文件写到 `devices/iphone-01/analytics/<header-date>.json`，`analytics-timeline.csv`
整体重建，每份快照都会与节点表（4500 / 4480 / 4460 / 4440 / 4390 mV）核对；对不上
会打印 `??`，不会默默通过。同一天重复导入会原地更新。GitHub Actions 每次 push 都跑
`verify.py`、断链检查，以及原始文件 / 标识符扫描。

只导出白名单里的数值字段。原始文件含 deviceId、UUID、运营商 / 国家、incident ID，
永远不进仓库。200 次循环之前的快照尤其有价值。纯文本健康表导出用
`scripts/ingest_analytics.py`。

## 许可

数据与脚本：CC0-1.0。见 [`LICENSE`](LICENSE)。
