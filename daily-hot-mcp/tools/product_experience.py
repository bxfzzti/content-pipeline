"""产品体验/开箱/吐槽内容搜索工具"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Any
from urllib.parse import quote

import feedparser
from bs4 import BeautifulSoup
from fastmcp.tools import Tool
from pydantic import Field

from daily_hot_mcp.utils import http_client


EXPERIENCE_KEYWORDS = (
    "体验",
    "开箱",
    "上手",
    "实测",
    "测评",
    "评测",
    "横评",
    "对比",
    "翻车",
    "吐槽",
    "避坑",
    "值不值",
    "好用",
    "不好用",
    "到手",
    "使用感受",
    "买前",
    "买后",
)

PRODUCT_HINTS = (
    "耳机",
    "手机",
    "电脑",
    "显示器",
    "键盘",
    "鼠标",
    "NAS",
    "硬盘",
    "路由器",
    "咖啡机",
    "洗地机",
    "扫地机",
    "电动牙刷",
    "电饭煲",
    "冰箱",
    "空调",
    "相机",
    "音箱",
    "智能",
)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)).strip()


def _classify(title: str, desc: str) -> str:
    text = f"{title} {desc}"
    if any(word in text for word in ("横评", "对比")):
        return "横评/对比"
    if any(word in text for word in ("吐槽", "翻车", "避坑", "不好用")):
        return "吐槽/避坑"
    if any(word in text for word in ("开箱", "上手", "到手")):
        return "新品开箱/上手"
    if any(word in text for word in ("体验", "实测", "测评", "评测", "使用感受")):
        return "体验/评测"
    if any(word in text for word in ("发布", "新品", "新款")):
        return "新品信息"
    return "产品内容"


def _format_smzdm_time(row: dict[str, Any]) -> str:
    ts = row.get("publish_date_lt")
    if ts:
        try:
            return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    return row.get("publish_time") or row.get("article_format_date") or row.get("article_date") or ""


def _to_int(value: Any) -> int:
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        return int(value or 0)
    except Exception:
        return 0


def _recency_score(publish_time: str) -> int:
    if not publish_time:
        return 0
    for fmt in ("%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            published = datetime.strptime(publish_time, fmt)
            now = datetime.now(published.tzinfo) if published.tzinfo else datetime.now()
            days = max((now - published).days, 0)
            if days <= 2:
                return 12
            if days <= 7:
                return 8
            if days <= 14:
                return 4
            return 0
        except Exception:
            continue
    return 0


def _looks_product_related(title: str, desc: str, keyword: str) -> bool:
    text = f"{title} {desc}"
    if keyword and keyword.lower() in text.lower():
        return True
    return any(word.lower() in text.lower() for word in PRODUCT_HINTS)


async def _search_smzdm(keyword: str, limit: int, offset: int, include_deals: bool) -> list[dict[str, Any]]:
    params = {
        "keyword": keyword,
        "category_id": "",
        "brand_id": "",
        "mall_id": "",
        "order": "time",
        "limit": max(limit * 3, 30),
        "offset": offset,
    }
    response = await http_client.get(
        "https://api.smzdm.com/v1/list",
        params=params,
        headers={
            "User-Agent": "smzdm-product-experience-mcp/1.0",
            "Accept": "application/json, text/plain, */*",
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("data", {}).get("rows", []) if isinstance(data, dict) else []

    results: list[dict[str, Any]] = []
    for row in rows:
        channel_type = row.get("article_channel_type", "")
        channel_name = row.get("article_channel_name", "")
        title = _text(row.get("article_title", ""))
        desc = _text(row.get("article_excerpt") or row.get("article_description") or row.get("article_subtitle") or "")
        content_excerpt = _text(row.get("article_filter_content") or "")[:1200]
        if not include_deals and channel_type not in {"yuanchuang", "post"} and channel_name != "文章":
            continue
        if not _looks_product_related(title, desc, keyword):
            continue
        results.append(
            {
                "source": "smzdm",
                "platform": "什么值得买",
                "channel": channel_type or channel_name,
                "content_type": _classify(title, desc),
                "title": title,
                "description": desc,
                "content_excerpt": content_excerpt,
                "author": row.get("article_referrals", ""),
                "publish_time": _format_smzdm_time(row),
                "collection_count": row.get("article_collection", 0),
                "comment_count": row.get("article_comment", 0),
                "up_count": row.get("article_love_count", 0),
                "cover": row.get("article_pic", ""),
                "link": row.get("article_url", ""),
                "relevance_reason": "关键词命中 + 什么值得买原创/文章频道" if channel_type == "yuanchuang" else "关键词命中 + 什么值得买商品/发现频道",
            }
        )
        if len(results) >= limit:
            break
    return results


async def _search_sspai(keyword: str, limit: int) -> list[dict[str, Any]]:
    response = await http_client.get(
        "https://sspai.com/api/v1/articles",
        params={"limit": 50, "offset": 0},
        headers={"User-Agent": "smzdm-product-experience-mcp/1.0"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("list", []) if isinstance(data, dict) else []
    results: list[dict[str, Any]] = []
    for row in rows:
        title = _text(row.get("title", ""))
        desc = _text(row.get("summary", "") or row.get("promote_intro", ""))
        if keyword and keyword.lower() not in f"{title} {desc}".lower():
            continue
        if not _looks_product_related(title, desc, keyword):
            continue
        released_at = row.get("released_at") or row.get("created_at")
        publish_time = ""
        if released_at:
            publish_time = datetime.fromtimestamp(int(released_at)).strftime("%Y-%m-%d %H:%M:%S")
        results.append(
            {
                "source": "sspai",
                "platform": "少数派",
                "channel": "article",
                "content_type": _classify(title, desc),
                "title": title,
                "description": desc,
                "author": row.get("author", {}).get("nickname", "") if isinstance(row.get("author"), dict) else "",
                "publish_time": publish_time,
                "comment_count": row.get("comment_count", 0),
                "collection_count": row.get("like_count", 0),
                "up_count": row.get("like_count", 0),
                "cover": row.get("banner", ""),
                "link": f"https://sspai.com/post/{row.get('id')}",
                "relevance_reason": "少数派近期数字生活文章关键词命中",
            }
        )
        if len(results) >= limit:
            break
    return results


async def _search_chiphell(keyword: str, limit: int) -> list[dict[str, Any]]:
    response = await http_client.get(
        "https://www.chiphell.com/forum.php",
        params={"mod": "guide", "view": "hot", "rss": "1"},
        headers={"User-Agent": "smzdm-product-experience-mcp/1.0"},
        timeout=15,
    )
    response.raise_for_status()
    feed = feedparser.parse(response.text)
    results: list[dict[str, Any]] = []
    for entry in feed.entries:
        title = _text(getattr(entry, "title", ""))
        desc = _text(getattr(entry, "summary", ""))
        if keyword and keyword.lower() not in f"{title} {desc}".lower():
            continue
        if not _looks_product_related(title, desc, keyword):
            continue
        results.append(
            {
                "source": "chiphell",
                "platform": "Chiphell",
                "channel": "hot_rss",
                "content_type": _classify(title, desc),
                "title": title,
                "description": desc,
                "author": getattr(entry, "author", ""),
                "publish_time": getattr(entry, "published", ""),
                "comment_count": 0,
                "collection_count": 0,
                "up_count": 0,
                "cover": "",
                "link": getattr(entry, "link", ""),
                "relevance_reason": "Chiphell 热门用户体验/开箱 RSS 关键词命中",
            }
        )
        if len(results) >= limit:
            break
    return results


async def search_product_experience_posts_func(
    keyword: Annotated[str, Field(description="产品关键词，如 NAS、洗地机、咖啡机、耳机")] = "",
    limit: Annotated[int, Field(description="最多返回条数，默认20，最大50")] = 20,
    include_deals: Annotated[bool, Field(description="是否保留什么值得买好价/发现频道，默认False，仅取原创/文章")] = False,
    sources: Annotated[str, Field(description="逗号分隔的数据源：smzdm,sspai,chiphell；默认全部")] = "smzdm,sspai,chiphell",
    args: dict | None = None,
) -> list:
    """按产品关键词搜索用户体验、开箱、横评、吐槽和新品相关内容。"""
    if args:
        keyword = args.get("keyword", keyword)
        limit = args.get("limit", limit)
        include_deals = args.get("include_deals", include_deals)
        sources = args.get("sources", sources)

    keyword = str(keyword or "").strip()
    limit = max(1, min(int(limit or 20), 50))
    source_set = {s.strip().lower() for s in str(sources or "").split(",") if s.strip()}
    if not source_set:
        source_set = {"smzdm", "sspai", "chiphell"}

    per_source_limit = max(limit, 10)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    if "smzdm" in source_set:
        try:
            results.extend(await _search_smzdm(keyword, per_source_limit, 0, include_deals))
        except Exception as exc:
            errors.append({"source": "smzdm", "error": str(exc)})
    if "sspai" in source_set:
        try:
            results.extend(await _search_sspai(keyword, per_source_limit))
        except Exception as exc:
            errors.append({"source": "sspai", "error": str(exc)})
    if "chiphell" in source_set:
        try:
            results.extend(await _search_chiphell(keyword, per_source_limit))
        except Exception as exc:
            errors.append({"source": "chiphell", "error": str(exc)})

    def score_breakdown(item: dict[str, Any]) -> dict[str, int]:
        text = f"{item.get('title','')} {item.get('description','')}"
        content_type = item.get("content_type")
        breakdown = {
            "keyword": 30 if keyword and keyword.lower() in text.lower() else 0,
            "source": 0,
            "content_type": {
                "体验/评测": 25,
                "吐槽/避坑": 24,
                "横评/对比": 22,
                "新品开箱/上手": 20,
                "新品信息": 12,
                "产品内容": 6,
            }.get(content_type, 0),
            "engagement": 0,
            "recency": _recency_score(str(item.get("publish_time") or "")),
            "concrete_product": 0,
        }
        if item.get("source") == "smzdm" and item.get("channel") in {"yuanchuang", "post"}:
            breakdown["source"] = 15
        elif item.get("source") == "sspai":
            breakdown["source"] = 10
        elif item.get("source") == "chiphell":
            breakdown["source"] = 8

        comments = _to_int(item.get("comment_count"))
        collections = _to_int(item.get("collection_count"))
        ups = _to_int(item.get("up_count"))
        breakdown["engagement"] = min(comments // 4, 8) + min(collections // 3, 6) + min(ups // 5, 4)

        title = str(item.get("title") or "")
        if re.search(r"[A-Za-z]+\\s*\\d|\\d{2,}|Pro|Max|Ultra|Plus|Mini", title, re.I):
            breakdown["concrete_product"] = 6
        return breakdown

    def score(item: dict[str, Any]) -> int:
        breakdown = score_breakdown(item)
        return sum(breakdown.values())

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(results, key=score, reverse=True):
        key = item.get("link") or item.get("title")
        if key in seen:
            continue
        seen.add(key)
        breakdown = score_breakdown(item)
        item["score_breakdown"] = breakdown
        item["creative_score"] = sum(breakdown.values())
        item["match_score"] = item["creative_score"]
        deduped.append(item)
        if len(deduped) >= limit:
            break

    if not deduped and not errors:
        return [
            {
                "source": "meta",
                "platform": "no_results",
                "keyword": keyword,
                "message": "未找到符合过滤条件的产品体验内容；如需包含纯优惠/好价，请设置 include_deals=true。",
                "items_count": 0,
            }
        ]

    if errors:
        deduped.append({"source": "meta", "platform": "source_errors", "errors": errors})
    return deduped


product_experience_tool_config = Tool.from_function(
    fn=search_product_experience_posts_func,
    name="search-product-experience-posts",
    description="按产品关键词搜索什么值得买/少数派/Chiphell上的体验、开箱、横评、吐槽、新品和消费决策内容，适合小红书二创选题。",
)

product_experience_tools = [product_experience_tool_config]
