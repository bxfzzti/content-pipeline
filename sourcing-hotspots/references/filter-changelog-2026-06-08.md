# filter_all_categories.py 变更日志

## 2026-06-08 更新

### 1. 时间窗口放宽：48h → 72h
热榜数据75%超过48小时，放宽到72h保留更多有效数据。

### 2. 汽车品牌扩充
新增：红旗、捷途、星途、银河、极越、奕境、极石

### 3. 汽车事件词扩充
新增：涨价、新能源、电动车、造车、车企、汽车市场、越野车、硬派

### 4. AI 事件词扩充（含英文）
新增中文：成本、能耗、效率、数据安全、隐私、数据中心、失业、就业、审查
新增英文：equity、stake、launch、announce、release、unveil、raise、funding、valuation、acquire、partnership、deploy、rollout、security、regulation、ban、pricing、revenue、billion、million、readying、comply、hack、attack、warn、urge、call for、impact、replace、automat

### 5. 新增趋势品类
无品牌但有行业趋势信号的关键词，仅限标题命中：
- 趋势汽车：新能源车涨价、新能源车降价、造车新势力、车市、二手车崩盘、油车崩盘
- 趋势AI：AI监考、AI搜题、AI就业、AI成本、AI能耗、芯片股、太空算力

### 6. 噪音平台收紧
原来：噪音平台只排除非AI内容
现在：噪音平台要求品牌+事件双命中才放行（过滤开发者教程）

### 7. AI 黑名单扩充
新增：depth解析、后缀到底、gateway to building、pet was、the better way to use、peptide、crypto.*lab

### 8. RSS 长文源只用标题匹配
新增 Wired、ArsTechnica、MIT-TR、TechCrunch、TheVerge 到标题匹配列表

### 9. 去重逻辑
标题词重叠 >30% 的条目只保留第一条

### 10. OpenAI 博客过滤
营销/case study 内容不归 AI 品类
