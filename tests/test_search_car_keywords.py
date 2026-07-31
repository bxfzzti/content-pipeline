import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "sourcing-hotspots" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from search_car_keywords import (  # noqa: E402
    VERTICAL_SITE_QUERIES,
    hit_matches_site,
    iter_vertical_site_queries,
    parse_ddg_lite,
    parse_rss_search,
    run_search,
)


class SearchCarKeywordsTests(unittest.TestCase):
    def test_vertical_sources_cover_core_auto_sites(self):
        sites = {source["site"] for source in VERTICAL_SITE_QUERIES}

        self.assertIn("dongchedi.com", sites)
        self.assertIn("autohome.com.cn", sites)
        self.assertIn("yiche.com", sites)

    def test_iter_vertical_site_queries_uses_site_scoped_queries(self):
        data = {
            "categories": {
                "新势力": {"理想": ["L6"], "小鹏": ["MONA"]},
                "AI": {"OpenAI": ["GPT"]},
            }
        }

        queries = list(iter_vertical_site_queries(data, "2026年07月", max_brands=2))

        self.assertTrue(any(item["query"].startswith("site:dongchedi.com 理想") for item in queries))
        self.assertFalse(any(item["brand"] == "OpenAI" for item in queries))
        self.assertFalse(any(" OR " in item["query"] for item in queries))
        self.assertEqual([item["source"] for item in queries[:2]], ["懂车帝", "懂车帝"])

    def test_hit_matches_site_rejects_search_noise(self):
        self.assertTrue(hit_matches_site({"url": "https://www.autohome.com.cn/news/1.html"}, "autohome.com.cn"))
        self.assertFalse(hit_matches_site({"url": "https://www.foodnetwork.com/recipes/lasagna"}, "dongchedi.com"))

    def test_iter_vertical_site_queries_can_include_only_dongchedi(self):
        data = {"categories": {"新势力": {"理想": ["L6"], "小鹏": ["MONA"]}}}

        queries = list(iter_vertical_site_queries(data, "2026年07月", max_brands=2, include_sites={"dongchedi.com"}))

        self.assertTrue(queries)
        self.assertTrue(all(item["site"] == "dongchedi.com" for item in queries))

    def test_iter_vertical_site_queries_can_exclude_dongchedi(self):
        data = {"categories": {"新势力": {"理想": ["L6"]}}}

        queries = list(iter_vertical_site_queries(data, "2026年07月", max_brands=1, exclude_sites={"dongchedi.com"}))

        self.assertTrue(queries)
        self.assertFalse(any(item["site"] == "dongchedi.com" for item in queries))

    def test_parse_ddg_lite_extracts_title_url_and_snippet(self):
        html = """
        <a class="result-link" href="https://www.autohome.com.cn/news/1.html">理想 L6 车主口碑</a>
        <td class="result-snippet">真实车主反馈 &amp; 配置争议</td>
        """

        results = parse_ddg_lite(html)

        self.assertEqual(
            results,
            [
                {
                    "title": "理想 L6 车主口碑",
                    "url": "https://www.autohome.com.cn/news/1.html",
                    "snippet": "真实车主反馈 & 配置争议",
                }
            ],
        )

    def test_parse_rss_search_extracts_search_items(self):
        xml = """<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0"><channel>
          <item>
            <title>问界 M9 续航实测</title>
            <link>https://example.com/m9</link>
            <description>第三方测试 &amp; 用户争议</description>
          </item>
        </channel></rss>
        """

        results = parse_rss_search(xml)

        self.assertEqual(
            results,
            [
                {
                    "title": "问界 M9 续航实测",
                    "url": "https://example.com/m9",
                    "snippet": "第三方测试 & 用户争议",
                }
            ],
        )

    def test_run_search_can_disable_general_search(self):
        import argparse
        import search_car_keywords

        original_load = search_car_keywords.load_keywords
        original_search = search_car_keywords.search_public_index
        search_car_keywords.load_keywords = lambda: {
            "categories": {"新势力": {"理想": ["L6"]}},
            "hot_search_keywords": ["新车上市"],
        }
        search_car_keywords.search_public_index = lambda query, **_kwargs: [
            {"title": query, "url": "https://www.dongchedi.com/article/1", "snippet": "dongchedi.com"}
        ]
        try:
            result = run_search(
                argparse.Namespace(
                    vertical_sites=True,
                    max_vertical_brands=1,
                    max_searches=10,
                    limit_per_query=1,
                    timeout=1,
                    include_sites="dongchedi.com",
                    exclude_sites="",
                    general_search=False,
                )
            )
        finally:
            search_car_keywords.load_keywords = original_load
            search_car_keywords.search_public_index = original_search

        self.assertEqual(result["searches_made"], 1)
        self.assertEqual(result["total_results"], 1)
        self.assertEqual(result["results"][0]["site"], "dongchedi.com")


if __name__ == "__main__":
    unittest.main()
