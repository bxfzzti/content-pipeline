# Linkly Local Search Prerequisite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正 Linkly 本地检索前置条件和失败判断，使仓库规则、Hermes 本地规则与 Desktop 实际行为一致。

**Architecture:** 保持 Linkly 在三层内容创作流中的职责不变，只修正接入检查。用监听文件夹提供本地索引，用可选知识库组织主题资料，用真实 MCP `search` 区分“可用但未命中”和“连接故障”。

**Tech Stack:** Markdown Skill、Linkly AI Desktop v0.8.0、Streamable HTTP MCP `http://127.0.0.1:60606/mcp`、Git/GitHub CLI。

## Global Constraints

- HTTP MCP 是主接入方式，CLI 只用于诊断和本地调试。
- Linkly AI Desktop 必须运行。
- “设置 -> 文件夹”至少添加一个监听目录；知识库不是本地检索前置条件。
- 暂不启用 Remote Tunnel。
- Linkly 不参与外部热点抓取，也不替代 zvec。

---

### Task 1: 修正仓库说明和 Agent 判断

**Files:**
- Modify: `README.md`
- Modify: `article-pipeline/SKILL.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: Linkly Desktop 的监听文件夹、可选知识库和 HTTP MCP `search`。
- Produces: 一套不依赖 `list_libraries` 非空状态的可用性判断规则。

- [x] **Step 1: 修正 README 前置条件**

把必需条件写成“Desktop 运行且设置了监听文件夹”，把知识库说明为可选组织层。

- [x] **Step 2: 修正 Skill 检查顺序**

按“确认 MCP -> 执行 search -> 命中则 outline/read -> 空结果则降级”的顺序执行；不得用 `list_libraries` 空列表判定故障。

- [x] **Step 3: 记录变更**

在 CHANGELOG 新增版本条目，并纠正 v0.6.7 中错误的前置条件描述。

- [x] **Step 4: 静态检查**

Run: `rg -n "Settings.*Libraries|没有配置资料库|list_libraries.*故障" README.md article-pipeline/SKILL.md CHANGELOG.md`

Expected: 不再出现把知识库当作本地检索必需条件的表述。

### Task 2: 同步 Hermes 本地规则

**Files:**
- Modify: `/Users/xxqq/.hermes/skills/pipeline-article/SKILL.md`

**Interfaces:**
- Consumes: Task 1 的检查顺序和失败分类。
- Produces: Hermes 运行时采用相同 Linkly 判断规则。

- [x] **Step 1: 创建可直接恢复的备份**

Run: `mkdir -p /Users/xxqq/.hermes/backups/linkly-folder-prerequisite-20260716_225449 && cp -a /Users/xxqq/.hermes/skills/pipeline-article /Users/xxqq/.hermes/backups/linkly-folder-prerequisite-20260716_225449/`

Expected: 备份目录存在且包含 `SKILL.md`。

- [x] **Step 2: 同步规则**

修改 Hermes Skill 中的前置条件、检查顺序和降级说明，使其与仓库 Skill 一致。

- [x] **Step 3: 对比检查**

Run: `rg -n "监听文件夹|知识库|list_libraries|真实.*search" /Users/xxqq/.hermes/skills/pipeline-article/SKILL.md`

Expected: 同时说明监听文件夹必需、知识库可选、真实搜索决定是否命中。

### Task 3: 真实回归并发布

**Files:**
- Verify: `/Users/xxqq/content-pipeline/README.md`
- Verify: `/Users/xxqq/content-pipeline/article-pipeline/SKILL.md`
- Verify: `/Users/xxqq/.hermes/skills/pipeline-article/SKILL.md`

**Interfaces:**
- Consumes: Task 1 和 Task 2 的统一规则。
- Produces: 可复现的 HTTP MCP 检索证据和 GitHub 版本。

- [x] **Step 1: 检查 MCP 和索引**

Run: `linkly doctor`

Expected: Server、App、Version、MCP 全部 `[ok]`。

- [x] **Step 2: 执行真实检索和读取**

通过 HTTP MCP 搜索“产品体验 新品 开箱 横评 吐槽 什么值得买”，再对长文档执行 `outline` 和 `read`。

Expected: 命中 `/Users/xxqq/content-pipeline` 内文档并读出产品体验规则。

- [x] **Step 3: 检查仓库差异**

Run: `git diff --check && git status --short`

Expected: 无空白错误，只有本次计划内文件变更。

- [x] **Step 4: 提交和发布**

Run: `git add README.md CHANGELOG.md article-pipeline/SKILL.md docs/superpowers/plans/2026-07-16-linkly-local-search-prerequisite.md && git commit -m "v0.6.8 fix Linkly local search prerequisites" && git tag v0.6.8 && git push origin main && git push origin v0.6.8`

Expected: `origin/main` 指向 v0.6.8 提交，GitHub Release 可访问。
