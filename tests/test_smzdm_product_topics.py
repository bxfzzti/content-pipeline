import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "sourcing-hotspots" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from smzdm_product_topics import (  # noqa: E402
    FIELDS,
    collect_keyword_results,
    load_existing_rows,
)


class ProductTopicTests(unittest.IsolatedAsyncioTestCase):
    async def test_keyword_jobs_are_bounded_and_parallel(self):
        active = 0
        peak = 0

        async def fake_call(_group, keyword, _limit):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.02)
            active -= 1
            return [{"title": keyword, "link": f"https://example.com/{keyword}", "creative_score": 80}]

        results = await collect_keyword_results(fake_call, limit_per_keyword=1, concurrency=4, timeout_seconds=1)
        self.assertEqual(len(results), 20)
        self.assertLessEqual(peak, 4)
        self.assertGreater(peak, 1)

    async def test_keyword_timeout_does_not_cancel_other_keywords(self):
        async def fake_call(_group, keyword, _limit):
            if keyword == "NAS":
                await asyncio.sleep(0.1)
            return [{"title": keyword, "creative_score": 70}]

        results = await collect_keyword_results(fake_call, limit_per_keyword=1, concurrency=5, timeout_seconds=0.02)
        by_keyword = {result.keyword: result for result in results}
        self.assertEqual(by_keyword["NAS"].items, [])
        self.assertIn("timeout", by_keyword["NAS"].error.lower())
        self.assertTrue(by_keyword["耳机"].items)

    def test_sync_existing_loads_rows_without_fetch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rows.json"
            path.write_text(json.dumps({"fields": FIELDS, "rows": [["标题"] + [None] * (len(FIELDS) - 1)]}), encoding="utf-8")
            fields, rows = load_existing_rows(path)
        self.assertEqual(fields, FIELDS)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
