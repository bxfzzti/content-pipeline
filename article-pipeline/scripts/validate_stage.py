#!/usr/bin/env python3
"""Validate deterministic content-pipeline stage contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_hotspots(root: Path) -> list[str]:
    errors: list[str] = []
    json_path = root / '01-hotspots-presentation.json'
    markdown_path = root / '01-hotspots-presentation.md'
    if not json_path.is_file():
        return [f'missing: {json_path}']
    if not markdown_path.is_file():
        return [f'missing: {markdown_path}']

    try:
        payload = json.loads(json_path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return [f'invalid json: {exc}']

    if payload.get('display_order') != ['full_web', 'focus']:
        errors.append('display_order must be full_web then focus')
    full_web = payload.get('full_web')
    focus = payload.get('focus')
    if not isinstance(full_web, dict):
        errors.append('full_web must be an object')
    elif sum(bool(items) for items in full_web.values()) < 2:
        errors.append('full_web must contain at least two non-empty categories')
    if not isinstance(focus, dict) or list(focus) != ['auto', '3c', 'smart_home']:
        errors.append('focus keys must be auto, 3c, smart_home')

    markdown = markdown_path.read_text(encoding='utf-8')
    full_pos = markdown.find('# 第一部分：全网热点')
    focus_pos = markdown.find('# 第二部分：我关注的方向')
    if full_pos < 0 or focus_pos < 0 or full_pos >= focus_pos:
        errors.append('markdown must show full-web hotspots before focus areas')
    shortlist = root / '01c-screening-candidates.json'
    if not shortlist.is_file():
        errors.append(f'missing: {shortlist}')
    else:
        try:
            shortlist_payload = json.loads(shortlist.read_text(encoding='utf-8'))
            if len(shortlist_payload.get('candidates') or []) < 5:
                errors.append('screening shortlist must contain at least five candidates')
        except (OSError, ValueError) as exc:
            errors.append(f'invalid screening shortlist: {exc}')
    return errors


def validate_screening(root: Path) -> list[str]:
    errors = validate_hotspots(root)
    suggestion = root / '02-topic-suggestion.md'
    suggestion_json = root / '02-topic-suggestion.json'
    if not suggestion.is_file() or suggestion.stat().st_size == 0:
        errors.append(f'missing or empty: {suggestion}')
    if not suggestion_json.is_file():
        errors.append(f'missing: {suggestion_json}')
    else:
        try:
            payload = json.loads(suggestion_json.read_text(encoding='utf-8'))
            if not (payload.get('stats') or {}).get('minimum_met'):
                errors.append('screening must contain at least five complete recommendations')
            for item in payload.get('recommendations') or []:
                dimensions = item.get('dimensions') or {}
                expected = sum(int(value) for value in dimensions.values()) * 2
                if expected != item.get('writing_value_score'):
                    errors.append(f"score mismatch: {item.get('candidate_id')}")
                if item.get('content_line') not in {'hot_take', 'decision', 'framework'}:
                    errors.append(f"missing content_line: {item.get('candidate_id')}")
                if not item.get('line_reason'):
                    errors.append(f"missing line_reason: {item.get('candidate_id')}")
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f'invalid screening json: {exc}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('hotspots', 'screening'))
    parser.add_argument('--root', default='/tmp/article-pipeline')
    args = parser.parse_args()
    root = Path(args.root)
    errors = validate_hotspots(root) if args.stage == 'hotspots' else validate_screening(root)
    print(json.dumps({'ok': not errors, 'stage': args.stage, 'errors': errors}, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == '__main__':
    raise SystemExit(main())
