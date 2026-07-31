---
name: screening-topics
description: 筛选题时使用。接收热点列表，跑六问审查 + 内容策略门槛 + 传播势能判断，输出 S/A/B 级选题建议。
---

# screening-topics

接收代码预筛短名单 → 模型补充语义判断 → 代码复算并输出 S/A/B 级选题建议。**只出建议，不写正文。**

## 产物与进度（强制）

开始时先发进度：「正在跑 2/7 选题筛选，会做六问审查、内容策略三问和 zvec 去重。」

完成后必须生成 `/tmp/article-pipeline/02a-model-judgments.json`、`02-topic-suggestion.json` 和 `02-topic-suggestion.md`。不得再使用「manual_screening」降级文本代替结构化结果。

聊天中输出至少 5 个、最多 10 个选题的紧凑结果：标题、内容线、总分、核心判断、推荐角度、反面理由、原文链接。六问和各维度展开写入产物文件，不在聊天中逐条铺开，不使用 Markdown 表格。

开始前必须读取并校验 `/tmp/article-pipeline/01c-screening-candidates.json`。该文件由热点脚本确定性生成，最多 15 条；模型禁止重新扫描完整热点池、重新搜索或加入短名单之外的话题。统一输入契约见 `../article-pipeline/references/hotspot-output-contract.md`。

## 固定分工（强制）

代码负责：时效门槛、全网热度、时效性、讨论热度、同事件去重、短名单、总分、等级、排序、数量和品类配比。

模型只负责：情绪强度、内容关联度、内容线判断、账号资产价值、核心判断、推荐角度、反面理由、读者认知起点、下一步要求和六问通过数。

模型不得输出或修改 `heat_score`、`freshness_score`、`discussion_score`、`writing_value_score` 和等级。

## Step 1: 接收代码短名单

只读取 `01c-screening-candidates.json` 的 `candidates`。其中前三项固定分和时效状态已经锁定。

关键词系统和 KOL 账号列表详见 `references/screening-reference.md`。

✅ 每条热点条目标记所属品类和命中关键词数。

## Step 2: 生成模型语义判断

默认由 `scripts/run_screening_once.py` 使用 `deepseek-v4-flash` 一次完成全部候选判断，主 Agent 不再逐条读写和多轮调度。

不得再次调用 web、zvec、子 Agent 或热点工具。对每个候选只填写以下 JSON 字段，并写入 `/tmp/article-pipeline/02a-model-judgments.json`：

```json
{
  "run_id": "原样复制 01c-screening-candidates.json 顶层 run_id",
  "judgments": [{
    "candidate_id": "C01",
    "emotion_score": 4,
    "relevance_score": 5,
    "content_line": "hot_take / decision / framework",
    "line_reason": "为什么这条题应该走这条内容线",
    "asset_value": 4,
    "core_judgment": "一句明确判断",
    "recommended_angle": "一个最值得写的角度",
    "risk": "最严重的反面理由",
    "reader_start": "读者第一反应",
    "next_stage_requirement": "进入下一步前必须补的证据或必须选择的模板",
    "six_question_pass_count": 5
  }]
}
```

`run_id` 是本轮契约键，禁止省略或自行生成。终审脚本会拒绝任何上一轮遗留的模型判断。

`content_line` 是正式筛选结果的一等字段，不是展示标签：

- `hot_take`：热点观点线，借公共情绪、冲突和新事实输出锐利判断。
- `decision`：消费决策线，回答买不买、怎么选、避什么坑、产品体验是否可信。
- `framework`：长期框架线，把热点沉淀成判断方法、选购框架或行业/消费决策模型。

内容线按“读者承诺”判断，不按品类硬分。汽车、3C、智能家居都可以进入三条线：写“我怎么看”是 `hot_take`，写“该不该买/怎么选/该等还是该避”是 `decision`，写“以后遇到这类产品、品牌叙事或技术路线怎么判断”是 `framework`。汽车是高客单价产品，不能因为来源是汽车媒体就默认归为热点观点线。

`candidate_type=product_experience` 的候选来自什么值得买等产品体验池，默认优先考虑 `decision`，但模型仍可因单篇体验弱、证据不足或不适合二创而降低关联度或写“不适用”。

