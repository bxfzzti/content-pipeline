# Harness Engineering 方法论应用于内容生产流水线

来源：https://movez.substack.com/p/harness-engineering-with-claude-14

## 三层架构

| 层 | 定义 | 当前状态 | 改进方向 |
|---|---|---|---|
| **Harness**（驾驭层） | 单个Agent的运行环境——模型、工具、权限、上下文 | SKILL.md 5000+字，混合配置/流程/教训 | 瘦身到<1500字，教训移到lessons.md |
| **Loop**（循环层） | Harness + 定时器 + 自动派生子Agent | 全靠手动触发 | 加cronjob每天自动抓热点+筛选推送 |
| **System**（自进化） | Loop + 可累积的记忆 | 教训散落在SKILL.md的⚠️里 | 结构化pipeline-memory/STATE.md |

## 5个具体改进（2026-06-18分析）

### 1. SKILL.md瘦身
- 当前：sourcing-hotspots SKILL.md有40+条⚠️ pitfall notes，占70%篇幅
- 改进：SKILL.md只保留执行步骤，⚠️教训移到lessons.md，调优记录移到filter-tuning-history.md
- 目标：从5000字→1500字

### 2. 加确定性Hooks
- 当前：质检靠LLM判断，没有硬拦截
- 改进：加PrePublish hook，检查质检报告是否存在且通过
- 原则："hooks用于must-have/never-have，不是判断题"

### 3. 结构化记忆
- 当前：教训以⚠️形式散落在各SKILL.md
- 改进：创建pipeline-memory/STATE.md，记录已验证事实、效果追踪、最近5条教训
- 每次流水线跑完自动更新，下次运行时读取

### 4. 加Loop
- 当前：热点抓取全靠手动触发
- 改进：用cronjob每天早9点自动跑热点抓取→筛选Agent→推送3个S/A级选题到飞书

### 5. 加Reviewer Subagent
- 当前：质检Agent和写作Agent共享上下文
- 改进：质检Agent完全隔离，不传入写作Agent的中间过程，只传入最终正文+事实材料

## 核心洞察

> "一个好的Loop搭配一个烂的Harness，会规模化地产出垃圾。Harness是那个不性感但决定性的层。"

应用到内容生产：
- SKILL.md是Harness（静态配置）
- 流水线执行是Loop（定时触发）
- 教训积累是System（自进化）

当前最大的问题是Harness太重（SKILL.md太长）和System缺失（教训没有结构化积累）。
