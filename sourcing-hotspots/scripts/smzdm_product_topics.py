#!/usr/bin/env python3
"""Run the SMZDM product-topic pipeline and optionally sync rows to Lark Base."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


KEYWORDS = {
    "电脑数码主抓": ["NAS", "耳机", "键盘", "路由器", "显卡", "显示器", "手机", "充电器", "游戏本"],
    "生活电器主抓": ["洗地机", "咖啡机", "扫地机器人", "空气净化器", "空调", "冰箱"],
    "家居/办公/车载补充": ["浴霸", "投影仪", "3D打印机", "车载冰箱", "智能门锁"],
}

FIELDS = [
    "标题",
    "原文链接",
    "关键词",
    "组别",
    "内容类型",
    "单篇分",
    "关键词稳定分",
    "排名",
    "评论数",
    "收藏数",
    "点赞数",
    "发布时间",
    "抓取时间",
    "内容定位",
    "二创切入",
    "分数明细",
    "状态",
    "今日新增",
]


def clean(value: Any, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[:limit].rstrip() + "..."
    return text


def to_int(value: Any) -> int:
    try:
        return int(str(value or "0").replace(",", "").strip())
    except Exception:
        return 0


def extract_url(value: Any) -> str:
    text = clean(value)
    match = re.search(r"\((https?://[^)]+)\)", text)
    if match:
        return match.group(1)
    match = re.search(r"https?://\\S+", text)
    return match.group(0) if match else text


def summarize(item: dict[str, Any]) -> tuple[str, str]:
    keyword = item.get("_keyword") or ""
    content_type = item.get("content_type") or "产品内容"
    excerpt = clean(item.get("content_excerpt") or item.get("description"), 220)
    if content_type in {"体验/评测", "新品开箱/上手"}:
        angle = f"适合做「{keyword}真实体验/买前担忧」方向。"
    elif content_type == "横评/对比":
        angle = f"适合做「{keyword}怎么选/参数之外的差异」方向。"
    elif content_type == "吐槽/避坑":
        angle = f"适合做「{keyword}避坑/翻车复盘」方向。"
    elif content_type == "新品信息":
        angle = f"适合做「{keyword}新品值不值得关注」方向。"
    else:
        angle = f"适合做「{keyword}消费决策/选购清单」方向。"
    return excerpt, angle


async def fetch_topics(limit_per_keyword: int) -> tuple[list[dict[str, Any]], list[tuple[str, str, int, int, float, float]]]:
    rows: list[dict[str, Any]] = []
    keyword_stats: list[tuple[str, str, int, int, float, float]] = []

    async with streamablehttp_client("http://127.0.0.1:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for group, keywords in KEYWORDS.items():
                for keyword in keywords:
                    result = await session.call_tool(
                        "search-product-experience-posts",
                        {
                            "keyword": keyword,
                            "limit": limit_per_keyword,
                            "include_deals": False,
                            "sources": "smzdm",
                        },
                    )
                    payload = json.loads("".join(getattr(c, "text", str(c)) for c in result.content))
                    items = [x for x in payload if isinstance(x, dict) and x.get("source") != "meta"]
                    for item in items:
                        item["_keyword"] = keyword
                        item["_group"] = group
                        rows.append(item)
                    scores = [to_int(x.get("creative_score")) for x in items]
                    top = max(scores, default=0)
                    avg = round(sum(scores[:5]) / max(len(scores[:5]), 1), 1) if scores else 0.0
                    stable = round(avg + min(len(items), 8) * 1.5, 1)
                    keyword_stats.append((group, keyword, len(items), top, avg, stable))

    best: dict[str, dict[str, Any]] = {}
    for item in rows:
        key = item.get("link") or item.get("title")
        if not key:
            continue
        if key not in best or to_int(item.get("creative_score")) > to_int(best[key].get("creative_score")):
            best[key] = item
    ranked = sorted(best.values(), key=lambda x: to_int(x.get("creative_score")), reverse=True)
    stable_by_keyword = {keyword: stable for _, keyword, _, _, _, stable in keyword_stats}
    for index, item in enumerate(ranked, 1):
        item["_rank"] = index
        item["_keyword_stable_score"] = stable_by_keyword.get(item.get("_keyword"), 0.0)
    return ranked, keyword_stats


def build_base_rows(items: list[dict[str, Any]], fetched_at: str, max_rows: int) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for item in items[:max_rows]:
        breakdown = item.get("score_breakdown") or {}
        excerpt, angle = summarize(item)
        detail = (
            f"kw{breakdown.get('keyword', 0)} / src{breakdown.get('source', 0)} / "
            f"type{breakdown.get('content_type', 0)} / eng{breakdown.get('engagement', 0)} / "
            f"new{breakdown.get('recency', 0)} / model{breakdown.get('concrete_product', 0)}"
        )
        rows.append(
            [
                clean(item.get("title"), 500),
                item.get("link") or "",
                item.get("_keyword") or "",
                item.get("_group") or "",
                item.get("content_type") or "产品内容",
                to_int(item.get("creative_score")),
                float(item.get("_keyword_stable_score") or 0),
                to_int(item.get("_rank")),
                to_int(item.get("comment_count")),
                to_int(item.get("collection_count")),
                to_int(item.get("up_count")),
                item.get("publish_time") or None,
                fetched_at,
                excerpt,
                angle,
                detail,
                "待评估",
                True,
            ]
        )
    return rows


def write_report(path: Path, items: list[dict[str, Any]], keyword_stats: list[tuple[str, str, int, int, float, float]], fetched_at: str) -> None:
    type_counts: dict[str, int] = defaultdict(int)
    for item in items:
        type_counts[item.get("content_type") or "未分类"] += 1

    lines = [
        "# 什么值得买产品体验默认池",
        "",
        f"- 运行时间：{fetched_at}",
        "- sources：smzdm",
        "- include_deals：false，过滤纯优惠/好价",
        "- 品类稳定分：前5条平均单篇分 + 有效条数加成",
        "",
        "## 关键词表现",
        "",
        "| 组别 | 关键词 | 有效条数 | 最高单篇分 | 前5平均分 | 品类稳定分 |",
        "|------|--------|----------|------------|------------|------------|",
    ]
    for group, keyword, count, top, avg, stable in sorted(keyword_stats, key=lambda x: (-x[5], -x[3], -x[2])):
        lines.append(f"| {group} | {keyword} | {count} | {top} | {avg} | {stable} |")

    lines.extend(["", "## 高分文章素材", ""])
    for item in items[:50]:
        excerpt, angle = summarize(item)
        lines.extend(
            [
                f"### {item.get('_rank')}. {clean(item.get('title'))}",
                f"- 关键词：{item.get('_keyword')} / 类型：{item.get('content_type')} / 分数：{item.get('creative_score')}",
                f"- 链接：{item.get('link')}",
                f"- 内容定位：{excerpt}",
                f"- 二创切入：{angle}",
                "",
            ]
        )

    lines.extend(["## 类型分布", ""])
    for content_type, count in sorted(type_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {content_type}: {count} 条")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_lark(args: list[str], cwd: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    proc = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    try:
        data = json.loads(proc.stdout)
    except Exception:
        data = {"ok": False, "raw": proc.stdout, "returncode": proc.returncode}
    if proc.returncode != 0 or data.get("ok") is False:
        raise RuntimeError(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def sync_to_lark(base_token: str, table_id: str, rows: list[list[Any]], workdir: Path) -> None:
    # Manual upsert by URL. record-search may be unavailable for some tenants, so
    # read existing URLs with record-list and do local lookup.
    existing: dict[str, str] = {}
    offset = 0
    while True:
        listed = run_lark(
            [
                "lark-cli",
                "base",
                "+record-list",
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--field-id",
                "原文链接",
                "--limit",
                "200",
                "--offset",
                str(offset),
                "--format",
                "json",
                "--as",
                "user",
            ],
            workdir,
        )
        data = listed.get("data") or {}
        values = data.get("data") or []
        record_ids = data.get("record_id_list") or []
        for record_id, value_row in zip(record_ids, values):
            if value_row:
                existing[extract_url(value_row[0])] = record_id
        if not data.get("has_more"):
            break
        offset += 200

    to_create: list[list[Any]] = []
    for row in rows:
        url = row[FIELDS.index("原文链接")]
        record_id = existing.get(extract_url(url))
        if record_id:
            patch = {field: value for field, value in zip(FIELDS, row)}
            patch["今日新增"] = False
            run_lark(
                [
                    "lark-cli",
                    "base",
                    "+record-upsert",
                    "--base-token",
                    base_token,
                    "--table-id",
                    table_id,
                    "--record-id",
                    record_id,
                    "--json",
                    json.dumps(patch, ensure_ascii=False),
                    "--as",
                    "user",
                ],
                workdir,
            )
        else:
            to_create.append(row)
        time.sleep(0.15)

    for start in range(0, len(to_create), 200):
        batch = {"fields": FIELDS, "rows": to_create[start : start + 200]}
        run_lark(
            [
                "lark-cli",
                "base",
                "+record-batch-create",
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--json",
                json.dumps(batch, ensure_ascii=False),
                "--as",
                "user",
            ],
            workdir,
        )


async def amain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--limit-per-keyword", type=int, default=10)
    parser.add_argument("--max-rows", type=int, default=80)
    parser.add_argument("--sync-lark", action="store_true")
    parser.add_argument("--base-token", default=os.environ.get("HERMES_TOPICS_BASE_TOKEN", ""))
    parser.add_argument("--table-id", default=os.environ.get("HERMES_TOPICS_TABLE_ID", "选题池"))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items, keyword_stats = await fetch_topics(args.limit_per_keyword)
    rows = build_base_rows(items, fetched_at, args.max_rows)

    (output_dir / "smzdm_product_topics_rows.json").write_text(
        json.dumps({"fields": FIELDS, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "smzdm_product_topics_items.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(output_dir / "smzdm_product_topics_report.md", items, keyword_stats, fetched_at)

    if args.sync_lark:
        if not args.base_token:
            raise SystemExit("--sync-lark requires --base-token or HERMES_TOPICS_BASE_TOKEN")
        sync_to_lark(args.base_token, args.table_id, rows, Path.cwd())


if __name__ == "__main__":
    asyncio.run(amain())
