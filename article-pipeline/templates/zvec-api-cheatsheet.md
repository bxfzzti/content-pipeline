# zvec API 熬坑速查

## Doc 构造
```python
# ❌ kwargs 方式
zvec.Doc(id="d1", text="hello", type="topic")
# ✅ fields dict
zvec.Doc(id="d1", fields={"text": "hello", "type": "topic"})
```

## Collection 打开
```python
# ❌ 重复 create_and_open → ValueError
# ✅ 先 open，失败再 create_and_open
try:
    coll = zvec.open(path=path)
except:
    coll = zvec.create_and_open(path=path, schema=schema)
```

## 查询结果
```python
# ❌ results[0]["text"]
# ✅ results[0].fields.get("text", "")
```

## Query API
```python
# ❌ zvec.VectorQuery（已废弃）
# ✅ zvec.Query("embedding", vector=qvec)
```
