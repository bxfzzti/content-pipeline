---
name: article-pipeline
description: >
  文章生产流水线总入口。统一编排：热点抓取→选题筛选→角度选择→定调→写正文→质检→发布。
  同时承载路由规则、硬约束、风格路径选择。
  Triggers — "跑流程", "一条龙", "写文章", "从热点开始写", "pipeline", "全流程",
  "抓热点", "筛选题", "选角度", "定调", "写正文", "质检", "发布"
---

# article-pipeline — 内容创作流总入口

> 所有内容创作请求都从这里进。plan-first 原则贯穿始终。

---

## 流水线全景

**完整路径：热点 → 选题 → 角度（含KOL）→ 标题先行 → 拆论点 → 找支柱 → 定调 → 写正文 → 质检 → 修复 → 发布**

```
Step 1: 抓热点          sourcing-hotspots（skill）
         │ 输出：01-hotspots-raw.md
         │ 并行输出：01b-product-experience.md（产品体验/开箱/吐槽/横评候选池）
         ▼
Step 1.2: 数据质量评估   热点数据Agent（references/hotspot-agent-prompt.md）
         │ 自动去重、纠正分类、标注情绪强度
         │ ⚠️ 两层输出：第一层"全网热点"（社会/国际/财经/文娱/体育）+ 第二层"关注领域热点"（汽车/3C/AI/家居）
         │ 输出：结构化热点数据（按两层组织）
         ▼
Step 1.5: 筛选选题      筛选Agent（references/screening-agent-prompt.md）
         │ ⚠️ 两层筛选：先筛全网热点（按全网热度）→ 再筛关注领域热点
         │ 评分50分制：全网热度×2 + 时效性×2 + 讨论热度×2 + 情绪强度×2 + 内容关联度×2
         │ 输出：3-5个选题推荐（热度评分+切入方向+反面理由）
         │ ⏸ 用户确认选题
         ▼
Step 2: 选角度          angle-selection（skill，含KOL微博48-72h观点采集）
         │ 输出：03-angle.md
         │ ⏸ 用户确认角度
         ▼
Step 3: 结构设计        结构Agent（references/structure-agent-prompt.md）
         │ 输出：2-3种结构方案（框架+钩子+逻辑链）
         ▼
Step 4: 定调            framing-article（skill，标题先行）
         │ 输出：04-article-plan.md（标题+核心论点+支柱+论点大纲）
         │ ⏸ 用户确认plan
         ▼
Step 4.5: 骨架质检      质检Agent（references/quality-agent-prompt.md，只检查骨架）
         │ ❌ 不过 → 回退Step 4
         ▼
Step 5: 写正文          写作Agent（references/writing-agent-prompt.md）
         │ ⚠️ 事实补充驱动：先搜索事实，再动笔
         │ 输出：05-article-draft.md
         ▼
Step 5.5: 正文质检      质检Agent（references/quality-agent-prompt.md）
         │ ❌ 致命/严重 → 进入Step 6
         ▼
Step 6: 发布质检        质检Agent（L0-L5全面检查）
         │ 输出：质检报告（严重程度量化+修复建议+删减建议）
         │ ❌ 致命/严重 → 进入Step 6.5
         │ ⏸ 用户确认发布
         ▼
Step 6.5: 修复          修复Agent（references/fix-agent-prompt.md）
         │ 按严重程度排序修复
         │ 输出：修复报告+修复后的文章
         │ 修复后 → 回到Step 6重新质检（最多3轮）
         ▼
Step 7: 发布            发布Agent（references/publishing-agent-prompt.md）
         │ 发布到飞书 + 附备选标题
         │ 输出：飞书链接
         ▼
Step 8: 知识回写        存入 zvec 知识库（自动）
         │ 选题→topics库、角度→angles库、文章→style_anchors库
         │ 形成知识积累正循环
```

### 产品体验二创支线（2026-07-09）

`sourcing-hotspots` 现在同时拉两类上游输入：

