# Filter Script Changelog — 2026-06-07

## Problem
filter_all_categories.py produced only 23 items from 2900 raw entries (0.8% yield).
Root cause: 5 structural issues causing massive data loss.

## Fixes Applied

### 1. Time window 48h → 72h
- Line: `dom_cutoff_ms = now_ms - 72 * 3600 * 1000`
- Why: Hot-aggregator "hot lists" show what's trending NOW, not what was published in 48h. 75% of data was >48h old.
- Impact: 591→627 retained items (+6%)

### 2. English AI event keywords (30+ added)
- Added: equity, stake, launch, announce, release, unveil, raise, funding, valuation, acquire, partnership, deploy, rollout, security, regulation, ban, pricing, revenue, billion, million, readying, comply, hack, attack, warn, urge, call for, impact, replace, automat
- Why: International RSS (TechCrunch/Wired/Ars) content matched AI brands but event keywords were all Chinese → silent drop
- Impact: AI category 1→13 items

### 3. New auto brands
- Added: 红旗, 捷途, 星途, 银河, 极越, 奕境, 极石
- Impact: 红旗G919硬派越野首次命中

### 4. New auto event keywords
- Added: 涨价, 新能源, 电动车, 造车, 车企, 汽车市场, 越野车, 硬派
- Impact: "多款新能源车涨价了" "蜂巢能源动力电池" 命中

### 5. Trend/industry category (new)
- Auto trends: 新能源车涨价|新能源车降价|二手车.*崩盘|动力电池|固态电池
- AI trends: AI监考|AI搜题|AI就业|芯片股|太空算力|算力中心|数据中心
- **PITFALL: trend keywords must match in TITLE only, not desc.** "教育部高考十问十答" had "AI监考" only in desc → false positive.

### 6. Noise platform stricter filter
- Old: skip unless core AI brand present
- New: skip unless core AI brand AND event keyword both present
- Why: linuxdo developer tutorials with "OpenAI API" were passing through

### 7. OpenAI blog marketing filter
- Added: source=='openai' AND title matches How.*redesign|How.*build|case study|leveraging → skip
- Why: OpenAI blog case studies were being classified as AI news

### 8. RSS long-form source title-only matching
- Added Wired, ArsTechnica, MIT-TR, TechCrunch, TheVerge to ROUNDUP_PLUS (title-only matching)
- Why: Long-form articles have irrelevant topics in desc, causing false brand matches (e.g., "Crypto-Funded Peptide Labs" matched "Anthropic" in desc)

### 9. AI blacklist expanded
- Added: depth解析|后缀到底, gateway to building|pet was, the better way to use|怎么用, peptide|crypto.*lab|booming
- Filters: developer tutorials, personal stories, usage guides, unrelated industries

### 10. Deduplication (new)
- After classification, titles with >30% word overlap keep only the first match
- Why: Trump/OpenAI stake appeared from both TechCrunch and Engadget

## Results
- Before: 汽车7 | 3C11 | AI1 | 家居4 | Total23
- After:  汽车12 | 3C12 | AI13 | 家居5 | Total42 (+83%)
