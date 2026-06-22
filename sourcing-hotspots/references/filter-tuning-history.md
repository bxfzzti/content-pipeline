# filter_all_categories.py 调优记录

## 2026-06-07: 五项修复（23条→51条，+122%）

### 问题诊断
用户反馈"按照现在的规则没什么可写的"。漏斗分析发现：

```
原始数据 2900条
  → 48h时间过滤: 仅保留591条（79%被丢弃）
  → 噪音词+平台过滤: -68条
  → 品牌+事件双命中: 大量条目有品牌无事件被丢弃
  → 最终: 23条（汽车7 + 3C11 + AI1 + 家居4）
```

### 修复清单

| # | 问题 | 修复 | 效果 |
|---|------|------|------|
| 1 | 48h时间窗口太严 | 放宽至72h | +36条国内数据 |
| 2 | AI事件关键词只有中文 | ai_events加入英文事件词 | AI品类1→15条 |
| 3 | 汽车品牌缺漏 | 新增红旗/捷途/星途/银河/极越/奕境/极石 | 红旗G919首次命中 |
| 4 | 事件关键词太窄 | auto_events加入涨价/新能源/造车等；ai_events加入成本/能耗/数据中心等 | 趋势文归类 |
| 5 | 无趋势品类 | classify()末尾新增趋势auto+趋势AI，用高信号关键词匹配 | +5条趋势文 |

### 具体变更

**auto_brands 新增：** 红旗|捷途|星途|银河|极越|奕境|极石

**auto_events 新增：** 涨价|新能源|电动车|造车|车企|汽车市场|越野车|硬派

**ai_events 新增（中文）：** 成本|能耗|效率|数据安全|隐私|数据中心|失业|就业|审查

**ai_events 新增（英文）：** equity|stake|launch|announce|release|unveil|raise|funding|valuation|acquire|partnership|deploy|rollout|security|regulation|ban|pricing|revenue|billion|million|readying|comply|hack|attack|warn|urge|call.for|impact|replace|automat

**新增趋势品类：**
```python
# 趋势/行业品类（无品牌但有行业趋势信号，仅限高信号关键词）
trend_auto = r'新能源车涨价|新能源车降价|造车新势力|车市|汽车市场格局|车企淘汰|智驾普及|充电桩涨价|电池涨价|动力电池|固态电池'
trend_ai = r'AI监考|AI搜题|AI就业|AI失业|AI教育|AI医疗|AI成本|AI能耗|AI监管|AI审查|算力中心|数据中心|AI产业|大模型降价|大模型免费|AI替代|人工智能产业|AI芯片禁令|芯片股'
```

### 后续优化方向
- 3C品类改善有限（11→12），需要研究3C漏掉的条目原因
- 英文RSS中仍有一些误匹配（Crypto-Funded Chinese Peptide Labs误命中Anthropic品牌）
- 趋势关键词列表需要持续扩充（根据实际热点调整）
- linuxdo等噪音平台的API调试类文章偶尔被误归AI，需加强AI黑名单

## 2026-06-04: 初始版本（v3）
- 跨品类品牌分流
- 3C黑名单
- AI品牌+事件双命中
- 噪音平台硬排除
- 家居高频词上下文验证
- 黑名单大小写不敏感