1. **热点线**：平台热榜/RSS/hot-aggregator，输出 `/tmp/article-pipeline/01-hotspots-raw.md`。
2. **产品体验线**：`search-product-experience-posts`，按什么值得买为主、少数派/Chiphell 为补充，输出 `/tmp/article-pipeline/01b-product-experience.md`。

产品体验线用于发现科技类和生活类产品的体验、开箱、横评、吐槽、新品和避坑内容。筛选阶段不要把它混进热点榜；应作为「产品二创候选」单独评分，再和热点选题并列推荐。

默认输出必须保留原文链接、短摘录、`creative_score`、分数明细和二创切入。若写入飞书多维表格，使用 `sourcing-hotspots/scripts/smzdm_product_topics.py` 按原文链接去重增补。

阶段产物契约见 `references/data-flow.md`。

## zvec 知识库集成（2026-06-22）

本地向量搜索库，为流水线提供**选题去重、角度库、风格检查、竞品检索**能力。

**基础设施：**
- 知识库路径：`~/.hermes/zvec_content_kb`
- CLI 入口：`~/.hermes/zvec-content-poc.py`
- Python 环境：`/tmp/zvec-poc/bin/python`（需要 Python 3.10+，系统自带 3.9.6 不够）
- Embedding 模型：`shibing624/text2vec-base-chinese`（首次加载自动下载）
- 4 个 collection：`topics`（选题去重）、`angles`（角度库）、`competitors`（竞品内容）、`style_anchors`（风格锚点）

**接入点：**

| 流水线阶段 | zvec 操作 | 命令 |
|-----------|----------|------|
| Step 1.5 筛选前 | 选题去重 | `dedup "<标题>" 0.65` |
| Step 2 选角度前 | 搜历史角度 | `search_angles "<关键词>" 5` |
| Step 5.5 质检前 | 风格检查 | `check_style "<文章前500字>"` |
| Step 2 确认选题后 | 存入选题 | `add_topic "<id>" "<标题>" "<来源>"` |
| Step 3 确认角度后 | 存入角度 | `add_angle "<id>" "<描述>" "<选题>" <分数>` |
| Step 8 发布后 | 存入风格锚点 | `add_style "<id>" "<文章>" good` |

**知识积累闭环：** 每次流水线跑完，文章自动变成下一次的风格参考和选题去重依据。跑得越多，库越厚，质量越稳。

**CLI 命令速查：**
```bash
ZVEC="/tmp/zvec-poc/bin/python /Users/xxqq/.hermes/zvec-content-poc.py"
$ZVEC add_topic "<id>" "<text>" "[source]"
$ZVEC add_angle "<id>" "<text>" "<topic>" "[score]"
$ZVEC add_competitor "<id>" "<text>" "<author>" "[platform]"
$ZVEC add_style "<id>" "<text>" "[good|bad]"
$ZVEC dedup "<query>" "[threshold]"
$ZVEC search_angles "<query>" "[topk]"
$ZVEC search_competitor "<query>" "[topk]"
$ZVEC check_style "<draft_text>" "[topk]"
```

详见 `references/zvec-knowledge-base.md`。

**API 熬坑速查：** `templates/zvec-api-cheatsheet.md` — Doc 构造、Collection 打开、查询结果访问、Query API 的正确写法。

**集成指南：** `references/zvec-integration.md` — 环境配置、CLI 命令、4 个 collection、流水线接入点、API 坑。

**版本管理：** `references/github-versioning.md` — GitHub 仓库、发布流程、版本命名规则。仓库：https://github.com/bxfzzti/content-pipeline。自动发布脚本：`~/.hermes/scripts/publish-pipeline.sh "变更说明" [major|minor|patch]`

## zvec 知识库接入点

| Agent | Step | 操作 |
|-------|------|------|
| screening-agent | 1.5 | `dedup` 选题去重（阈值 0.65） |
| angle-selection | 0 | `search_angles` 搜历史角度 |
| quality-agent | 0.5 | `check_style` 风格相似度 |
| main-agent | 2/3 | `add_topic` / `add_angle` 存库 |
| main-agent | 8 | `add_style` 发布后回写风格锚点 |

