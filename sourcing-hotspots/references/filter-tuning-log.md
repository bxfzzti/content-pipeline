# 热点过滤器调优记录（2026-06-07）

## 问题诊断

原始过滤器从 2900 条热点中只保留 23 条（0.8%），原因是 5 个结构性问题。

## 5 个修复及效果

### 1. 时间窗口放宽 48h → 72h
- **问题：** 热榜数据 75% 超过 48h，但"热榜"显示的是当前趋势，不是发布时间
- **修复：** `dom_cutoff_ms = now_ms - 72 * 3600 * 1000`
- **效果：** 国内保留 591→627 条
- **位置：** filter_all_categories.py line ~223

### 2. AI 英文事件关键词（30+词）
- **问题：** 英文 RSS（TechCrunch/TheVerge 等）的 AI 新闻只有中文事件词，导致 OpenAI unveil、Anthropic readying、Trump equity stake 等大新闻被漏
- **修复：** ai_events 正则增加英文词：`equity|stake|launch|announce|release|unveil|raise|funding|valuation|acquire|partnership|deploy|rollout|security|regulation|ban|pricing|revenue|billion|million|readying|comply|hack|attack|warn|urge|call.for|impact|replace|automat`
- **效果：** AI 品类 1→22 条

### 3. 汽车品牌列表扩充
- **新增品牌：** 红旗|捷途|星途|银河|极越|奕境|极石
- **新增事件词：** 涨价|新能源|电动车|造车|车企|汽车市场|越野车|硬派
- **效果：** 红旗 G919 首次命中，"新能源车涨价"趋势文归类

### 4. 趋势/行业品类（无品牌趋势信号）
- **问题：** "多款新能源车涨价了""AI监考""芯片股暴跌"等无品牌趋势文无法归类
- **修复：** 新增 trend_auto/trend_ai 关键词列表，**必须在标题中命中**（不能只在 desc 中）
- **位置：** classify() 函数末尾，return None 之前
- **效果：** +5 条行业趋势文

### 5. 噪音平台收紧
- **问题：** linuxdo 的 AI API 教程被保留
- **修复：** 噪音平台要求 **品牌+事件双命中** 才放行（原来只要求品牌命中）
- **代码：** `core_ai_events` 正则 + `re.search(core_ai, text) and re.search(core_ai_events, text, re.I)`

## 3 个额外修复（清理阶段）

### 6. RSS 长文源只用标题匹配
- **问题：** Wired/ArsTechnica 的长文 desc 中包含无关品牌名（如 Anthropic 出现在肽实验室文章的 desc 中）
- **修复：** `ROUNDUP_PLUS = ROUNDUP_SOURCES | {'Wired', 'ArsTechnica', 'MIT-TR', 'TechCrunch', 'TheVerge'}`
- **效果：** 去掉 Wired peptide labs 等 desc 误匹配

### 7. OpenAI 博客营销过滤
- **问题：** OpenAI 博客的 case study / customer story 被归为 AI 新闻
- **修复：** `if source == 'openai' and re.search(r'How.*redesign|How.*build|case study|customer story|is using|leveraging', title, re.I): return None`

### 8. 去重逻辑
- **问题：** 同一事件在不同平台出现多次（如 Trump/OpenAI stake 在 TechCrunch+Engadget）
- **修复：** 标题词重叠 >30% 只保留第一条
- **位置：** classify 完成后、输出之前

## 最终效果对比

| 品类 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 汽车 | 7 | 12 | +71% |
| 3C | 11 | 12 | +9% |
| AI | 1 | 13 | +1200% |
| 家居 | 4 | 5 | +25% |
| 总计 | 23 | 42 | +83% |

## 还存在的问题

- AI 品类仍可能有噪音（高考+AI 是教育新闻还是 AI 新闻？边界模糊）
- 家居品类始终偏少（中文家居媒体无 RSS）
- 3C 品类改善不大（品牌+事件双命中仍然较严）
