#!/usr/bin/env python3
"""Build a compact, deterministic shortlist for semantic topic screening."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


CATEGORY_LABELS = {
    'social_livelihood': '社会/民生',
    'international_politics': '国际/政治',
    'finance_policy': '财经/政策',
    'sports': '体育',
    'entertainment': '文娱',
    'health': '健康',
    'technology_ai': '科技/AI',
    'other': '其他爆点',
    'auto': '汽车',
    '3c': '3C数码',
    'smart_home': '智能家居',
}

BRANDS = (
    '小米', '小鹏', '理想', '蔚来', '比亚迪', '阿维塔', '华为', '荣耀', '苹果',
    '三星', 'OPPO', 'vivo', '零跑', '特斯拉', '问界', '智界', '极氪', '戴森',
    'Dyson', 'Shark', '科沃斯', '米家', '安克', 'Robot Phone',
)
GENERIC_ENTITIES = {'ai', 'apple', 'iphone', 'huawei', 'xiaomi', 'robot', 'phone', 'pro', 'max', 'ultra'}


def normalized_title(title: str) -> str:
    return re.sub(r'[^0-9a-z\u4e00-\u9fff]+', '', title.lower())


def specific_entities(title: str) -> set[str]:
    compact = re.sub(r'(?i)(iphone|mate|pura|model|galaxy|redmi)\s+', r'\1', title)
    tokens = set(re.findall(r'(?i)(?:[a-z]+[0-9][a-z0-9+-]*|[0-9]+[a-z][a-z0-9+-]*)', compact))
    tokens.update(re.findall(r'(?i)\b(?:openpods|apple\s*music|robot\s*phone|deebot\s*x?\d+)\b', title))
    return {re.sub(r'\s+', '', token.lower()) for token in tokens if token.lower() not in GENERIC_ENTITIES}


def same_event(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get('url') and left.get('url') == right.get('url'):
        return True
    a = normalized_title(str(left.get('title') or ''))
    b = normalized_title(str(right.get('title') or ''))
    if not a or not b:
        return False
    if specific_entities(str(left.get('title') or '')) & specific_entities(str(right.get('title') or '')):
        return True
    left_numbers = set(re.findall(r'\d+', a))
    right_numbers = set(re.findall(r'\d+', b))
    if left_numbers and right_numbers and left_numbers != right_numbers:
        return False
    shorter, longer = sorted((a, b), key=len)
    return (len(shorter) >= 10 and shorter in longer) or SequenceMatcher(None, a, b).ratio() >= 0.78


def heat_score(item: dict[str, Any]) -> int:
    platforms = int(item.get('platform_count') or 1)
    best_rank = int(item.get('best_rank') or item.get('rank') or 100)
    if platforms >= 5 or (platforms >= 3 and best_rank <= 10):
        return 5
    if platforms >= 3:
        return 4
    if platforms == 2:
        return 3
    return 3 if best_rank <= 10 else 2


def freshness_score(item: dict[str, Any]) -> int | None:
    if not item.get('freshness_gate_pass'):
        return None
    age = item.get('age_hours')
    if age is None:
        return 5 if item.get('evidence_type') == 'hot_rank' else None
    age = float(age)
    if age <= 24:
        return 5
    if age <= 48:
        return 4
    return None


def discussion_score(item: dict[str, Any]) -> int:
    platforms = int(item.get('platform_count') or 1)
    if platforms >= 5:
        return 5
    if platforms >= 3:
        return 4
    if platforms == 2:
        return 3
    return 2


def detect_brand(item: dict[str, Any]) -> str:
    explicit = item.get('brands') or []
    if explicit and explicit[0] != '趋势':
        return str(explicit[0])
    title = str(item.get('title') or '')
    return next((brand for brand in BRANDS if brand.lower() in title.lower()), '')


def flatten(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category, items in (payload.get('full_web') or {}).items():
        for item in items or []:
            rows.append({**item, 'layer': 'full_web', 'category': category})
    for category, items in (payload.get('focus') or {}).items():
        for item in items or []:
            rows.append({**item, 'layer': 'focus', 'category': category})
    return rows


def prepare(payload: dict[str, Any], limit: int = 20) -> dict[str, Any]:
    run_material = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')
    run_id = hashlib.sha256(run_material).hexdigest()[:16]
    eligible: list[dict[str, Any]] = []
    rejected_freshness = 0
    for item in flatten(payload):
        freshness = freshness_score(item)
        if freshness is None:
            rejected_freshness += 1
            continue
        heat = heat_score(item)
        discussion = discussion_score(item)
        candidate = {
            'candidate_id': '',
            'title': item.get('title') or '',
            'url': item.get('url') or '',
            'source': item.get('source') or '',
            'layer': item['layer'],
            'category': item['category'],
            'category_label': CATEGORY_LABELS.get(item['category'], item['category']),
            'brand': detect_brand(item),
            'platform_count': int(item.get('platform_count') or 1),
            'published_at': item.get('published_at'),
            'age_hours': item.get('age_hours'),
            'freshness_status': item.get('freshness_status'),
            'heat_score': heat,
            'freshness_score': freshness,
            'discussion_score': discussion,
            'fixed_subtotal': (heat + freshness + discussion) * 2,
        }
        match = next((existing for existing in eligible if same_event(existing, candidate)), None)
        if match:
            if candidate['fixed_subtotal'] > match['fixed_subtotal']:
                eligible[eligible.index(match)] = candidate
            continue
        eligible.append(candidate)

    eligible.sort(
        key=lambda item: (
            item['fixed_subtotal'], item['platform_count'], item['layer'] == 'focus'
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    focus_quotas = {'auto': 4, '3c': 3, 'smart_home': 2}
    for category, quota in focus_quotas.items():
        selected.extend([item for item in eligible if item['category'] == category][:quota])

    full_web_counts: dict[str, int] = {}
    full_web_limit = min(6, max(0, limit - len(selected)))
    for item in eligible:
        if item['layer'] != 'full_web' or item in selected:
            continue
        category = item['category']
        if full_web_counts.get(category, 0) >= 2:
            continue
        selected.append(item)
        full_web_counts[category] = full_web_counts.get(category, 0) + 1
        if sum(candidate['layer'] == 'full_web' for candidate in selected) >= full_web_limit:
            break

    caps = {'auto': 6, '3c': 5, 'smart_home': 4}
    for item in eligible:
        if item in selected:
            continue
        category_count = sum(candidate['category'] == item['category'] for candidate in selected)
        if category_count >= caps.get(item['category'], 3):
            continue
        selected.append(item)
        if len(selected) >= limit:
            break

    selected = selected[:limit]
    selected.sort(
        key=lambda item: (
            item['fixed_subtotal'], item['platform_count'], item['layer'] == 'focus'
        ),
        reverse=True,
    )

    for index, item in enumerate(selected, 1):
        item['candidate_id'] = f'C{index:02d}'

    return {
        'schema_version': 2,
        'run_id': run_id,
        'source_generated_at': payload.get('generated_at'),
        'scoring_boundary': {
            'code_scores': ['heat_score', 'freshness_score', 'discussion_score'],
            'model_scores': ['emotion_score', 'relevance_score'],
            'total_formula': '(heat + freshness + discussion + emotion + relevance) * 2',
        },
        'stats': {
            'input_count': len(flatten(payload)),
            'freshness_rejected': rejected_freshness,
            'eligible_after_dedup': len(eligible),
            'shortlist_count': len(selected),
        },
        'candidates': selected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='/tmp/article-pipeline/01-hotspots-presentation.json')
    parser.add_argument('--output', default='/tmp/article-pipeline/01c-screening-candidates.json')
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    result = prepare(payload, max(5, min(args.limit, 30)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result['stats'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
