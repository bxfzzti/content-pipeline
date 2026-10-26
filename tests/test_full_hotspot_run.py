import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "sourcing-hotspots" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from full_hotspot_run import (  # noqa: E402
    SourceSpec,
    _parse_sse_json,
    build_source_registry,
    resolve_result,
    run_source_batch,
)


class FullHotspotRunTests(unittest.TestCase):
    def test_registry_contains_no_authenticated_xhs(self):
        names = {source.name.lower() for source in build_source_registry()}
        self.assertTrue(any(source.kind == "aggregator" for source in build_source_registry()))
        self.assertTrue(any(source.kind == "product" for source in build_source_registry()))
        self.assertTrue(any(source.kind == "car-search" for source in build_source_registry()))
        self.assertTrue(any(source.kind == "mcp-tool" for source in build_source_registry()))
        self.assertIn("dongchedi-site-search", names)
        self.assertIn("daily-hot-autohome", names)
        self.assertIn("vertical-auto-search", names)
        self.assertFalse(any("xhs" in name or "xiaohongshu" in name for name in names))

    def test_dongchedi_site_search_runs_before_autohome(self):
        names = [source.name for source in build_source_registry()]
        self.assertLess(names.index("dongchedi-site-search"), names.index("daily-hot-autohome"))

    def test_parse_sse_json_extracts_data_payload(self):
        payload = _parse_sse_json('event: message\ndata: {"jsonrpc":"2.0","result":{"ok":true}}\n\n')
        self.assertEqual(payload["result"], {"ok": True})

    def test_failed_source_uses_cache(self):
        result = resolve_result(
            "rss:test",
            live=None,
            cached={"data": [1]},
            error="timeout",
            elapsed_ms=20,
            cache_time="2026-07-16T00:00:00+00:00",
        )
        self.assertEqual(result.status, "cache")
        self.assertEqual(result.data, {"data": [1]})
        self.assertEqual(result.cache_time, "2026-07-16T00:00:00+00:00")

    def test_failed_source_without_cache_is_unavailable(self):
        result = resolve_result(
            "rss:test",
            live=None,
            cached=None,
            error="timeout",
            elapsed_ms=20,
        )
        self.assertEqual(result.status, "unavailable")
        self.assertIsNone(result.data)

    def test_batch_returns_at_deadline_and_falls_back(self):
        specs = [
            SourceSpec("fast", "rss"),
            SourceSpec("slow", "rss"),
        ]

        def fetcher(spec, _deadline):
            if spec.name == "slow":
                time.sleep(0.3)
            return {"source": spec.name}

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            (cache_dir / "slow.json").write_text(
                '{"cached_at":"2026-07-16T00:00:00+00:00","data":{"source":"cached"}}',
                encoding="utf-8",
            )
            started = time.monotonic()
            results = run_source_batch(
                specs,
                fetcher=fetcher,
                cache_dir=cache_dir,
                deadline_seconds=0.05,
            )
            elapsed = time.monotonic() - started

        by_name = {result.name: result for result in results}
        self.assertLess(elapsed, 0.2)
        self.assertEqual(by_name["fast"].status, "live")
        self.assertEqual(by_name["slow"].status, "cache")
        self.assertEqual(by_name["slow"].data, {"source": "cached"})


if __name__ == "__main__":
    unittest.main()