## 质检 Agent Prompt 模板

三个质检 agent 共用同一份「零跑文章6条教训」检查清单，但各自检查不同阶段的产物。

### 共用检查清单（传入每个 agent 的 context）

```
你是一个内容质检 agent。以下是必须遵守的6条硬性检查：

1. 核心论点必须能一句话说清
   - 如果你说不清这篇文章到底想说什么 → ❌ 不过
   - 如果核心论点可以用在任何一篇类似文章上 → ❌ 不过（太泛）

2. 必须有支柱性类比/参照物
   - 支柱 = 能撑住整篇文章、能串3+论据的那个参照物（如丰田之于零跑）
   - 如果找不到支柱 → ❌ 不过

3. 标题必须先行，且标题 = 核心论点的浓缩
   - 标题不是写完正文再补的
   - 标题的方向由选题类型决定（反差型/共鸣型/清单型/悬念型/紧迫型）

4. 每个论点必须有具体数据或场景
   - ❌「蔚来的体系能力很强」→ 空泛
   - ✅「蔚来换电站超过4000座，从北京到上海高速每隔100多公里一座」→ 具体
   - 如果有空泛论点 → ❌ 不过

5. 论点必须围绕核心论点展开
   - 如果一个论点删掉不影响核心论点的成立 → 它不该出现
   - 如果论点之间是「并列罗列」而不是「层层递进」→ ⚠️ 警告

6. 没有调研就没有发言权
   - 事实类信息（价格、数据、事件）必须有出处
   - 如果凭空编了一个标题方向（如「李斌预警」但李斌实际说的是另一回事）→ ❌ 不过
```

### Agent A：Step 3.5 核心论点质检

```
输入：标题候选 + 核心论点 + 支柱类比 + 角度说明
检查清单：第1条（核心论点能一句话说清？）、第2条（有支柱？）、第3条（标题先行？）、第6条（调研过事实？）
输出：通过/不通过 + 具体问题
```

### Agent B：Step 4.5 骨架质检

```
输入：文章骨架（论点列表 + 每个论点的关键素材 + 定调）
检查清单：第4条（每个论点有数据/场景？）、第5条（论点围绕核心论点？）、第2条（支柱贯穿全文？）
输出：通过/不通过 + 具体问题
```

### Agent C：Step 5.5/6 正文质检（质检Agent Prompt v3）

完整prompt见 `references/quality-agent-prompt.md`。

核心能力：
- L0 结构对照（对照结构Agent输出）
- L1 硬性规则（禁用词、设问句、反模式、事实核查、禁用标点）
- L2 风格一致性（标题、开头、节奏、口语化、结尾）
- L3 内容质量（观点支撑、支柱类比、数据密度、信息来源多样性）
- L4 活人感终审
- L5 平台适配（小红书300-800字/公众号1500-3000字/抖音200-500字）
- 读者体验模拟 + 删减建议 + 严重程度量化（致命/严重/中等/轻微）
- 最多迭代3轮，连续2轮无新增问题停止

执行方式：
```python
delegate_task(goal="正文质检", context="正文+事实材料+结构Agent输出+平台要求+质检Agent prompt", toolsets=["file", "web"])
```

实测验证（2026-06-17 沃齐尼亚文章）：质检Agent用9次web_search验证了15个数据点，成功发现2处致命事实错误（"梅西最后一届世界杯"错误、越位球时间线错误）。

⚠️ **质检不过必须重检**。致命/严重问题 → 退回修改 → 重检。不能跳过。

### 执行方式

```python
# Step 3.5
delegate_task(goal="核心论点质检", context="标题+论点+支柱+6条检查清单", toolsets=["search"])

# Step 4.5
delegate_task(goal="骨架质检", context="论点列表+素材+定调+6条检查清单", toolsets=["search"])

# Step 5.5
delegate_task(goal="正文质检", context="完整正文+6条检查清单+模板词表", toolsets=["file"])
```
中间产物全部存 `/tmp/article-pipeline/`，下游自动读取，不依赖聊天上下文。

