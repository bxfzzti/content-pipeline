# Changelog

所有版本变更记录。每次更新都会在这里记录版本号、变更内容和影响。

---

## v0.6.8 — 2026-07-16: Linkly 本地检索前置条件校准

**核心变更**：根据 Desktop 和 HTTP MCP 实跑结果，区分监听文件夹与知识库，修正本地检索可用性判断。

### 变更内容

- 明确「设置 → 文件夹」中的监听目录负责本地索引，是本地检索的必要条件。
- 明确「知识库 / Libraries」是可选主题组织层；`list_libraries` 空列表不代表本地检索不可用。
- 改用一次真实 MCP `search` 判断本地索引是否可检索。
- 区分「Linkly 本地资料不可用」与「Linkly 本地资料未命中」，两种情况均可降级到 web/search/zvec。
- 已用 `/Users/xxqq/content-pipeline` 监听目录完成 `search → outline → read` 回归。

---

## v0.6.7 — 2026-07-16: Linkly 接入方式校准

**核心变更**：将 Linkly AI 试点说明校准为 HTTP MCP 主接入方式，CLI 仅用于诊断和本地调试。

### 变更内容

- 明确主接入：`linkly-ai -> http://127.0.0.1:60606/mcp`。
- 明确 CLI 只用于 `linkly status`、`linkly doctor` 等诊断动作，不是主接入依赖。
- 明确前置条件：Linkly AI Desktop 必须运行，并配置可供检索的本地资料来源；监听文件夹与知识库的准确分工在 v0.6.8 中补充校准。
- 明确暂不启用 Remote Tunnel；本机 Hermes/Codex 直连 `127.0.0.1`。

---

## v0.6.6 — 2026-07-16: Linkly AI 本地资料检索试点

**核心变更**：启动 Linkly AI 试点，将其定位为本地资料检索层，用于历史资料检索、写作前事实补充和质检反查。

### 变更内容

- README 新增 Linkly AI 与 zvec、daily-hot-mcp 的分工说明。
- `article-pipeline/SKILL.md` 新增 Linkly AI 试点边界：不进入外部热点抓取，不替代 zvec。
- `references/data-flow.md` 增加按需本地证据文件 `/tmp/article-pipeline/03c-local-evidence.md`。
- 本机已安装 Linkly AI CLI/Desktop，并注册 Codex MCP：`linkly-ai -> http://127.0.0.1:60606/mcp`。

---

## v0.6.5 — 2026-07-10: README 金字塔结构重写

**核心变更**：重写 README 的使用描述，按「它是什么 → 解决什么问题 → 怎么工作 → 输出什么 → 核心能力 → 运行方式」组织信息。

### 变更内容

- 第一屏先说明产品定义，不再直接进入架构术语。
- 将三层架构、中文呈现原则等规则后移到能力和组织方式部分。
- 把产品体验线、二创打分、飞书选题池、zvec 知识库按能力模块重排。
- 保留原有命令和真实输出示例，但调整到更符合用户阅读顺序的位置。

---

## v0.6.4 — 2026-07-10: 对外名称更新

**核心变更**：将仓库对外展示名更新为「会自己找选题的小红书内容创作流」，更明确表达这套流程的主要使用场景。

### 变更内容

- README 主标题改为「会自己找选题的小红书内容创作流」。
- GitHub 仓库描述同步改为小红书内容创作流定位。
- 保留仓库 URL `content-pipeline` 不变，避免影响已有链接。

---

## v0.6.3 — 2026-07-10: 中文呈现原则

**核心变更**：明确内容创作流的所有用户可见内容默认用自然中文呈现，不依赖 GitHub 或浏览器自动翻译。

### 变更内容

- README 新增「中文呈现原则」。
- `article-pipeline/SKILL.md` 新增强制中文输出规则。
- 明确代码标识、命令、文件名、API 字段可保留英文，但解释、建议、阶段产物、飞书记录和发布汇报必须中文。

---

## v0.6.2 — 2026-07-10: 三层架构收敛

**核心变更**：把内容创作流从“多 Agent 默认接力”收敛为“主 Agent 统筹 + Skill SOP + 工具/数据源执行”的三层架构。

### 变更内容

- README 新增三层架构说明，明确主 Agent、Skill、工具/数据源的职责边界。
- `article-pipeline/SKILL.md` 顶部新增强制架构规则，运行时不再默认把每个阶段都派成独立 Agent。
- 重写 `article-pipeline/references/main-agent-prompt.md` 为 v4 三层收敛版：主 Agent 对搜索、整理、修复、发布和失败回退负责。
- `references/data-flow.md` 增加三层视角，明确子 Agent 只在多候选筛选、质量审查、多方案并行时作为独立视角介入。
- 保留历史 prompt 调优资料，但标注运行时以三层架构为准。

---

