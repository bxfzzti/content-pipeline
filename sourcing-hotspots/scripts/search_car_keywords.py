#!/usr/bin/env python3
"""
车型关键词主动搜索层。
用品牌+车型+事件关键词组合搜索，捕获尚未登上热榜的新车发布、价格公布等事件。

用法：
    python3 search_car_keywords.py [--hours 24] [--output /tmp/car_keyword_results.json]

输出：按品牌分组的最新消息列表
"""
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), '..', 'references', 'car-model-keywords.json')

def load_keywords():
    with open(KEYWORDS_PATH, 'r') as f:
        return json.load(f)

def search_ddg(query, limit=5):
    """DuckDuckGo lite search，返回结果列表"""
    url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        # 简单提取结果
        results = []
        import re
        # DDG lite 的结果在 <a class="result-link" href="..."> 和 <td class="result-snippet"> 中
        links = re.findall(r'class="result-link"[^>]*href="([^"]+)"[^>]*>([^<]+)', html)
        snippets = re.findall(r'class="result-snippet"[^>]*>([^<]+)', html)
        for i, (url, title) in enumerate(links[:limit]):
            snippet = snippets[i].strip() if i < len(snippets) else ""
            results.append({"title": title.strip(), "url": url, "snippet": snippet})
        return results
    except Exception as e:
        return []

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hours', type=int, default=24, help='时间窗口（小时）')
    parser.add_argument('--output', type=str, default='/tmp/car_keyword_results.json')
    parser.add_argument('--max-searches', type=int, default=30, help='最大搜索次数')
    args = parser.parse_args()

    data = load_keywords()
    results = []
    search_count = 0

    # 对每个品牌的每个车型，组合事件关键词搜索
    for category, brands in data['categories'].items():
        for brand, models in brands.items():
            if search_count >= args.max_searches:
                break
            # 用品牌名 + 最近事件关键词搜索
            for event_kw in ["上市", "发布", "预售", "申报", "交付", "降价"]:
                if search_count >= args.max_searches:
                    break
                query = f"{brand} {event_kw} {datetime.now().strftime('%Y年%m月')}"
                hits = search_ddg(query, limit=3)
                search_count += 1
                for h in hits:
                    results.append({
                        "brand": brand,
                        "category": category,
                        "query": query,
                        "title": h['title'],
                        "url": h['url'],
                        "snippet": h['snippet']
                    })

    # 用 hot_search_keywords 补充
    for kw in data.get('hot_search_keywords', [])[:10]:
        if search_count >= args.max_searches:
            break
        query = f"{kw} {datetime.now().strftime('%Y年%m月')}"
        hits = search_ddg(query, limit=3)
        search_count += 1
        for h in hits:
            results.append({
                "brand": "通用事件",
                "category": "事件",
                "query": query,
                "title": h['title'],
                "url": h['url'],
                "snippet": h['snippet']
            })

    output = {
        "search_time": datetime.now(timezone.utc).isoformat(),
        "searches_made": search_count,
        "total_results": len(results),
        "results": results
    }

    with open(args.output, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"搜索完成：{search_count}次搜索，{len(results)}条结果")
    print(f"输出：{args.output}")

if __name__ == '__main__':
    main()