**从热点到文章的典型路径（以零跑8万辆为例）：**
```
月初销量数据（零跑8万辆、理想4万辆）→ 筛选题（零跑破纪录最有故事）→ 选角度（用丰田类比）→ 定标题（「8万辆之后，零跑不再是新势力」）→ 拆论点（零跑在做丰田做过的事）→ 找支柱（丰田精益生产）→ 定调 → 写正文 → 质检 → 发布
```
中间产物全部存 `/tmp/article-pipeline/`，下游自动读取，不依赖聊天上下文。

---

## 风格路径选择

| 路径 | 触发词 | 加载skill | 适用 |
|------|--------|----------|------|
| **卡兹克**（建筑式结构） | 默认 | `khazix-style` | 日常内容、行业判断、热点评论、商单——默认用这个 |
| **角色卡**（观察者型行业老兵） | 「用角色卡」「口语化风格」 | `writing-style` | 用户明确要求时才用 |

**铁律：Step 5 之前必须确定风格路径。** 用户没指定 → 默认卡兹克。用户说「用角色卡」→ 角色卡。不能写到一半换风格。

---

## 路由表：用户说什么 → 加载什么

| 用户说 | 加载skill | 备注 |
|--------|----------|------|
| 跑流程 / 一条龙 / 写一篇文章 | 本skill，全自动执行Step 1→7 | 跳过确认直接跑完 |
| 抓热点 / 今天有什么热点 | `sourcing-hotspots`（只抓不选） | |
| 筛选题 / 你觉得该写哪个 | `screening-topics`（必须加载SKILL执行） | 禁止凭记忆判断 |
| 选角度 / 从哪个角度写 | `angle-selection` | 定调前必经 |
| 定调 / 写作思路 | `framing-article` | 已有方向时先定调再写 |
| 写正文 / 动笔 / 展开 | `writing-draft` | 需已有plan输入 |
| 质检 / 自检 / 润色 | `polishing-writing` | 只检查不修改 |
| 发布 / 创建文档 | `publishing-doc` | 只排版发布 |
| 查微博账号怎么说 | `weibo-topic-signal` | 只做观点参考，不当热点源 |
| 好物推荐 / 种草文 | `xhs-product-recommendation` | 独立流水线 |
| 小红书优化 / 标题 / 封面 | `xhs-adapter` | 正文写完后优化 |
| 复盘 / 总结教训 | `growing-from-mistakes` | 独立于流水线 |

---

## 硬约束（不可绕过）

### 0. 任何文章都不能跳过选题审查和角度选择（2026-06-18 教训）

用户说"写个小红书""写一下""找个角度写"——**不是跳过流水线的许可，是触发流水线的指令。**

即使是"看起来很明确"的选题（如"写iPhone涨价"），也必须：
1. 跑 screening-topics 五问审查（确认事实层、争议空间、趋势关联）
2. 跑 angle-selection 三轴角度选择（痛点轴/误解轴/方法轴）
3. 然后才进入定调→写作

**用户两次被抓到跳过流程：**
- 第一次：比亚迪大唐+理想纯电，直接写没走审查。用户没说但效果一般。
- 第二次：iPhone涨价，直接写+直接找角度。用户明确指出"你没有走选题 定调 agent"。

**原因：** 跳过审查和角度选择，写出来的角度往往是"分析师视角"（中性描述、缺少立场），而不是"有态度的观察者视角"（有冲突感、有判断）。审查和角度选择的价值不只是"走流程"，而是通过子agent的多视角碰撞找到更犀利的切入点。

**自检：** 用户要求写一篇文章时，问自己"我跑了screening-topics和angle-selection吗？"如果没有，先跑。

### 1. 热点抓取必须多平台 + 多品类

每次抓热点必须包含三类源：
1. **主流热榜**（≥3个）：微博/知乎/抖音/头条
2. **垂直科技源**（≥4个）：ithome/geekpark/ifanr/huxiu + 微信文章 + B站热榜 + 知乎板块搜索
3. **小红书搜索**（≥5个关键词，每品类至少1个）

