#!/usr/bin/env python3
"""Run the full hotspot stage with a hard deadline and per-source fallback."""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional


RSS_SOURCES = [
    ("TechCrunch", "https://techcrunch.com/feed/", "intl"),
    ("TheVerge", "https://www.theverge.com/rss/index.xml", "intl"),
    ("Wired", "https://www.wired.com/feed/rss", "intl"),
    ("ArsTechnica", "https://feeds.arstechnica.com/arstechnica/index", "intl"),
    ("MIT-TR", "https://www.technologyreview.com/feed/", "intl"),
    ("HN-AI", "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+Claude+OR+DeepSeek&count=30&points=20", "intl"),
    ("ProductHunt", "https://www.producthunt.com/feed", "intl"),
    ("9to5Mac", "https://9to5mac.com/feed/", "intl"),
    ("TheVerge-Gadgets", "https://www.theverge.com/rss/gadgets/index.xml", "intl"),
    ("TheVerge-Transport", "https://www.theverge.com/rss/transportation/index.xml", "intl"),
    ("GoogleAI", "https://blog.google/technology/ai/rss/", "intl"),
    ("36Kr", "https://36kr.com/feed", "intl"),
    ("Engadget", "https://www.engadget.com/rss.xml", "intl"),
    ("GSMArena", "https://www.gsmarena.com/rss-news-reviews.php3", "intl"),
    ("ITHome", "https://www.ithome.com/rss/", "home"),
    ("ifanr", "https://www.ifanr.com/feed", "home"),
    ("TheVerge-SmartHome", "https://www.theverge.com/rss/smart-home/index.xml", "home"),
    ("HomeKit-News", "https://homekitnews.com/feed/", "home"),
    ("HomeAssistant", "https://www.home-assistant.io/atom.xml", "home"),
]


@dataclasses.dataclass(frozen=True)
class SourceSpec:
    name: str
    kind: str
    url: Optional[str] = None
    group: Optional[str] = None
    timeout_seconds: float = 10.0


@dataclasses.dataclass
class SourceResult:
    name: str
    status: str
    data: Any
    elapsed_ms: int
    error: Optional[str] = None
    cache_time: Optional[str] = None


def build_source_registry() -> list[SourceSpec]:
    specs = [SourceSpec("hot-aggregator", "aggregator", "http://127.0.0.1:6688/api/all", timeout_seconds=90)]
    specs.extend(SourceSpec(name, "rss", url, group, 10) for name, url, group in RSS_SOURCES)
    specs.append(SourceSpec("dongchedi-site-search", "car-search", group="dongchedi", timeout_seconds=35))
    specs.append(SourceSpec("daily-hot-autohome", "mcp-tool", timeout_seconds=20))
    specs.append(SourceSpec("vertical-auto-search", "car-search", group="supplement", timeout_seconds=45))
    specs.append(SourceSpec("product-experience", "product", timeout_seconds=90))
    return specs


def _cache_path(cache_dir: Path, name: str) -> Path:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "source"
    return cache_dir / f"{safe_name}.json"


def load_cache(cache_dir: Path, name: str) -> tuple[Any, Optional[str]]:
    path = _cache_path(cache_dir, name)
    if not path.exists():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("data"), payload.get("cached_at")
    except (OSError, ValueError, TypeError):
        return None, None