## Step 3: 六问选题审查

每条候选话题逐一跑六问：

```
Q1 事实层：≥3 个独立可查证的事实点？
Q2 争议空间：至少 2 种不同立场且都有受众？
Q3 趋势关联：能从这件事推导出这类事的走向？
Q4 独到角度：有至少 1 个别人不会说的核心判断？
Q5 行动指引：读者看完能做出具体 decision？
Q6 认知起点：读者看到这个话题时最顺理成章的反应是什么？
```

**决策**：6/6→S级、5/6→A级、4/6→B级、≤3/6→放弃。写不出认知起点→降为 B 级。

✅ 每条候选只在 JSON 中输出六问通过数和认知起点，不展开长报告。

## Step 3.5: 内容策略门槛

用老板内容策略做三问，不满足则降级：

```
S1 内部视角：能不能给出行业内部视角/品牌战役叙事，而不是复述新闻？
S2 反直觉/争议：有没有跟大众认知不同、可争论的判断？
S3 消费结论：读者看完能不能形成“买/不买/等/怎么选/避什么坑”的具体决策？
```

✅ 每条 S/A 级候选必须至少满足 2/3；只满足 1 项降为 B 级，0 项放弃。

五问详情和审查细则详见 `references/screening-reference.md`。

## Step 4: 代码复算与收口

写完模型判断 JSON 后必须执行：

```bash
python3 ~/.hermes/skills/screening-topics/scripts/finalize_screening.py
```

最终总分只能由该脚本计算。脚本失败时修复 JSON，不得手工计算或直接回复用户。

## Step 5: 输出选题建议

按金字塔原理：**先给最终排序结论，再给理由。**

格式按内容线分组：
```
结论：今天优先写 A，其次是 B。

热点观点线：
1. A — S级 — 为什么值得写 — 下一步要补什么

消费决策线：
1. B — A级 — 为什么值得写 — 下一步要补什么

长期框架线：
1. C — B级/储备 — 为什么暂缓或如何沉淀
```

完成脚本后不要在模型回复中重述热点或选题，只回复「筛选产物已生成」。运行时会读取 `02-topic-suggestion.md`，并与两层热点确定性组装成最终确认包。

✅ 选题结论作为独立消息块发给用户，不与工具输出紧邻。

## 关键约束

- **用户自带选题/标题时跳过筛选**：直接进入 angle-selection 或 framing-article。
- **赛道 ≠ 选题**：不要跳过筛选，仍从 sourcing-hotspots 开始。
- **语义判断 + 代码预筛结合**：代码完成机械判断，模型只做语义细筛。
- **时效性硬门槛**：必须读取 `published_at/age_hours/freshness_status`。0-24h 强时效，24-48h 正常；48-72h 默认转储备，只有跨 3+ 平台且最近 24h 有新证据才能推荐；超过 72h 禁止进入“今天推荐”。实时热榜缺发布时间时可用当前榜单作证，普通文章缺时间不得进入 S/A 级。
- **禁止猜时效**：不得凭模型记忆、品牌知名度或标题措辞判断“刚发布”。单维度 5 分规则不得绕过时效硬门槛。
- **推荐数量与多样性**：正常至少输出 5 个，最多 10 个；同一事件只保留 1 条，同一品牌最多 2 条，同一车型/产品最多 1 条，汽车默认不超过最终列表一半。若合格候选不足 5 个，必须说明缺口、时效淘汰数量与原因，禁止用旧题或低质量题凑数。
- **评分口径**：前三项来自代码，后两项来自模型，`writing_value_score` 必须由 `finalize_screening.py` 复算；严禁模型自报总分。
- **内容线继承**：后续 angle-selection、framing、writing 必须读取 `content_line`。热点观点线优先定立场，消费决策线优先给行动建议，长期框架线优先沉淀方法。

## 参考

- 关键词体系、KOL 账号、五问详情、传播势能标准、多方向模式：`references/screening-reference.md`
- 坑位记录：`references/pitfalls.md`
- 筛选 Agent prompt：`references/screening-agent-prompt.md`
