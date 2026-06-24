# zvec 知识库集成指南

## 概述

zvec 是阿里开源的进程内向量数据库（向量搜索界的 SQLite），已集成到内容流水线中，提供"记忆"能力。

## 环境

- **Python**: `/tmp/zvec-poc/bin/python`（venv，Python 3.12）
- **CLI 入口**: `~/.hermes/zvec-content-poc.py`
- **数据目录**: `~/.hermes/zvec_content_kb/`
- **Embedding 模型**: `shibing624/text2vec-base-chinese`（768维，首次运行自动下载）
- **安装**: `uv pip install zvec sentence-transformers --python /tmp/zvec-poc/bin/python`

## 4 个 Collection

| Collection | 用途 | 接入点 |
|------------|------|--------|
| `topics` | 选题去重 | screening-agent Step 1.5 |
| `angles` | 角度库 | angle-selection Step 0 |
| `competitors` | 竞品内容库 | 手动/Agent 添加 |
| `style_anchors` | 风格锚点（good/bad） | quality-agent Step 0.5 + 发布后回写 |

## CLI 命令

```bash
PYTHON="/tmp/zvec-poc/bin/python"
KB="/Users/xxqq/.hermes/zvec-content-poc.py"

# 添加
$PYTHON $KB add_topic <id> <text> [source]
$PYTHON $KB add_angle <id> <text> <topic> [score]
$PYTHON $KB add_competitor <id> <text> <author> [platform]
$PYTHON $KB add_style <id> <text> [good|bad]

# 查询
$PYTHON $KB dedup <query> [threshold]        # 默认 0.75
$PYTHON $KB search_angles <query> [topk]      # 默认 5
$PYTHON $KB search_competitor <query> [topk]  # 默认 5
$PYTHON $KB check_style <draft_text> [topk]   # 返回 good/bad/verdict
```

## 流水线接入点

### screening-agent (Step 1.5)
```bash
/tmp/zvec-poc/bin/python ~/.hermes/zvec-content-poc.py dedup "<热点标题>" 0.65
```
- score ≥ 0.80 → "可能重复"，建议跳过
- 0.65 ≤ score < 0.80 → "相关选题"，建议差异化

### angle-selection (Step 0)
```bash
/tmp/zvec-poc/bin/python ~/.hermes/zvec-content-poc.py search_angles "<选题关键词>" 5
```
- score ≥ 0.80 → 直接复用或迭代
- 0.65 ≤ score < 0.80 → 参考避免重复

### quality-agent (Step 0.5)
```bash
/tmp/zvec-poc/bin/python ~/.hermes/zvec-content-poc.py check_style "<文章前500字>"
```
- verdict=pass → 合格
- verdict=warn → 风格偏弱
- verdict=fail → 严重偏离（更像硬广）

### main-agent (Step 2/3/8)
- 用户确认选题后 → `add_topic`
- 用户确认角度后 → `add_angle`
- 发布成功后 → `add_style` (good) + `add_topic`

## zvec API 坑

1. **Doc 初始化**: 用 `fields={}` dict 传参，不能用 kwargs
   ```python
   # ✅ 正确
   zvec.Doc(id="d1", vectors={"embedding": vec}, fields={"text": "...", "type": "..."})
   # ❌ 错误
   zvec.Doc(id="d1", vectors={...}, text="...", type="...")
   ```

2. **打开已有 collection**: 用 `zvec.open(path=...)`，不能用 `create_and_open`（会报 path exists）
   ```python
   try:
       coll = zvec.open(path=path)
   except Exception:
       coll = zvec.create_and_open(path=path, schema=schema)
   ```

3. **Query API**: 用 `zvec.Query('embedding', vector=...)` 不是 `VectorQuery`（已 deprecated）

4. **结果是 Doc 对象**: 用 `.id`, `.score`, `.fields` 属性访问，不是 dict `[]`

5. **Python 版本**: zvec 要求 Python 3.10-3.14，系统默认 3.9 不行

## GitHub 版本管理

仓库：https://github.com/bxfzzti/content-pipeline

每次流水线变更后：
1. 同步文件到 `/tmp/content-pipeline-v1/`
2. 更新 `CHANGELOG.md`
3. `git commit` + `git tag -a v<X.Y.Z>` + `git push`
