# zvec 知识库集成详细文档

## 环境设置

```bash
# zvec 需要 Python 3.10+，系统自带 3.9.6 不行
uv venv /tmp/zvec-poc --python 3.12
uv pip install zvec sentence-transformers --python /tmp/zvec-poc/bin/python
```

首次运行会自动下载 embedding 模型（~90MB），之后走本地缓存。

## API 熬坑记录

### Doc 构造：fields 必须用 dict 参数

```python
# ❌ 错误：字段作为 kwargs
zvec.Doc(id="d1", vectors={"embedding": vec}, text="hello", type="topic")

# ✅ 正确：字段包在 fields dict 里
zvec.Doc(id="d1", vectors={"embedding": vec}, fields={"text": "hello", "type": "topic"})
```

### create_and_open 不能重复打开

```python
# ❌ 错误：已存在的 collection 再次 create_and_open 会报 ValueError
coll = zvec.create_and_open(path="/path/to/existing", schema=schema)

# ✅ 正确：先尝试 open，失败再 create_and_open
try:
    coll = zvec.open(path=path)
except Exception:
    coll = zvec.create_and_open(path=path, schema=schema)
```

### 查询结果是 Doc 对象，不是 dict

```python
# ❌ 错误：当 dict 用
results[0]["text"]

# ✅ 正确：用属性访问
results[0].id          # str
results[0].score       # float
results[0].fields      # dict or None
results[0].fields.get("text", "")
```

### VectorQuery 已废弃

```python
# ❌ 废弃 API
coll.query(zvec.VectorQuery("embedding", vector=qvec), topk=5)

# ✅ 新 API
coll.query(zvec.Query("embedding", vector=qvec), topk=5)
```

## 4 个 Collection Schema

所有 collection 共用同一个 schema 结构：
- `embedding`: VECTOR_FP32, 768 维
- `text`: STRING（主要内容）
- `type`: STRING（分类/标签）
- `source`: STRING（来源/作者）
- `timestamp`: STRING（ISO 时间戳）

| Collection | 用途 | type 字段含义 | source 字段含义 |
|-----------|------|-------------|---------------|
| topics | 选题去重 | 固定 "topic" | 来源平台:作者 |
| angles | 角度库 | 选题标题 | SPOV 分数 |
| competitors | 竞品内容 | "平台:作者" | 作者名 |
| style_anchors | 风格锚点 | "good" 或 "bad" | 固定 "user_feedback" |

## 阈值参考

| 场景 | 推荐阈值 | 说明 |
|------|---------|------|
| 选题去重 | 0.65 | 0.80+ 高度相似建议跳过，0.65-0.80 相关建议差异化 |
| 角度搜库 | 0.65 | 0.80+ 直接复用，0.65-0.80 作参考避免重复 |
| 风格检查 | N/A | 用 good/bad 平均分对比，verdict 判定 |

## 相关文件

- CLI 入口：`~/.hermes/zvec-content-poc.py`
- 数据目录：`~/.hermes/zvec_content_kb/`
- Python 环境：`/tmp/zvec-poc/`
