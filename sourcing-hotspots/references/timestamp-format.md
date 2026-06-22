# hot-aggregator 时间戳格式

## `item.timestamp` 字段

每个平台的每条数据都有 `timestamp` 字段（毫秒级 epoch）。

### 正常平台
- `ithome`: 正常毫秒epoch，如 `1780457220097` = 2026-06-03
- `weibo`: 正常
- `douyin`: 正常
- `zhihu`: 正常
- `huxiu`: 正常
- `geekpark`: 正常

### 异常平台
- `toutiao`（头条）: timestamp 为负值或极小值（如 `-2124087364602`），**不可用于时间过滤**，已自动跳过
- 部分平台可能无 timestamp 字段（值为 0）→ 保留这些条目（宁可多收录不可漏掉）

## 实测数据分布（2026-06-04）
- 总条目: 2938
- 超过48h: 2214 (75.4%)  ← 这就是为什么要过滤
- 48h内: 724
- 时间戳异常: 少量（主要是toutiao的50条）

## 过滤逻辑
```
if timestamp > 0 and timestamp < now_ms - 48h:
    skip  # 太旧
elif timestamp < 0 or timestamp > now_ms + 1h:
    skip  # 时间戳异常
else:
    keep  # 包括 timestamp==0 的条目
```
