# Two-Minute Full Hotspot Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 120 秒内抓取或降级覆盖全部热点来源，默认恢复选题、角度、定调确认，并禁止内容流使用个人小红书登录态。

**Architecture:** 新增一个 Python 编排器并行执行 hot-aggregator、RSS 和产品体验抓取，为每个来源保存独立缓存和运行状态，在全局截止时间前生成统一 manifest 与阶段产物。产品脚本改为受控并发，并支持直接复用已有 JSON 同步飞书；主流程文档作为交互与安全契约，由自动测试防止规则回退。

**Tech Stack:** Python 3.12 标准库、现有 MCP Python SDK、`unittest`、Hermes/Codex Markdown Skill、macOS launchd、现有 `lark-cli`。

## Global Constraints

- 从收到“跑一次内容创作流”开始，120 秒内返回完整热点候选和来源状态。
- 所有已配置热点来源必须产生 `live`、`cache`、`unavailable` 或 `disabled` 状态，不能静默遗漏。
- 内容创作流不得调用任何个人小红书登录态工具、Cookie 或 CDP 页面。
- 默认在选题、角度、定调三个节点等待用户确认。
- 只有“直接跑完”“全自动”“不用确认”等明确指令可以跳过三个确认点。
- 同一批产品体验数据只抓取一次，本地产物与飞书同步复用同一 JSON。
- 不删除或修改用户现有的小红书 Cookie，只禁止内容创作流读取它们。

---

### Task 1: 两分钟热点来源编排器

**Files:**
- Create: `sourcing-hotspots/scripts/full_hotspot_run.py`
- Create: `tests/test_full_hotspot_run.py`

**Interfaces:**
- Consumes: hot-aggregator `GET /api/all`、公开 RSS URL、`smzdm_product_topics.py` 子进程。
- Produces: `run_pipeline(config: RunConfig) -> RunSummary`、`00-source-manifest.json`、`01-hotspots-raw.json`、`01b-product-experience.json`。

- [ ] **Step 1: 写来源状态、缓存回退和安全注册表测试**

```python
class FullHotspotRunTests(unittest.TestCase):
    def test_registry_contains_no_authenticated_xhs(self):
        names = {source.name for source in build_source_registry()}
        self.assertFalse(any("xhs" in name or "xiaohongshu" in name for name in names))

    def test_failed_source_uses_cache(self):
        result = resolve_result("rss:test", live=None, cached={"items": [1]}, error="timeout")
        self.assertEqual(result.status, "cache")
        self.assertEqual(result.data, {"items": [1]})

    def test_failed_source_without_cache_is_unavailable(self):
        result = resolve_result("rss:test", live=None, cached=None, error="timeout")
        self.assertEqual(result.status, "unavailable")
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python3 -m unittest tests.test_full_hotspot_run -v`

Expected: FAIL，提示 `full_hotspot_run` 不存在。

- [ ] **Step 3: 实现最小来源模型和缓存接口**

```python
@dataclass(frozen=True)
class SourceSpec:
    name: str
    kind: str
    url: str | None = None
    timeout_seconds: float = 10.0

@dataclass
class SourceResult:
    name: str
    status: str
    data: Any
    elapsed_ms: int
    error: str | None = None
    cache_time: str | None = None

def resolve_result(name: str, live: Any, cached: Any, error: str | None) -> SourceResult:
    if live is not None:
        return SourceResult(name, "live", live, 0, error)
    if cached is not None:
        return SourceResult(name, "cache", cached, 0, error)
    return SourceResult(name, "unavailable", None, 0, error)
```

- [ ] **Step 4: 实现并行运行和 120 秒全局截止时间**

```python
@dataclass(frozen=True)
class RunConfig:
    output_dir: Path
    cache_dir: Path
    deadline_seconds: float = 120.0
    aggregator_url: str = "http://127.0.0.1:6688/api/all"

def run_pipeline(config: RunConfig) -> RunSummary:
    deadline = time.monotonic() + config.deadline_seconds
    with ThreadPoolExecutor(max_workers=24) as pool:
        futures = {pool.submit(fetch_source, spec, deadline): spec for spec in build_source_registry()}
        results = collect_until_deadline(futures, deadline)
    return write_outputs(config, results)
```

`collect_until_deadline` 必须在截止时间到达时取消未开始任务，并为未返回来源读取缓存或生成 `unavailable`。hot-aggregator 返回后展开其中平台列表，每个平台独立写入 manifest；聚合器整体失败时从缓存展开并标记为 `cache`。

- [ ] **Step 5: 实现本地服务健康检查与按需启动**

```python
def ensure_hot_aggregator(url: str, workdir: Path, deadline: float) -> bool:
    if probe_json(url, timeout=3):
        return True
    subprocess.Popen(
        ["node", "--import", "tsx", "index.mjs"],
        cwd=workdir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return wait_until_healthy(url, deadline=min(deadline, time.monotonic() + 20))
```

