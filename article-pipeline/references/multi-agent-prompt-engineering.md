# Multi-Agent Prompt Engineering Methodology (2026-06-17)

## Core Insight

User: "这些 prompt 还是偏描述性质的呀...AI读到这些的时候，你并没有对这些框架做展开，那么 AI 怎么理解到底是哪些框架呢？"

**Lesson: Prompts must be fully expanded, not just titled.** Each framework, each scoring dimension, each decision rule needs concrete examples and templates.

## Prompt Structure Pattern (proven through 3 rounds of iteration)

### 1. Forced Constraints at Top

Put 6-8 hard rules at the very top, before any methodology. These are "you MUST do X" rules that override everything else.

```
## 强制约束（必须遵守）
1. 必须用web_search验证关键数字
2. 必须逐层检查
3. 必须给出具体修复建议
...
```

### 2. Expanded Frameworks (not just names)

Bad: "选择框架：AIDA/PAS/故事弧线/对比结构/递进结构"
Good: Each framework has:
- 适用场景 (when to use)
- 结构模板 (step-by-step template)
- 每一步怎么做 (concrete instructions with examples)
- 配套钩子 (which hook type pairs with it)

### 3. Decision Trees (not just rules)

Bad: "优先选热度评分最高的"
Good:
```
素材中有没有明确的人物？
├── 有，而且有戏剧性转折
│   └── 用【故事弧线】
├── 有，但没有明显转折
│   └── 看写作目的：需要说服→AIDA，需要指出问题→PAS
└── 没有明确人物
    └── 有两个可比对象→对比结构，需要由浅入深→递进结构
```

### 4. Self-Check Checklist

Every agent must have a self-check step before output:
```
### 自检清单
- [ ] 是否按格式输出？
- [ ] 是否验证了关键数据？
- [ ] 每个问题是否给出了修复建议？
```

### 5. Complete Input→Output Example

Bad: "输出格式：{...}"
Good: A full example showing:
- What the input looks like
- What the output should look like
- The reasoning process in between

## Testing Pattern

1. Write prompt v1 → test with real data → find issues
2. Fix issues → write prompt v2 → test again
3. Iterate until prompt produces correct output consistently

Key testing discoveries:
- v1 prompts: Agent didn't follow scoring system (used 10-point instead of 40-point)
- v2 prompts: Agent skipped self-check steps
- v3 prompts: Agent produced correct output after forced constraints added

## Information Transfer Format (message-format.md)

All inter-agent communication must follow standardized formats:

```
主Agent → 筛选Agent: 热点数据(结构化) + 内容定位
筛选Agent → 主Agent: 选题推荐(热度评分+切入方向+反面理由+差异化建议)
主Agent → 结构Agent: 事实材料 + 读者已知信息 + 切入方向
结构Agent → 主Agent: 结构方案(框架+钩子+逻辑链+自检清单)
主Agent → 写作Agent: 文章骨架 + 结构方案 + 事实材料 + 风格要求 + 平台要求
主Agent → 质检Agent: 文章正文 + 事实材料 + 结构Agent输出 + 平台要求
质检Agent → 修复Agent: 质检报告 + 原文
修复Agent → 主Agent: 修复报告 + 修复后的文章
主Agent → 发布Agent: 文章正文 + 标题 + 备选标题
```

## The 8-Agent Architecture

| Agent | Role | Key Constraint |
|-------|------|---------------|
| Main Agent | Pure orchestrator | Only does flow control + info passing + decisions |
| Hotspot Data Agent | Data quality | Auto-dedup, auto-fix classification, mark emotion intensity |
| Screening Agent | Topic selection | 40-point scoring, dynamic angle types, single-dimension breakout |
| Structure Agent | Article structure | Decision tree for framework, paired hooks, combination frameworks |
| Writing Agent | Write content | Fact-driven: search first, write second |
| Quality Check Agent | Quality check | L0-L5 six layers, severity quantification, reader simulation |
| Fix Agent | Fix issues | Fix by severity order, mark original→fixed, verify no new issues |
| Publishing Agent | Publish to Feishu | Auto-generate 5×2 backup titles, auto-authorize |

## Critical User Corrections

1. **"AI没有'我跟这个话题之间发生了什么'的认知流程"** — AI writing is fact-driven, not narrative-driven. Search facts first, organize second.

2. **"不应该是发布前再检查 而是每一步都要检查 分一个 agent 出来"** — Quality check must happen at every step, not just before publishing.

3. **"主 Agent 既要组装信息，又要搜索事实，还要写正文、发布，这几个环节都给它一个人干会乱掉吧"** — Main agent must be pure orchestrator, each task goes to a dedicated agent.

4. **"你先把两个 Prompts 怎么写的，先发给我看一下"** — User wants to see full prompt content, not just summaries.

5. **"这些 prompt 还是偏描述性质的呀"** — Prompts must be fully expanded with concrete examples, not just titled frameworks.
