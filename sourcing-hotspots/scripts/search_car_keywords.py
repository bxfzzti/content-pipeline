#!/usr/bin/env python3
"""车型关键词主动搜索层。

用品牌、车型、事件关键词和汽车垂直站点组合搜索，捕获尚未登上热榜的新车发布、
价格公布、车主口碑、测试争议等事件。懂车帝、汽车之家、易车没有稳定公开 RSS/API，
因此只作为公开搜索索引补链源使用，不依赖登录态、Cookie 或逆向接口。

用法：
    python3 search_car_keywords.py [--output /tmp/car_keyword_results.json]

输出：结构化搜索结果，保留标题、摘要、来源、原文链接。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
from typing import Any, Iterable
from urllib.parse import urlparse


KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "..", "references", "car-model-keywords.json")

VERTICAL_SITE_QUERIES = [
    {
        "site": "dongchedi.com",
        "source": "懂车帝",
        "intent": "车主体验/评测/争议",
        "keywords": ["评测", "车主", "实测", "吐槽", "续航", "智驾"],
    },
    {
        "site": "autohome.com.cn",
        "source": "汽车之家",
        "intent": "口碑/论坛/配置价格",
        "keywords": ["口碑", "论坛", "车主", "问题", "优惠", "配置"],
    },
    {
        "site": "yiche.com",
        "source": "易车",
        "intent": "新车/导购/评测",
        "keywords": ["新车", "上市", "导购", "评测", "价格", "配置"],
    },
    {
        "site": "chedongxi.com",
        "source": "车东西",
        "intent": "智能汽车/产业信号",
        "keywords": ["智驾", "发布", "量产", "测试", "芯片", "座舱"],
    },
    {
        "site": "d1ev.com",
        "source": "第一电动",
        "intent": "新能源车/产业信号",
        "keywords": ["新能源", "上市", "销量", "续航", "补能", "智驾"],
    },
    {
        "site": "42how.com",
        "source": "42号车库",
        "intent": "新能源车体验/深度讨论",
        "keywords": ["体验", "试驾", "评测", "智驾", "续航", "车主"],
    },
]

EVENT_KEYWORDS = ["上市", "发布", "预售", "申报", "交付", "降价"]
FOCUS_CATEGORIES = {"新势力", "华为系", "传统+合资", "比亚迪系"}


def load_keywords(path: str = KEYWORDS_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def strip_tags(value: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", value)).strip()


def parse_ddg_lite(html: str, limit: int = 5) -> list[dict[str, str]]:
    """解析 DuckDuckGo lite 结果。独立函数便于单测，不把网络状态混进解析逻辑。"""
    results = []
    links = re.findall(r'class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.S)
    snippets = re.findall(r'class="result-snippet"[^>]*>(.*?)</td>', html, flags=re.S)
    for index, (url, title) in enumerate(links[:limit]):
        snippet = strip_tags(snippets[index]) if index < len(snippets) else ""
        results.append({"title": strip_tags(title), "url": unescape(url), "snippet": snippet})
    return results


def parse_rss_search(xml_text: str, limit: int = 5) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    results = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", default="").strip()
        url = item.findtext("link", default="").strip()
        snippet = item.findtext("description", default="").strip()
        if title:
            results.append({"title": strip_tags(title), "url": unescape(url), "snippet": strip_tags(snippet)})
    return results


def fetch_text(url: str, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def search_bing_rss(query: str, limit: int = 5, timeout: float = 10.0) -> list[dict[str, str]]:
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&format=rss"
    try:
        return parse_rss_search(fetch_text(url, timeout), limit=limit)
    except Exception:  # noqa: BLE001 - source failures are isolated by design
        return []


def search_google_news_rss(query: str, limit: int = 5, timeout: float = 10.0) -> list[dict[str, str]]:
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    try:
        return parse_rss_search(fetch_text(url, timeout), limit=limit)
    except Exception:  # noqa: BLE001 - source failures are isolated by design
        return []


def search_ddg(query: str, limit: int = 5, timeout: float = 10.0) -> list[dict[str, str]]:
    """DuckDuckGo lite search，返回结果列表。失败返回空列表，不阻塞热点主流程。"""
    url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
    try:
        return parse_ddg_lite(fetch_text(url, timeout), limit=limit)
    except Exception:  # noqa: BLE001 - source failures are isolated by design
        return []


def search_public_index(query: str, limit: int = 5, timeout: float = 10.0) -> list[dict[str, str]]:
    for searcher in (search_bing_rss, search_google_news_rss, search_ddg):
        results = searcher(query, limit=limit, timeout=timeout)
        if results:
            return results
    return []


def iter_brand_event_queries(data: dict[str, Any], month_label: str) -> Iterable[dict[str, str]]:
    for category, brands in data["categories"].items():
        for brand in brands:
            for event_keyword in EVENT_KEYWORDS:
                yield {
                    "category": category,
                    "brand": brand,
                    "query": f"{brand} {event_keyword} {month_label}",
                    "source": "全网搜索",
                    "intent": "品牌事件",
                    "site": "",
                }


def iter_vertical_site_queries(
    data: dict[str, Any],
    month_label: str,
    max_brands: int = 10,
    include_sites: set[str] | None = None,
    exclude_sites: set[str] | None = None,
) -> Iterable[dict[str, str]]:
    focus_brands: list[tuple[str, str]] = []
    for category, brands in data["categories"].items():
        if category in FOCUS_CATEGORIES:
            focus_brands.extend((category, brand) for brand in brands)

    # Site-major order keeps Dongchedi ahead of other vertical platforms.
    # With a global max-searches budget, brand-major ordering would spend the
    # first batch across many sites and leave later brands without Dongchedi
    # coverage. Dongchedi is the primary automotive vertical source here.
    for source in VERTICAL_SITE_QUERIES:
        site = source["site"]
        if include_sites and site not in include_sites:
            continue
        if exclude_sites and site in exclude_sites:
            continue
        for category, brand in focus_brands[:max_brands]:
            terms = " ".join(source["keywords"][:3])
            yield {
                "category": category,
                "brand": brand,
                "query": f"site:{source['site']} {brand} {terms} {month_label}",
                "source": source["source"],
                "intent": source["intent"],
                "site": source["site"],
            }


def hit_matches_site(hit: dict[str, str], site: str) -> bool:
    if not site:
        return True
    host = urlparse(hit.get("url", "")).netloc.lower()
    if site.lower() in host:
        return True
    text = f"{hit.get('title', '')} {hit.get('snippet', '')}".lower()
    return site.lower() in text


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    data = load_keywords()
    results = []
    search_count = 0
    month_label = datetime.now().strftime("%Y年%m月")

    query_specs = list(iter_brand_event_queries(data, month_label)) if args.general_search else []
    include_sites = {site.strip() for site in args.include_sites.split(",") if site.strip()} if args.include_sites else None
    exclude_sites = {site.strip() for site in args.exclude_sites.split(",") if site.strip()} if args.exclude_sites else None
    if args.vertical_sites:
        query_specs = list(
            iter_vertical_site_queries(
                data,
                month_label,
                args.max_vertical_brands,
                include_sites=include_sites,
                exclude_sites=exclude_sites,
            )
        ) + query_specs

    for query_spec in query_specs:
        if search_count >= args.max_searches:
            break
        hits = search_public_index(query_spec["query"], limit=args.limit_per_query, timeout=args.timeout)
        search_count += 1
        for hit in hits:
            if not hit_matches_site(hit, query_spec.get("site", "")):
                continue
            results.append({**query_spec, "title": hit["title"], "url": hit["url"], "snippet": hit["snippet"]})

    if not args.general_search:
        return {
            "search_time": datetime.now(timezone.utc).isoformat(),
            "searches_made": search_count,
            "total_results": len(results),
            "vertical_sources": [
                source
                for source in VERTICAL_SITE_QUERIES
                if (not include_sites or source["site"] in include_sites)
                and (not exclude_sites or source["site"] not in exclude_sites)
            ],
            "results": results,
        }

    for keyword in data.get("hot_search_keywords", [])[:10]:
        if search_count >= args.max_searches:
            break
        query = f"{keyword} {month_label}"
        hits = search_public_index(query, limit=args.limit_per_query, timeout=args.timeout)
        search_count += 1
        for hit in hits:
            results.append(
                {
                    "brand": "通用事件",
                    "category": "事件",
                    "query": query,
                    "source": "全网搜索",
                    "site": "",
                    "intent": "事件补充",
                    "title": hit["title"],
                    "url": hit["url"],
                    "snippet": hit["snippet"],
                }
            )

    return {
        "search_time": datetime.now(timezone.utc).isoformat(),
        "searches_made": search_count,
        "total_results": len(results),
        "vertical_sources": [
            source
            for source in VERTICAL_SITE_QUERIES
            if (not include_sites or source["site"] in include_sites)
            and (not exclude_sites or source["site"] not in exclude_sites)
        ],
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=24, help="时间窗口（小时，保留兼容参数）")
    parser.add_argument("--output", type=str, default="/tmp/car_keyword_results.json")
    parser.add_argument("--max-searches", type=int, default=24, help="最大搜索次数")
    parser.add_argument("--max-vertical-brands", type=int, default=8, help="垂直站点最多覆盖品牌数")
    parser.add_argument("--limit-per-query", type=int, default=3, help="每次搜索最多保留结果数")
    parser.add_argument("--timeout", type=float, default=6.0, help="单次搜索超时秒数")
    parser.add_argument("--include-sites", default="", help="只搜索这些站点，逗号分隔，如 dongchedi.com")
    parser.add_argument("--exclude-sites", default="", help="排除这些站点，逗号分隔")
    parser.add_argument("--general-search", action=argparse.BooleanOptionalAction, default=True, help="是否启用非站点限定的品牌/事件全网搜索")
    parser.add_argument("--vertical-sites", action=argparse.BooleanOptionalAction, default=True, help="启用汽车垂直站点搜索补链")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = run_search(args)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)
    print(f"搜索完成：{output['searches_made']}次搜索，{output['total_results']}条结果")
    print(f"输出：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