不得每次 `kill -9`；只有健康检查失败时才启动。已运行服务继续复用。

- [ ] **Step 6: 运行单元测试**

Run: `python3 -m unittest tests.test_full_hotspot_run -v`

Expected: PASS，覆盖实时、缓存、不可用、安全注册表和全局截止时间。

- [ ] **Step 7: 提交编排器**

```bash
git add sourcing-hotspots/scripts/full_hotspot_run.py tests/test_full_hotspot_run.py
git commit -m "feat: add bounded full hotspot orchestrator"
```

### Task 2: 产品体验并发抓取与结果复用

**Files:**
- Modify: `sourcing-hotspots/scripts/smzdm_product_topics.py`
- Create: `tests/test_smzdm_product_topics.py`

**Interfaces:**
- Consumes: `search-product-experience-posts` MCP 工具或既有 `smzdm_product_topics_rows.json`。
- Produces: `fetch_topics(limit_per_keyword, concurrency, timeout_seconds)`；`--sync-existing` 模式不触发 MCP 抓取。

- [ ] **Step 1: 写并发和复用测试**

```python
class ProductTopicTests(unittest.IsolatedAsyncioTestCase):
    async def test_keyword_jobs_are_bounded(self):
        peak = await measure_fake_keyword_concurrency(concurrency=4)
        self.assertLessEqual(peak, 4)
        self.assertGreater(peak, 1)

    def test_sync_existing_loads_rows_without_fetch(self):
        fields, rows = load_existing_rows(self.rows_path)
        self.assertEqual(fields, FIELDS)
        self.assertEqual(len(rows), 1)
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python3 -m unittest tests.test_smzdm_product_topics -v`

Expected: FAIL，提示新接口不存在。

- [ ] **Step 3: 将 20 个关键词改为受控并发**

```python
semaphore = asyncio.Semaphore(concurrency)

async def fetch_one(group: str, keyword: str) -> KeywordResult:
    async with semaphore:
        return await asyncio.wait_for(call_keyword(group, keyword), timeout_seconds)

jobs = [fetch_one(group, keyword) for group, keywords in KEYWORDS.items() for keyword in keywords]
keyword_results = await asyncio.gather(*jobs, return_exceptions=True)
```

单关键词失败必须生成空结果和错误状态，不能取消其他关键词。

- [ ] **Step 4: 增加 `--sync-existing` 模式**

```python
parser.add_argument("--sync-existing", action="store_true")
parser.add_argument("--concurrency", type=int, default=5)
parser.add_argument("--keyword-timeout", type=float, default=12.0)

if args.sync_existing:
    fields, rows = load_existing_rows(output_dir / "smzdm_product_topics_rows.json")
    sync_to_lark(args.base_token, args.table_id, rows, Path.cwd())
    return
```

`--sync-existing` 缺少结果文件时必须退出并显示明确错误，不能回退为重新抓取。

- [ ] **Step 5: 运行产品测试和脚本帮助检查**

Run: `python3 -m unittest tests.test_smzdm_product_topics -v`

Expected: PASS。

Run: `python3 sourcing-hotspots/scripts/smzdm_product_topics.py --help`

Expected: 包含 `--sync-existing`、`--concurrency` 和 `--keyword-timeout`。

- [ ] **Step 6: 提交产品脚本改造**

```bash
git add sourcing-hotspots/scripts/smzdm_product_topics.py tests/test_smzdm_product_topics.py
git commit -m "perf: parallelize and reuse product topic runs"
```

### Task 3: 固化交互确认与小红书安全契约

**Files:**
- Modify: `article-pipeline/SKILL.md`
- Modify: `article-pipeline/references/main-agent-prompt.md`
- Modify: `sourcing-hotspots/SKILL.md`
- Modify: `sourcing-hotspots/references/hotspot-agent-prompt.md`
- Create: `tests/test_workflow_contracts.py`

**Interfaces:**
- Consumes: 用户自然语言指令。
- Produces: 默认交互路由、三个确认门、登录态小红书硬禁用规则。

- [ ] **Step 1: 写文档契约测试**

```python
class WorkflowContractTests(unittest.TestCase):
    def test_normal_run_is_interactive(self):
        text = Path("article-pipeline/SKILL.md").read_text()
        self.assertIn("跑一次流程", text)
        self.assertIn("默认交互模式", text)
        self.assertNotIn("跳过确认直接跑完", text)

    def test_authenticated_xhs_is_forbidden(self):
        text = Path("sourcing-hotspots/SKILL.md").read_text()
        self.assertIn("禁止个人小红书登录态", text)
        self.assertNotIn("每次抓热点必须包含三类源", text)
```

- [ ] **Step 2: 运行契约测试并确认失败**

Run: `python3 -m unittest tests.test_workflow_contracts -v`