## v0.6.1 — 2026-07-10: README 命名与使用说明重写

**核心变更**：重写仓库首页文案，把说明书式 README 改成更贴近内容创作方法论的结构。

### 变更内容

- 仓库标题从泛化的「内容创作流水线」改为「会自己找选题的内容流水线」。
- 第一屏改为痛点导入：不从模块解释开始，而是先回答「为什么需要这套流程」。
- 使用说明按内容生产真实路径重排：抓素材 → 筛选题 → 选角度 → 写作 → 质检 → 小红书适配 → 飞书沉淀。
- 强化产品体验选题池的价值表达：不只给标题，还要给原文链接、短摘、二创切入和分数。
- 增加真实输出示例，说明如何从什么值得买文章转成小红书选题。

---

## v0.6.0 — 2026-07-09: 产品体验选题池 + 什么值得买二创流 + 飞书 Base 增补

**核心变更**：在热点抓取之外新增「产品体验线」，把什么值得买等平台上的体验、开箱、横评、吐槽、新品内容沉淀为小红书二创候选池，并支持每日增补到飞书多维表格。

### 新增能力

- `daily-hot-mcp/tools/product_experience.py`
  - 新增 MCP 工具 `search-product-experience-posts`
  - 主源：什么值得买原创/文章
  - 补充源：少数派、Chiphell
  - 返回原文链接、内容短摘、内容类型、互动数据、`creative_score` 和 `score_breakdown`
- `sourcing-hotspots/scripts/smzdm_product_topics.py`
  - 按默认产品词池抓取什么值得买体验类内容
  - 输出 Markdown 报告、items JSON、Base 批量写入 JSON
  - 支持按原文链接分页去重后增补/更新飞书 Base
- `sourcing-hotspots/references/lark_base_schema.json`
  - 飞书多维表格字段 schema：标题、原文链接、关键词、组别、内容类型、单篇分、关键词稳定分、互动数据、内容定位、二创切入、状态等
- `sourcing-hotspots/scripts/create_lark_base.sh`
  - 一键创建「Hermes 产品体验选题池」Base
- `sourcing-hotspots/scripts/install_daily_smzdm_topics_launchd.sh`
  - 安装 macOS launchd 每日刷新任务

### 流程变化

- `sourcing-hotspots` 现在并行输出：
  - `/tmp/article-pipeline/01-hotspots-raw.md`：热点线
  - `/tmp/article-pipeline/01b-product-experience.md`：产品体验线
- `article-pipeline` 将产品体验线作为「产品二创候选」进入筛选阶段，不再混入热点榜。
- 默认产品词不再靠泛词猜测，而是基于什么值得买类目热度和实跑效果收敛：
  - 电脑数码：`NAS`、`耳机`、`键盘`、`路由器`、`显卡`、`显示器`、`手机`、`充电器`、`游戏本`
  - 生活电器：`洗地机`、`咖啡机`、`扫地机器人`、`空气净化器`、`空调`、`冰箱`
  - 家居/办公/车载：`浴霸`、`投影仪`、`3D打印机`、`车载冰箱`、`智能门锁`

### 打分修正

- `creative_score` 不使用阅读量；当前接口未稳定提供阅读量。
- 单篇分由关键词命中、来源、内容类型、互动、近期性、具体型号组成。
- 互动分从「可压倒排序」调整为「辅助加分」，避免单篇异常互动把小样本品类顶到第一。
- 新增「关键词稳定分」：前 5 条平均单篇分 + 有效条数加成，用于判断品类是否稳定产出可二创素材。

### 验证结果

- 成功创建飞书 Base「Hermes 产品体验选题池」。
- 写入 81 条什么值得买产品体验候选，原文链接去重后 0 重复。
- 每日刷新任务安装为 `ai.hermes.smzdm-product-topics`，默认每天 09:20 运行。

---

## v0.5.0 — 2026-06-27: v0.5.0: 流水线清理+迁移完成 — Agent prompt全部迁入references/，content-engine归档，新增6个skill同步（framing-article/writing-draft/polishing-writing/publishing-doc/khazix-style/xhs-product-recommendation），路径修复

### 变更文件
-  angle-selection/SKILL.md                         |  95 ++----------------
-  article-pipeline/SKILL.md                        |   2 +-
-  article-pipeline/references/github-versioning.md |  63 +++++++-----
-  screening-topics/SKILL.md                        | 120 +++--------------------
-  sourcing-hotspots/SKILL.md                       |   2 +-
-  5 files changed, 61 insertions(+), 221 deletions(-)

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

> 历史记录：该架构已在 v0.6.2 收敛为三层架构，以下内容只作为当时版本的设计记录，不再作为运行时默认规则。

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
- 当时版本将主 Agent 设计为纯调度；该原则已在 v0.6.2 被“三层架构”取代
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
