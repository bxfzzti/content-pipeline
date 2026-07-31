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

CONTENT_LINES = {
    'hot_take': '热点观点线',
    'decision': '消费决策线',
    'framework': '长期框架线',
}

BRANDS = (
    '小米', '小鹏', '理想', '蔚来', '比亚迪', '阿维塔', '华为', '荣耀', '苹果',
    '三星', 'OPPO', 'vivo', '零跑', '特斯拉', '问界', '智界', '极氪', '戴森',
    'Dyson', 'Shark', '科沃斯', '米家', '安克', 'Robot Phone',
)
GENERIC_ENTITIES = {'ai', 'apple', 'iphone', 'huawei', 'xiaomi', 'robot', 'phone', 'pro', 'max', 'ultra'}

DECISION_TERMS = (
    '买', '选', '值不值', '值得买', '避坑', '体验', '横评', '对比', '预算',
    '价格', '配置', '适合', '不适合', '谁该', '谁不该', '怎么选',
)

FRAMEWORK_TERMS = (
    '框架', '方法', '清单', '五问', '四象限', '怎么判断', '判断标准', '话术翻译',
    '决策模型', '选择逻辑', '选车逻辑', '买车逻辑', '家庭用户', '预算分层',
)

AUTO_PRODUCT_TERMS = (
    '车型', '新车', '上市', '发布', '预售', '价格', '售价', '续航', '智驾', '座舱',
    '底盘', '配置', '试驾', '车主', '增程', '纯电', '混动', 'SUV', 'MPV', '轿车',
    '买', '选', '对比', '横评', '体验',
)

AUTO_INDUSTRY_TERMS = (
    '营收', '利润', '利润率', '财报', '销量', '交付', '裁员', '工厂', '供应链',
    '战略', '转型', '押注', '行业', '合作', '投资', '融资',
)


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
        if item.get('evidence_type') == 'hot_rank':
            return 5
        if item.get('evidence_type') == 'search_index':
            return 3
        return None
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


def default_content_line(item: dict[str, Any]) -> str:
    text = ' '.join(str(item.get(key) or '') for key in ('title', 'desc', 'summary', 'category_label'))
    if any(term in text for term in FRAMEWORK_TERMS):
        return 'framework'
    if item.get('candidate_type') == 'product_experience':
        return 'decision'
    if item.get('category') == 'auto':
        if any(term in text for term in AUTO_PRODUCT_TERMS):
            return 'decision'
        if any(term in text for term in AUTO_INDUSTRY_TERMS):
            return 'hot_take'
        return 'decision'
    if item.get('category') in {'3c', 'smart_home'} or any(term in text for term in DECISION_TERMS):
        return 'decision'
    return 'hot_take'


def product_category(item: dict[str, Any]) -> str:
    text = ' '.join(str(item.get(key) or '') for key in ('title', '_keyword', '_group', 'content_type'))
    if any(term in text for term in ('洗地机', '咖啡机', '扫地机器人', '空气净化器', '空调', '冰箱', '浴霸', '智能门锁')):
        return 'smart_home'
    return '3c'


def score_from_product(item: dict[str, Any]) -> tuple[int, int, int]:
    creative = int(item.get('creative_score') or item.get('match_score') or 0)
    engagement = sum(int(item.get(key) or 0) for key in ('comment_count', 'collection_count', 'up_count'))
    heat = 5 if creative >= 90 else 4 if creative >= 80 else 3 if creative >= 70 else 2
    freshness = 4
    discussion = 5 if engagement >= 300 else 4 if engagement >= 80 else 3 if engagement >= 20 else 2
    return heat, freshness, discussion


def product_candidates(product_items: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    ranked = sorted(
        (item for item in product_items if isinstance(item, dict)),
        key=lambda item: int(item.get('creative_score') or item.get('match_score') or 0),
        reverse=True,
    )
    for item in ranked:
        key = item.get('link') or item.get('title')
        if not key or key in seen:
            continue
        seen.add(key)
        category = product_category(item)
        heat, freshness, discussion = score_from_product(item)
        candidate = {
            'candidate_id': '',
            'candidate_type': 'product_experience',
            'title': item.get('title') or '',
            'url': item.get('link') or '',
            'source': item.get('platform') or item.get('source') or '产品体验源',
            'layer': 'focus',
            'category': category,
            'category_label': CATEGORY_LABELS.get(category, category),
            'brand': detect_brand(item),
            'platform_count': 1,
            'published_at': item.get('publish_time'),
            'age_hours': None,
            'freshness_status': '产品体验池（发布时间需点开核验）',
            'heat_score': heat,
            'freshness_score': freshness,
            'discussion_score': discussion,
            'fixed_subtotal': (heat + freshness + discussion) * 2,
            'default_content_line': 'decision',
            'default_content_line_label': CONTENT_LINES['decision'],
            'line_hint': '产品体验、开箱、横评、吐槽默认优先评估为消费决策线。',
            'product_keyword': item.get('_keyword') or '',
            'product_content_type': item.get('content_type') or '',
            'creative_score': item.get('creative_score'),
        }
        selected.append(candidate)
        if len(selected) >= limit:
            break
    return selected


def flatten(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category, items in (payload.get('full_web') or {}).items():
        for item in items or []:
            rows.append({**item, 'layer': 'full_web', 'category': category})
    for category, items in (payload.get('focus') or {}).items():
        for item in items or []:
            rows.append({**item, 'layer': 'focus', 'category': category})
    return rows


def prepare(payload: dict[str, Any], limit: int = 20, product_items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    product_items = product_items or []
    run_material = json.dumps(
        {'hotspots': payload, 'products': product_items[:20]},
        ensure_ascii=False,
        sort_keys=True,
    ).encode('utf-8')
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
            'candidate_type': 'hotspot',
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
        line = default_content_line(candidate)
        candidate['default_content_line'] = line
        candidate['default_content_line_label'] = CONTENT_LINES[line]
        candidate['line_hint'] = '系统默认分流，最终以模型语义判断为准。'
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

    products = product_candidates(product_items, limit=6)
    product_target = min(len(products), max(1, min(3, limit // 4))) if products else 0
    for item in products[:product_target]:
        if any(same_event(existing, item) for existing in selected):
            continue
        if len(selected) >= limit:
            removable_index = next(
                (
                    index for index in range(len(selected) - 1, -1, -1)
                    if selected[index].get('candidate_type') != 'product_experience'
                ),
                None,
            )
            if removable_index is None:
                break
            selected.pop(removable_index)
        selected.append(item)

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
            'model_scores': ['emotion_score', 'relevance_score', 'content_line', 'asset_value'],
            'total_formula': '(heat + freshness + discussion + emotion + relevance) * 2',
        },
        'stats': {
            'input_count': len(flatten(payload)),
            'freshness_rejected': rejected_freshness,
            'eligible_after_dedup': len(eligible),
            'shortlist_count': len(selected),
            'product_candidate_count': sum(item.get('candidate_type') == 'product_experience' for item in selected),
        },
        'candidates': selected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='/tmp/article-pipeline/01-hotspots-presentation.json')
    parser.add_argument('--output', default='/tmp/article-pipeline/01c-screening-candidates.json')
    parser.add_argument('--product-input', default='/tmp/article-pipeline/01b-product-experience.json')
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    product_items: list[dict[str, Any]] = []
    product_path = Path(args.product_input)
    if product_path.exists():
        product_payload = json.loads(product_path.read_text(encoding='utf-8'))
        if isinstance(product_payload, list):
            product_items = product_payload
    result = prepare(payload, max(5, min(args.limit, 30)), product_items)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result['stats'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