Expected: FAIL，当前仍含“跳过确认直接跑完”和小红书 Cookie 抓取规则。

- [ ] **Step 3: 统一主流程路由**

把“跑流程 / 一条龙 / 写一篇文章”改为默认交互模式，明确停在：

1. 热点与选题确认。
2. 角度确认。
3. 定调与文章计划确认。

单独增加“直接跑完 / 全自动 / 不用确认”路由，且不得把普通“跑一次流程”解释为全自动。

- [ ] **Step 4: 固化小红书硬禁用**

删除热点阶段中所有要求调用 `xhs`、`xiaohongshu-mcp`、Cookie 或 CDP 登录态的规则，替换为：

```text
禁止个人小红书登录态：热点与研究阶段不得调用 xhs-cli、xiaohongshu-mcp、浏览器 Cookie、CDP 登录页或任何本地小红书 Cookie。只允许处理用户主动提供的链接、截图、导出内容，以及无需个人登录态的公开索引。
```

- [ ] **Step 5: 写入两分钟执行契约**

热点 Skill 必须指向 `full_hotspot_run.py`，明确 120 秒全局截止、来源状态输出、缓存时间标注和禁止深度研究。Linkly、zvec、网页核验、评论研究、生图全部延后到选题确认后。

- [ ] **Step 6: 运行契约测试**

Run: `python3 -m unittest tests.test_workflow_contracts -v`

Expected: PASS。

- [ ] **Step 7: 提交规则修正**

```bash
git add article-pipeline/SKILL.md article-pipeline/references/main-agent-prompt.md sourcing-hotspots/SKILL.md sourcing-hotspots/references/hotspot-agent-prompt.md tests/test_workflow_contracts.py
git commit -m "fix: restore interactive gates and block xhs login state"
```

### Task 4: 文档、本地同步与真实回归

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `/Users/xxqq/.hermes/skills/pipeline-article/SKILL.md`
- Modify: `/Users/xxqq/.hermes/skills/sourcing-hotspots/SKILL.md`
- Create: runtime files under `/tmp/article-pipeline/` only during test.

**Interfaces:**
- Consumes: Task 1 至 Task 3 的最终实现。
- Produces: 本地 Hermes 生效规则、真实耗时报告、可发布 Git 提交。

- [ ] **Step 1: 更新中文使用说明与变更记录**

README 必须说明默认交互模式、120 秒全覆盖定义、来源状态和小红书安全边界。CHANGELOG 记录性能、隐私、评分和重复抓取修复。

- [ ] **Step 2: 备份并同步 Hermes 本地 Skill**

```bash
backup="$HOME/.hermes/backups/two-minute-hotspot-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup"
cp "$HOME/.hermes/skills/pipeline-article/SKILL.md" "$backup/pipeline-article.SKILL.md"
cp "$HOME/.hermes/skills/sourcing-hotspots/SKILL.md" "$backup/sourcing-hotspots.SKILL.md"
```

随后把仓库中的两个 Skill 同步到对应 Hermes 路径。不得覆盖其他本地 Skill。

- [ ] **Step 3: 运行全部单元测试**

Run: `python3 -m unittest discover -s tests -v`

Expected: 全部 PASS。

- [ ] **Step 4: 执行真实两分钟抓取**

```bash
/Users/xxqq/.hermes/hermes-agent/.venv/bin/python \
  sourcing-hotspots/scripts/full_hotspot_run.py \
  --output-dir /tmp/article-pipeline/two-minute-run \
  --deadline-seconds 120
```

Expected: 退出码 0，总耗时不超过 120 秒，生成 manifest、热点 JSON/Markdown 和产品体验 JSON/Markdown。

- [ ] **Step 5: 验证安全和来源覆盖**

Run: `rg -n -i 'xhs|xiaohongshu|cookies/xhs|18060' /tmp/article-pipeline/two-minute-run`

Expected: 无登录态调用记录；若文档中的禁用说明未写入运行目录，则输出为空。

Run: 使用 Python 读取 manifest，断言每个来源都有合法状态，汇总实时、缓存、不可用和禁用数量，并检查 `elapsed_seconds <= 120`。

- [ ] **Step 6: 验证产品同步不会重新抓取**

用测试 Base 参数执行 `smzdm_product_topics.py --sync-existing`，同时记录 daily-hot-mcp 请求计数或运行日志，断言同步阶段没有新增 `search-product-experience-posts` 调用。

- [ ] **Step 7: 提交文档和本地同步说明**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: document two-minute interactive hotspot flow"
```

- [ ] **Step 8: 发布前检查**

Run: `git status --short --branch`

Expected: 工作树干净，分支仅包含本次设计、计划、实现和文档提交。

Run: `git log --oneline --decorate -8`

Expected: 能看到设计、计划、编排器、产品优化、规则修正和文档提交。