**⚠️ 热点必须分两层输出（2026-06-17 修正）：**
- **第一层：全网热点**（不限方向）— 社会/民生、国际、财经/政策、文娱/体育、其他爆点
- **第二层：关注领域热点** — 汽车、3C、AI、家居

不能只输出关注领域热点。全网热点先按热度排序，再看关注领域。这样既能捕捉"大话题"（如高考、中东局势），也能保留"精准话题"（如华为智驾）。

跨日去重：当天与前一天推荐选题重复率 > 50% → 换源、换关键词。

### 2. 品类差异化 Q5 校验

| 品类 | Q5标准 | 要求 |
|------|--------|------|
| 🚗 汽车 | 严格消费决策 | 买/不买/等 |
| 💻 数码 | 中等消费决策 | 值不值得买/关注 |
| 🏠 家居 | 中等消费决策 | 值不值得买/怎么选 |
| 📡 科技热点 | 社交货币 | 读完有谈资、想转发 |
| 🤖 AI/机器人 | 认知升级 | 知道一个新趋势 |

### 3. 事件独立捕获

标题命中以下事件词 → 自动捕获为汽车候选，不依赖品牌词命中：
`首秀 / 首发 / 亮相 / 预售 / 新车发布 / 正式上市`

### 4. 微博灵感账号规则

**定位：** 用户关注的微博账号（奶爸兄地、一苒、小特叔叔等）是KOL观点来源，只做定调/角度/争议点参考。

**允许：** 用户明确要求「看看这些账号怎么说」；已确定候选选题后补充KOL观点；定调阶段需要争议点。

**禁止：** 用户只说「抓热点」时默认运行；把个人账号当热点源/事实源；因账号发过相关内容就自动给选题+1级。

### 5. 质检不过必须重检

🔴 硬伤 → 退回修改 → 重检。不能跳过。

### 6. 发布后附标题备选

文档末尾用 `---` 分隔，标题 `## 小红书标题备选`，5个方向（冲突型🔥/反常识型🤔/解决方案型💡/参数型✂️/短爆型📱）各2个标题。

---

## 用户交互点

4个暂停点等待用户确认：
1. **Step 2→3**：选题确认
2. **Step 3→4**：角度确认
3. **Step 4→5**：plan确认
4. **Step 6→7**：质检通过确认

用户说「直接跑」时跳过确认，全自动执行到质检。

**⚠️ 全自动模式必须生成标题备选（2026-06-15 教训）：** 全自动跑完7步后，必须在 Step 7 发布前生成 5方向×2标题的备选列表，附在文档末尾。实测中跳过了这一步，导致文档缺少标题备选。

**⚠️ weibo-topic-signal 超时处理：** 超时30秒即跳过，不阻塞主流程。在最终汇报中标注「KOL微博：⚠️ 超时跳过」。不能因为微博超时就反复重试或卡住。

---

## 一键启动规则

用户说「跑流程」「一条龙」「跑一次流程」时：
1. 自动执行 Step 1（热点抓取）
2. **⚠️ 必须走热点数据Agent（Step 1.2）和筛选Agent（Step 1.5）** — 不能只跑filter脚本就跳到下一步。2026-06-18教训：用户两次指出"抓热点没有走Agent"和"没有走选题定调agent"。filter脚本是数据预处理，Agent才是质量评估和选题判断。
3. **自动选最佳选题，直接进入角度→质检→定调→质检→写作→质检→发布**
4. 每一步质检用 delegate_task 派独立 agent，把零跑文章6条教训作为检查清单
5. 质检不过→回退上一步重做，不跳过
6. 全程完成后汇报：飞书链接 + 核心论点 + 备选标题

---

## 商单特殊路径

用户提供品牌brief时，跳过 Step 1-2，直接：
1. 分析brief中的合规红线 + 必须包含的信息
2. Step 3：用「体验化」视角选角度（不是播报员视角）
3. Step 4→5→6→7

