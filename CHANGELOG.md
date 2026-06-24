# Changelog

所有版本变更记录。每次更新都会在这里记录版本号、变更内容和影响。

---

## v0.4.1 — 2026-06-24: 脚本同步更新：article-pipeline/sourcing-hotspots/angle-selection prompt微调

### 变更文件
-  angle-selection/SKILL.md   |  2 ++
-  article-pipeline/SKILL.md  | 14 +++++++++
-  sourcing-hotspots/SKILL.md | 71 +++++++++++++++++-----------------------------
-  3 files changed, 42 insertions(+), 45 deletions(-)

---

## v0.4.0 — 2026-06-22: zvec 知识库集成

**核心变更**：接入阿里开源 zvec 向量搜索库，为流水线增加"记忆"能力。

### 新增模块
- `zvec/zvec_kb.py` — 本地向量知识库 CLI，4 个 collection（topics/angles/competitors/style_anchors）
- embedding 模型：shibing624/text2vec-base-chinese（768维）

### 5 个检索场景
1. **选题去重** — 新选题和历史选题做向量相似度匹配（阈值 0.65）
2. **角度库** — 搜索历史角度避免重复造轮子
3. **竞品内容库** — 搜索竞品是否写过类似内容
4. **风格锚点** — 检查文章风格是否符合要求（good/bad 对比）
5. **混合检索** — 向量 + 关键词跨库搜索

### Agent prompt 变更
- `screening-agent-prompt.md` — 新增 Step 1.5 选题去重检查
- `quality-agent-prompt.md` — 新增 Step 0.5 风格相似度检查
- `angle-selection/SKILL.md` — 新增 Step 0 搜历史角度
- `main-agent-prompt.md` — 新增 Step 2/3 存库操作 + Step 8 发布后回写

### 知识积累闭环
每次流水线跑完，文章自动变成下一次的风格参考和选题去重依据。跑得越多，库越厚，质量越稳。

---

## v0.3.0 — 2026-06-17: Agent Prompt 优化

**核心变更**：基于两次全流程验证，优化所有 Agent prompt 的遵守率。

### 关键优化
- **负面示例约束**：所有 prompt 加入"不能用XX，如XX"的负面示例，显著提高 AI 遵守率
- **评分体系统一**：筛选 Agent 强制 50 分制（5 维度×2 权重），禁止自创评分体系
- **框架约束**：结构 Agent 强制从 5 种预设框架（AIDA/PAS/故事弧线/对比/递进）选择，禁止自创框架名称
- **钩子规则**：钩子可以用设问句，但正文不能用设问引导
- **质检维度**：质检 Agent 禁止自创检查维度，必须按 L0-L6 固定维度检查
- **L6 补充检查**：正式纳入数据来源、合规风险、竞品表述、宣传口径、互动引导、话题标签
- **小红书风格**：写作 Agent 新增口语化、短段落、emoji、互动引导等平台适配要求

### 验证结果
- 第一次验证：5 个 Agent prompt 问题（未遵守评分、自创框架等）
- 第二次验证：所有问题修复，文章质量明显提升

---

## v0.2.0 — 2026-06-10: 多 Agent 协同体系

**核心变更**：从单 Agent 升级为 8 Agent 协同体系。

### 8 个 Agent
| Agent | 职责 | Prompt 版本 |
|-------|------|------------|
| 主 Agent | 纯调度（流程控制、信息传递、决策） | v3 |
| 热点数据 Agent | 热点数据质量评估 | v2 |
| 筛选 Agent | 热点筛选 + 50 分制评分 | v4 |
| 结构 Agent | 文章结构分析 + 框架推荐 | v4 |
| 写作 Agent | 事实补充驱动写作 | v1 |
| 质检 Agent | L0-L6 七层质检 | v3 |
| 修复 Agent | 按质检报告修复文章 | v1 |
| 发布 Agent | 飞书文档发布 | v1 |

### 核心设计原则
- 主 Agent 只做调度，不写文章、不搜索、不发布
- 事实补充驱动：写之前必须先搜索事实，搜够了再写
- 信息传递标准化：Agent 间传递信息遵循 message-format.md
- 迭代轮次管理：质检→修复→重质检最多 3 轮

### 流程
```
Step 1: 抓热点 → Step 1.2: 数据质量评估 → Step 1.5: 筛选
→ Step 2: 选题确认 → Step 3: 选角度 → Step 3.5: 结构分析
→ Step 4: 定调 → Step 5: 写正文 → Step 5.5/6: 质检
→ Step 6.5: 修复 → Step 7: 发布
```

---

## v0.1.0 — 2026-06-06: 初始版本

**核心变更**：建立基础内容创作流水线。

### 基础模块
- `article-pipeline/` — 主流水线 SKILL
- `sourcing-hotspots/` — 热点抓取（hot-aggregator 多平台聚合）
- `screening-topics/` — 选题筛选（五问审查 + 传播势能判断）
- `angle-selection/` — 角度选择（三轴旋转法 + SPOV 评分）
- `framing-article/` — 文章定调（标题先行 + 支柱性类比）
- `writing-draft/` — 正文撰写（卡兹克风格）
- `polishing-writing/` — 四层写作自检
- `publishing-doc/` — 飞书文档发布

### 写作风格
- 默认卡兹克结构（Hook→铺垫→核心→收束）
- 30 篇文章的活人感技巧（过渡词替换表 8 个×5 个真实示例）
- 事实补充驱动方法论

### 热点分层
- 第一层：全网热点（社会/国际/财经/文娱/体育）
- 第二层：关注领域热点（汽车/3C/AI/家居）

---

## 版本命名规则

- **主版本.次版本.补丁版本**（如 v0.4.0）
- 主版本：架构级变更（如从单 Agent 到多 Agent）
- 次版本：功能新增（如新增 zvec 知识库）
- 补丁版本：prompt 修复、bug 修复、文档更新