def save_cache(cache_dir: Path, name: str, data: Any) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_at = datetime.now(timezone.utc).isoformat()
    path = _cache_path(cache_dir, name)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps({"cached_at": cached_at, "data": data}, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(path)
    return cached_at


def resolve_result(
    name: str,
    live: Any,
    cached: Any,
    error: Optional[str],
    elapsed_ms: int,
    cache_time: Optional[str] = None,
) -> SourceResult:
    if live is not None:
        return SourceResult(name, "live", live, elapsed_ms, error)
    if cached is not None:
        return SourceResult(name, "cache", cached, elapsed_ms, error, cache_time)
    return SourceResult(name, "unavailable", None, elapsed_ms, error)


def run_source_batch(
    specs: Iterable[SourceSpec],
    fetcher: Callable[[SourceSpec, float], Any],
    cache_dir: Path,
    deadline_seconds: float,
) -> list[SourceResult]:
    specs = list(specs)
    started = time.monotonic()
    deadline = started + max(0.0, deadline_seconds)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(24, max(1, len(specs))))
    futures = {executor.submit(fetcher, spec, deadline): spec for spec in specs}
    done, pending = concurrent.futures.wait(futures, timeout=max(0.0, deadline - time.monotonic()))
    results: list[SourceResult] = []

    for future in done:
        spec = futures[future]
        elapsed_ms = int((time.monotonic() - started) * 1000)
        try:
            live = future.result()
            save_cache(cache_dir, spec.name, live)
            results.append(resolve_result(spec.name, live, None, None, elapsed_ms))
        except Exception as exc:  # noqa: BLE001 - source failures are isolated
            cached, cache_time = load_cache(cache_dir, spec.name)
            results.append(resolve_result(spec.name, None, cached, str(exc), elapsed_ms, cache_time))

    for future in pending:
        spec = futures[future]
        future.cancel()
        cached, cache_time = load_cache(cache_dir, spec.name)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        results.append(resolve_result(spec.name, None, cached, "global deadline exceeded", elapsed_ms, cache_time))

    executor.shutdown(wait=False, cancel_futures=True)
    return sorted(results, key=lambda result: result.name.lower())


def _fetch_json(url: str, timeout: float) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "content-pipeline/0.7"})
    with urllib.request.urlopen(request, timeout=max(0.2, timeout)) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_mcp_json(url: str, body: dict[str, Any], timeout: float, session_id: Optional[str] = None) -> tuple[dict[str, str], str]:
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=max(0.2, timeout)) as response:
        return dict(response.headers.items()), response.read().decode("utf-8", errors="ignore")


def _parse_sse_json(text: str) -> dict[str, Any]:
    for line in text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(text)


def call_daily_hot_tool(tool_name: str, timeout: float) -> Any:
    url = os.environ.get("DAILY_HOT_MCP_URL", "http://127.0.0.1:8000/mcp")
    headers, init_text = _post_mcp_json(
        url,
        {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "content-pipeline", "version": "1.0"},
            },
            "id": 1,
        },
        timeout,
    )
    session_id = headers.get("mcp-session-id") or headers.get("Mcp-Session-Id")
    if not session_id:
        raise RuntimeError(f"MCP initialize missing session id: {init_text[:200]}")
    _post_mcp_json(url, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, timeout, session_id)
    _, call_text = _post_mcp_json(
        url,
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": {"args": {}}},
            "id": 2,
        },
        timeout,
        session_id,
    )
    payload = _parse_sse_json(call_text)
    if payload.get("error"):
        raise RuntimeError(json.dumps(payload["error"], ensure_ascii=False))
    content = ((payload.get("result") or {}).get("content") or [])
    if not content:
        return []
    text = content[0].get("text", "")
    return json.loads(text)


def _text(node: Optional[ET.Element], *names: str) -> str:
    if node is None:
        return ""
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def fetch_rss(spec: SourceSpec, timeout: float) -> list[dict[str, Any]]:
    request = urllib.request.Request(spec.url or "", headers={"User-Agent": "Mozilla/5.0 content-pipeline/0.7"})
    with urllib.request.urlopen(request, timeout=max(0.2, timeout)) as response:
        root = ET.fromstring(response.read())

    items: list[dict[str, Any]] = []
    nodes = root.findall(".//item")
    if not nodes:
        nodes = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for node in nodes[:100]:
        title = _text(node, "title", "{http://www.w3.org/2005/Atom}title")
        description = _text(node, "description", "summary", "{http://www.w3.org/2005/Atom}summary")
        pub_date = _text(node, "pubDate", "updated", "{http://www.w3.org/2005/Atom}updated")
        link = _text(node, "link")
        if not link:
            link_node = node.find("{http://www.w3.org/2005/Atom}link")
            link = link_node.attrib.get("href", "") if link_node is not None else ""
        if title:
            items.append({"title": title, "desc": description[:500], "pubDate": pub_date, "link": link, "source": spec.name})
    return items