详见 `references/xhs-commercial-content-style.md`。

---

## 多方向并行测试模式

当用户说「这个话题值得写」时：
1. 出3-5个完全不同方向（认知颠覆/观点输出/趋势洞察/选购决策/体验种草）
2. `delegate_task` 并行写
3. 批量发布到飞书
4. 观察哪个方向效果好，下次复制

---

## 批量写作模式

多篇并行用 `delegate_task`，每篇存 `/tmp/article-pipeline/batch-NN-title.md`，写完循环发布。

子agent prompt必须反复强调字数要求（2500-3000中文字），写完验证字数。

---

## 子agent网络问题

子agent的 `web_extract` 可能被限制。回退方案：
1. 先尝试子agent并行搜索
2. 全部失败 → 主agent直接搜，每轮2-3个不同关键词
3. 搜3-4轮后提取关键URL → 主agent用 `web_extract` 抓正文
4. 不要等子agent超时太久

---

## 创作心法

### 小爆品：快速迭代
先做10个不同方向 → 找最好的复制10个版本 → 再找最好的复制 → 如此往复。重点是「快速迭代」。

### 大爆品：持续更新等运气
持续稳定更新 + 迭代 + 活足够长时间。大爆品基本纯看运气，能做的就是活久一点。

### 商单=内容
把商单当内容做（创意比brief好），把内容当商单做（信息准确公正）。不区分，都以好内容为标准。

---

## 方法论来源

- **Compound Engineering**（Matt Van Horn）：plan-first、中间产物存档、并行不等待
- **得到品控手册11.0**：认知交付五要素、启动动机四心法、品控网络化

详见 `references/dedao-content-methodology.md`。

---

## 多Agent协同工作流（2026-06-17）

单个Agent的逻辑天然比较直来直去——接到任务→搜索→写，链路上没有"质疑"环节。需要多个Agent在关键节点提出质疑、反问、补充新观点。

### 三个协同Agent

| Agent | 职责 | 何时介入 | Prompt位置 |
|-------|------|---------|-----------|
| **热点数据Agent** | 数据质量评估、去重、纠正分类、标注情绪强度、两层输出（全网热点+关注领域热点） | Step 1→1.2之间 | `references/hotspot-agent-prompt.md` |
| **筛选Agent** | 两层筛选（先全网后领域）、50分制评分（含全网热度维度）、切入方向分析 | Step 1.2→1.5之间 | `references/screening-agent-prompt.md` |
| **结构Agent** | 搜完事实后，提出2-3种文章结构方案 | Step 2→3之间 | `references/structure-agent-prompt.md` |
| **写作Agent** | 搜索事实+写正文 | Step 4→5之间 | `references/writing-agent-prompt.md` |
| **质检Agent** | 检查事实/风格/逻辑 | Step 4.5/5.5/6 | `references/quality-agent-prompt.md` |
| **修复Agent** | 按质检报告修复 | Step 6→6.5之间 | `references/fix-agent-prompt.md` |
| **发布Agent** | 发布到飞书+附备选标题 | Step 6.5→7之间 | `references/publishing-agent-prompt.md` |

**⚠️ Prompt设计核心原则**：约束必须加负面示例（"不能用XX，如XX"），正面约束Agent不一定遵守。详见 `references/multi-agent-prompt-design.md`。

### 协同流程

```
热点数据 → 热点数据Agent（质量评估+去重+纠正分类）
                ↓
         主Agent组装信息
                ↓
         筛选Agent（选什么、从哪切入）
                ↓
         主Agent确认选题
                ↓
         结构Agent（怎么组织）
                ↓
         主Agent定调
                ↓
         写作Agent（搜索事实+写正文）
                ↓
         质检Agent（写得对不对、好不好）
                ↓
         修复Agent（按质检报告修复）
                ↓
         质检Agent（最终确认，最多3轮）
                ↓
         发布Agent（发布到飞书）
```

### 执行方式

