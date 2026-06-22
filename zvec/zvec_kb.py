#!/usr/bin/env python3
"""
zvec 知识库集成模块
供内容流水线各 Agent 调用
"""
import zvec
import os
import json
import sys
from datetime import datetime

DB_PATH = os.path.expanduser("~/.hermes/zvec_content_kb")
COLLECTIONS = {}

# ============================================================
# Embedding（延迟加载，首次调用才载入模型）
# ============================================================
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("shibing624/text2vec-base-chinese")
    return _embedder

def embed(texts):
    model = get_embedder()
    return model.encode(texts, normalize_embeddings=True).tolist()

# ============================================================
# Collection 管理
# ============================================================
def get_collection(name, dim=768):
    if name in COLLECTIONS:
        return COLLECTIONS[name]
    path = os.path.join(DB_PATH, name)
    try:
        coll = zvec.open(path=path)
    except Exception:
        schema = zvec.CollectionSchema(
            name=name,
            vectors=zvec.VectorSchema("embedding", zvec.DataType.VECTOR_FP32, dim),
            fields=[
                zvec.FieldSchema("text", zvec.DataType.STRING),
                zvec.FieldSchema("type", zvec.DataType.STRING),
                zvec.FieldSchema("source", zvec.DataType.STRING),
                zvec.FieldSchema("timestamp", zvec.DataType.STRING),
            ],
        )
        coll = zvec.create_and_open(path=path, schema=schema)
    COLLECTIONS[name] = coll
    return coll

def make_doc(doc_id, text, doc_type, source):
    vec = embed([text])[0]
    return zvec.Doc(
        id=doc_id,
        vectors={"embedding": vec},
        fields={"text": text, "type": doc_type, "source": source, "timestamp": datetime.now().isoformat()},
    )

def result_to_dict(r):
    return {
        "id": r.id,
        "score": round(r.score, 3),
        "text": r.fields.get("text", "") if r.fields else "",
        "type": r.fields.get("type", "") if r.fields else "",
        "source": r.fields.get("source", "") if r.fields else "",
    }

# ============================================================
# 选题库
# ============================================================
def add_topic(topic_id, text, source=""):
    coll = get_collection("topics")
    coll.insert([make_doc(topic_id, text, "topic", source)])

def check_topic_dedup(query, threshold=0.75):
    """检查选题去重，返回相似选题列表"""
    coll = get_collection("topics")
    qvec = embed([query])[0]
    results = coll.query(zvec.Query("embedding", vector=qvec), topk=5)
    return [result_to_dict(r) for r in results if r.score >= threshold]

# ============================================================
# 角度库
# ============================================================
def add_angle(angle_id, text, topic, score=0):
    coll = get_collection("angles")
    coll.insert([make_doc(angle_id, text, topic, str(score))])

def search_angles(query, topk=5):
    """搜相似角度"""
    coll = get_collection("angles")
    qvec = embed([query])[0]
    results = coll.query(zvec.Query("embedding", vector=qvec), topk=topk)
    return [result_to_dict(r) for r in results]

# ============================================================
# 竞品内容库
# ============================================================
def add_competitor(article_id, text, author, platform="weibo"):
    coll = get_collection("competitors")
    coll.insert([make_doc(article_id, text, f"{platform}:{author}", author)])

def search_competitor(query, topk=5):
    coll = get_collection("competitors")
    qvec = embed([query])[0]
    results = coll.query(zvec.Query("embedding", vector=qvec), topk=topk)
    return [result_to_dict(r) for r in results]

# ============================================================
# 风格锚点库
# ============================================================
def add_style_anchor(anchor_id, text, is_good=True):
    coll = get_collection("style_anchors")
    coll.insert([make_doc(anchor_id, text, "good" if is_good else "bad", "user_feedback")])

def check_style(draft_text, topk=5):
    """检查草稿风格，返回 good/bad 相似度"""
    coll = get_collection("style_anchors")
    qvec = embed([draft_text])[0]
    results = coll.query(zvec.Query("embedding", vector=qvec), topk=topk)
    good_scores, bad_scores = [], []
    for r in results:
        d = result_to_dict(r)
        if d["type"] == "good":
            good_scores.append(d["score"])
        elif d["type"] == "bad":
            bad_scores.append(d["score"])
    avg_good = sum(good_scores) / len(good_scores) if good_scores else 0
    avg_bad = sum(bad_scores) / len(bad_scores) if bad_scores else 0
    verdict = "pass"
    if avg_bad > avg_good:
        verdict = "fail"
    elif avg_good < 0.7:
        verdict = "warn"
    return {"good": round(avg_good, 3), "bad": round(avg_bad, 3), "verdict": verdict}

# ============================================================
# CLI 入口（供 Agent 通过 terminal 调用）
# ============================================================
def cli():
    """
    用法:
      python zvec_kb.py add_topic <id> <text> [source]
      python zvec_kb.py add_angle <id> <text> <topic> [score]
      python zvec_kb.py add_competitor <id> <text> <author> [platform]
      python zvec_kb.py add_style <id> <text> [good|bad]
      python zvec_kb.py dedup <query> [threshold]
      python zvec_kb.py search_angles <query> [topk]
      python zvec_kb.py search_competitor <query> [topk]
      python zvec_kb.py check_style <draft_text> [topk]
    """
    if len(sys.argv) < 2:
        print(cli.__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "add_topic" and len(sys.argv) >= 4:
        add_topic(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
        print(json.dumps({"ok": True, "id": sys.argv[2]}))

    elif cmd == "add_angle" and len(sys.argv) >= 5:
        score = int(sys.argv[5]) if len(sys.argv) > 5 else 0
        add_angle(sys.argv[2], sys.argv[3], sys.argv[4], score)
        print(json.dumps({"ok": True, "id": sys.argv[2]}))

    elif cmd == "add_competitor" and len(sys.argv) >= 5:
        platform = sys.argv[5] if len(sys.argv) > 5 else "weibo"
        add_competitor(sys.argv[2], sys.argv[3], sys.argv[4], platform)
        print(json.dumps({"ok": True, "id": sys.argv[2]}))

    elif cmd == "add_style" and len(sys.argv) >= 4:
        is_good = sys.argv[4] != "bad" if len(sys.argv) > 4 else True
        add_style_anchor(sys.argv[2], sys.argv[3], is_good)
        print(json.dumps({"ok": True, "id": sys.argv[2]}))

    elif cmd == "dedup" and len(sys.argv) >= 3:
        threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.75
        results = check_topic_dedup(sys.argv[2], threshold)
        print(json.dumps({"query": sys.argv[2], "matches": results}, ensure_ascii=False))

    elif cmd == "search_angles" and len(sys.argv) >= 3:
        topk = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        results = search_angles(sys.argv[2], topk)
        print(json.dumps({"query": sys.argv[2], "results": results}, ensure_ascii=False))

    elif cmd == "search_competitor" and len(sys.argv) >= 3:
        topk = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        results = search_competitor(sys.argv[2], topk)
        print(json.dumps({"query": sys.argv[2], "results": results}, ensure_ascii=False))

    elif cmd == "check_style" and len(sys.argv) >= 3:
        topk = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        result = check_style(sys.argv[2], topk)
        print(json.dumps(result, ensure_ascii=False))

    else:
        print(cli.__doc__)

if __name__ == "__main__":
    cli()