def ensure_hot_aggregator(url: str, workdir: Path, max_wait_seconds: float = 20.0) -> bool:
    try:
        _fetch_json(url, 3)
        return True
    except Exception:  # noqa: BLE001 - health probe controls fallback
        pass
    if not workdir.exists():
        return False
    subprocess.Popen(
        ["node", "--import", "tsx", "index.mjs"],
        cwd=str(workdir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + max_wait_seconds
    while time.monotonic() < deadline:
        time.sleep(1)
        try:
            _fetch_json(url, 3)
            return True
        except Exception:  # noqa: BLE001
            continue
    return False


def _product_python() -> str:
    configured = os.environ.get("HERMES_TOPICS_PYTHON")
    if configured:
        return configured
    hermes_python = Path.home() / ".hermes" / "hermes-agent" / ".venv" / "bin" / "python"
    return str(hermes_python) if hermes_python.exists() else sys.executable


def make_fetcher(output_dir: Path, script_dir: Path) -> Callable[[SourceSpec, float], Any]:
    product_dir = output_dir / "product-run"

    def fetch(spec: SourceSpec, deadline: float) -> Any:
        remaining = max(0.2, deadline - time.monotonic())
        timeout = min(spec.timeout_seconds, remaining)
        if spec.kind == "aggregator":
            return _fetch_json(spec.url or "", timeout)
        if spec.kind == "rss":
            return fetch_rss(spec, timeout)
        if spec.kind == "product":
            product_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    _product_python(),
                    str(script_dir / "smzdm_product_topics.py"),
                    "--output-dir",
                    str(product_dir),
                    "--limit-per-keyword",
                    "8",
                    "--max-rows",
                    "80",
                ],
                check=True,
                timeout=timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            return json.loads((product_dir / "smzdm_product_topics_items.json").read_text(encoding="utf-8"))
        if spec.kind == "car-search":
            output_path = output_dir / ("01d-dongchedi-site-search.json" if spec.group == "dongchedi" else "01d-vertical-auto-search.json")
            max_searches = "10" if spec.group == "dongchedi" else "12"
            command = [
                sys.executable,
                str(script_dir / "search_car_keywords.py"),
                "--output",
                str(output_path),
                "--max-searches",
                max_searches,
                "--max-vertical-brands",
                "8",
                "--limit-per-query",
                "3",
                "--timeout",
                "3",
                "--no-general-search",
            ]
            if spec.group == "dongchedi":
                command.extend(["--include-sites", "dongchedi.com"])
            elif spec.group == "supplement":
                command.extend(["--exclude-sites", "dongchedi.com"])
            subprocess.run(
                command,
                check=True,
                timeout=timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            return json.loads(output_path.read_text(encoding="utf-8"))
        if spec.kind == "mcp-tool":
            if spec.name == "daily-hot-autohome":
                return call_daily_hot_tool("get-autohome-trending", timeout)
            raise ValueError(f"unsupported mcp tool source: {spec.name}")
        raise ValueError(f"unsupported source kind: {spec.kind}")

    return fetch


def _manifest_entries(results: list[SourceResult]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for result in results:
        if result.name == "hot-aggregator" and isinstance(result.data, dict):
            for platform in result.data.get("data", []):
                status = result.status
                if status == "live" and platform.get("fromCache"):
                    status = "cache"
                entries.append(
                    {
                        "name": f"hot-aggregator:{platform.get('name', 'unknown')}",
                        "status": status,
                        "items": len(platform.get("data") or []),
                        "elapsed_ms": result.elapsed_ms,
                        "cache_time": result.data.get("updateTime") if status == "cache" else None,
                        "error": result.error,
                    }
                )
            continue
        if isinstance(result.data, list):
            count = len(result.data)
        elif isinstance(result.data, dict) and isinstance(result.data.get("results"), list):
            count = len(result.data["results"])
        else:
            count = int(result.data is not None)
        entries.append(
            {
                "name": result.name,
                "status": result.status,
                "items": count,
                "elapsed_ms": result.elapsed_ms,
                "cache_time": result.cache_time,
                "error": result.error,
            }
        )
    entries.append(
        {
            "name": "xiaohongshu-authenticated",
            "status": "disabled",
            "items": 0,
            "elapsed_ms": 0,
            "cache_time": None,
            "error": "禁止个人小红书登录态",
        }
    )
    return sorted(entries, key=lambda entry: entry["name"].lower())


def write_outputs(output_dir: Path, results: list[SourceResult], script_dir: Path, elapsed_seconds: float) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    by_name = {result.name: result for result in results}
    aggregator = by_name.get("hot-aggregator")
    aggregator_data = aggregator.data if aggregator and isinstance(aggregator.data, dict) else {"data": []}
    (output_dir / "01-hotspots-raw.json").write_text(json.dumps(aggregator_data, ensure_ascii=False, indent=2), encoding="utf-8")

    intl: list[dict[str, Any]] = []
    home: list[dict[str, Any]] = []
    groups = {name: group for name, _, group in RSS_SOURCES}
    for result in results:
        if not isinstance(result.data, list) or result.name not in groups:
            continue
        (home if groups[result.name] == "home" else intl).extend(result.data)
    intl_path = output_dir / "01-rss-intl.json"
    home_path = output_dir / "01-rss-home.json"
    intl_path.write_text(json.dumps(intl, ensure_ascii=False, indent=2), encoding="utf-8")
    home_path.write_text(json.dumps(home, ensure_ascii=False, indent=2), encoding="utf-8")

    dongchedi_result = by_name.get("dongchedi-site-search")
    car_search_result = by_name.get("vertical-auto-search")
    autohome_result = by_name.get("daily-hot-autohome")
    car_search_path = output_dir / "01d-vertical-auto-search.json"
    car_supplement_results: list[dict[str, Any]] = []
    if dongchedi_result and isinstance(dongchedi_result.data, dict):
        (output_dir / "01d-dongchedi-site-search.json").write_text(
            json.dumps(dongchedi_result.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        car_supplement_results.extend(dongchedi_result.data.get("results") or [])
    if car_search_result and isinstance(car_search_result.data, dict):
        car_supplement_results.extend(car_search_result.data.get("results") or [])
    if autohome_result and isinstance(autohome_result.data, list):
        (output_dir / "01e-autohome-trending.json").write_text(
            json.dumps(autohome_result.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        for item in autohome_result.data:
            car_supplement_results.append(
                {
                    "title": item.get("title", ""),
                    "snippet": item.get("desc", ""),
                    "source": item.get("source", "汽车之家"),
                    "url": item.get("url", ""),
                    "query": "daily-hot:get-autohome-trending",
                    "site": "autohome.com.cn",
                    "intent": item.get("category", "汽车之家热榜"),
                }
            )
    car_search_path.write_text(
        json.dumps(
            {
                "search_time": datetime.now(timezone.utc).isoformat(),
                "total_results": len(car_supplement_results),
                "results": car_supplement_results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    filter_proc = subprocess.run(
        [
            sys.executable,
            str(script_dir / "filter_all_categories.py"),
            str(output_dir / "01-hotspots-raw.json"),
            str(intl_path),
            str(home_path),
            str(output_dir),
            str(car_search_path),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )
    entries = _manifest_entries(results)
    counts = {status: sum(entry["status"] == status for entry in entries) for status in ("live", "cache", "unavailable", "disabled")}
    manifest = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "deadline_seconds": None,
        "source_count": len(entries),
        "status_counts": counts,
        "sources": entries,
    }
    (output_dir / "00-source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    source_summary = (
        f"# 两分钟全覆盖热点\n\n"
        f"- 总耗时：{elapsed_seconds:.1f} 秒\n"
        f"- 来源：{len(entries)}，实时 {counts['live']}，缓存 {counts['cache']}，不可用 {counts['unavailable']}，禁用 {counts['disabled']}\n\n"
    )
    (output_dir / "01-hotspots-raw.md").write_text(source_summary + filter_proc.stdout, encoding="utf-8")

    filtered_path = Path("/tmp/filtered_daily.json")
    if filtered_path.exists():
        shutil.copy2(filtered_path, output_dir / "01-hotspots-filtered.json")

    presentation_path = output_dir / "01-hotspots-presentation.json"
    presentation_valid = False
    if presentation_path.exists():
        try:
            presentation = json.loads(presentation_path.read_text(encoding="utf-8"))
            presentation_valid = bool((presentation.get("validation") or {}).get("valid"))
        except (OSError, ValueError, TypeError):
            presentation_valid = False
    manifest["presentation_valid"] = presentation_valid

    product_result = by_name.get("product-experience")
    product_dir = output_dir / "product-run"
    product_json_path = output_dir / "01b-product-experience.json"
    if product_result and product_result.data is not None:
        product_json_path.write_text(json.dumps(product_result.data, ensure_ascii=False, indent=2), encoding="utf-8")
        report = product_dir / "smzdm_product_topics_report.md"
        rows = product_dir / "smzdm_product_topics_rows.json"
        if report.exists():
            shutil.copy2(report, output_dir / "01b-product-experience.md")
        if rows.exists():
            shutil.copy2(rows, output_dir / "01b-product-experience-rows.json")

    shortlist_path = output_dir / "01c-screening-candidates.json"
    shortlist_valid = False
    shortlist_count = 0
    screening_script = script_dir.parent.parent / "screening-topics" / "scripts" / "prepare_screening_candidates.py"
    if presentation_valid and screening_script.exists():
        shortlist_proc = subprocess.run(
            [
                sys.executable,
                str(screening_script),
                "--input",
                str(presentation_path),
                "--output",
                str(shortlist_path),
                "--product-input",
                str(product_json_path),
                "--limit",
                "12",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=8,
        )
        if shortlist_proc.returncode == 0 and shortlist_path.exists():
            try:
                shortlist_payload = json.loads(shortlist_path.read_text(encoding="utf-8"))
                shortlist_count = len(shortlist_payload.get("candidates") or [])
                shortlist_valid = shortlist_count >= 5
            except (OSError, ValueError, TypeError):
                shortlist_valid = False
    manifest["screening_shortlist_valid"] = shortlist_valid
    manifest["screening_shortlist_count"] = shortlist_count

    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="/tmp/article-pipeline")
    parser.add_argument("--cache-dir", default=str(Path.home() / ".hermes" / "cache" / "content-pipeline"))
    parser.add_argument("--deadline-seconds", type=float, default=120.0)
    parser.add_argument("--aggregator-url", default="http://127.0.0.1:6688/api/all")
    parser.add_argument("--aggregator-dir", default=str(Path.home() / ".openclaw" / "workspace" / "hot-aggregator"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir)
    script_dir = Path(__file__).resolve().parent
    registry = build_source_registry()
    registry[0] = dataclasses.replace(registry[0], url=args.aggregator_url)
    ensure_hot_aggregator(args.aggregator_url, Path(args.aggregator_dir), min(20.0, args.deadline_seconds / 4))
    reserve = min(8.0, args.deadline_seconds / 10)
    remaining = max(0.1, args.deadline_seconds - (time.monotonic() - started) - reserve)
    results = run_source_batch(registry, make_fetcher(output_dir, script_dir), cache_dir, remaining)
    elapsed = time.monotonic() - started
    manifest = write_outputs(output_dir, results, script_dir, elapsed)
    manifest["deadline_seconds"] = args.deadline_seconds
    (output_dir / "00-source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = (
        elapsed <= args.deadline_seconds
        and bool(manifest.get("presentation_valid"))
        and bool(manifest.get("screening_shortlist_valid"))
    )
    print(json.dumps({"ok": ok, **manifest}, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