```python
# Step 1.5：筛选Agent
delegate_task(goal="热点筛选分析", context="热点数据(按message-format.md格式)+内容定位+筛选Agent prompt", toolsets=["web"])

# Step 3.5：结构Agent
delegate_task(goal="文章结构分析", context="事实材料(按message-format.md格式)+读者已知信息+切入方向+结构Agent prompt", toolsets=["file"])

# Step 4.5/5.5/6：质检Agent（已有）
delegate_task(goal="正文质检", context="正文+6条检查清单", toolsets=["search"])
```

**⚠️ Agent间信息传递必须用标准化格式**（见 `references/message-format.md`）。主Agent负责组装信息按格式传给子Agent，子Agent按格式输出。信息缺失时子Agent先问，不编造。

### 关键原则

- **结构Agent和筛选Agent的prompt质量决定它们能不能提出有价值的质疑**
- 核心价值不是"多个Agent帮我写"，而是**在关键节点有人提出质疑和替代方案**
- 主Agent从多个方案中选一个，或者把不同方案的优点组合

---

## 写作方法论：事实补充驱动（2026-06-17）

**AI没有"我跟这个话题之间发生了什么"的认知流程。**

正确路径：
1. **接到选题** → 先搜索：这个事到底是个什么事？
2. **各方观点** → 谁在说？说了什么？不同角度的解读是什么？
3. **抽取信息** → 从搜索结果里挑出有价值的事实、细节、数据
4. **组织成文** → 钩子→铺垫→核心→收尾

钩子铺垫核心收尾是骨架，事实补充是肉。骨架可以设计，但肉必须从搜索里来。**搜够了再写，搜不够不动笔。**

### 写作反模式（必须避免）

- 设问引导开场（"你有没有发现""我好奇的是"）
- 设问过渡（"为什么？""他们去哪了？"）
- 虚拟对话体（"你说X5L是豪华品牌"）
- 排比式并列总结（"A输在X。B输在Y。"）
- 煽情式收尾（"这让人不禁深思"）

---

## 用户给定标题时的处理（2026-06-18 教训）

用户说「主题 XXX」或明确给出标题时：
1. **跳过 angle-selection**，直接用用户标题进入 framing-article
2. 不要重新取标题、不要问用户"要不要换个角度"
3. 仍需走 framing（定调+论点结构）→ writing → quality check → publish
4. 用户要的是"按我的标题走后续流程"，不是"帮我重新想角度"

## 参考文件

- `references/dedao-content-methodology.md` — 得到品控方法论
- `references/xhs-commercial-content-style.md` — 商单内容体验化写法
- `references/boss-content-strategy.md` — 品牌知识图谱+选题策略（原content-engine）
- `references/product-article-angles.md` — 产品文章角度库（原content-engine）
- `references/ifanr-content-analysis.md` — 爱范儿内容模式分析（原content-engine）
- `references/structure-agent-prompt.md` — 结构Agent prompt v4（决策树选框架+配套钩子+自检清单）
- `references/screening-agent-prompt.md` — 筛选Agent prompt v5（50分制评分含全网热度维度+两层筛选+动态切入方向+单维度爆点规则）
- `references/message-format.md` — 多Agent信息传递格式规范（主Agent↔子Agent的标准化输入输出格式）
- `references/quality-agent-prompt.md` — 质检Agent prompt v3（L0-L5六层检查+严重程度量化+平台适配+读者体验模拟+删减建议+迭代管理）
- `references/structure-agent-case-study.md` — 结构Agent完整案例（沃齐尼亚vs阿尔奥维斯，含输入/输出/教训）
- `references/harness-engineering-analysis.md` — Harness Engineering方法论分析（2026-06-18，5个改进方向：SKILL.md瘦身/确定性Hooks/结构化记忆/Loop自动化/Reviewer隔离）
- `references/multi-agent-prompt-design.md` — 多Agent prompt设计原则（负面示例>正面约束、8 Agent架构、信息传递格式、迭代控制）
- `references/zvec-knowledge-base.md` — zvec 本地向量知识库集成（API 熬坑、CLI 命令、阈值参考、schema 设计）
