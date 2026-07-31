#!/usr/bin/env python3
"""Merge semantic judgments with deterministic scores and render recommendations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TEXT = (
    'core_judgment',
    'recommended_angle',
    'risk',
    'reader_start',
    'line_reason',
    'next_stage_requirement',
)
CONTENT_LINES = {
    'hot_take': '热点观点线',
    'decision': '消费决策线',
    'framework': '长期框架线',
}


def level_for(score: int) -> str:
    if score >= 40:
        return 'S级'
    if score >= 30:
        return 'A级'
    if score >= 20:
        return 'B级/储备'
    return '不推荐'


def valid_judgment(judgment: dict[str, Any]) -> bool:
    try:
        scores_valid = all(1 <= int(judgment[name]) <= 5 for name in ('emotion_score', 'relevance_score'))
        asset_valid = 1 <= int(judgment.get('asset_value')) <= 5
    except (KeyError, TypeError, ValueError):
        return False
    content_line = str(judgment.get('content_line') or '')
    return (
        scores_valid
        and asset_valid
        and content_line in CONTENT_LINES
        and all(str(judgment.get(name) or '').strip() for name in REQUIRED_TEXT)
    )


def finalize(candidates_payload: dict[str, Any], judgments_payload: dict[str, Any], maximum: int = 10) -> dict[str, Any]:
    candidate_run_id = str(candidates_payload.get('run_id') or '')
    judgment_run_id = str(judgments_payload.get('run_id') or '') if isinstance(judgments_payload, dict) else ''
    if not candidate_run_id or judgment_run_id != candidate_run_id:
        return {
            'schema_version': 2,
            'run_id': candidate_run_id,
            'contract_error': 'model judgments run_id does not match current candidates',
            'stats': {
                'candidate_count': len(candidates_payload.get('candidates') or []),
                'valid_model_judgments': 0,
                'formal_recommendation_count': 0,
                'minimum_met': False,
            },
            'recommendations': [],
            'reserve': [],
        }
    judgments = judgments_payload.get('judgments') if isinstance(judgments_payload, dict) else judgments_payload
    by_id = {
        str(item.get('candidate_id')): item
        for item in (judgments or [])
        if isinstance(item, dict) and valid_judgment(item)
    }
    merged: list[dict[str, Any]] = []
    for candidate in candidates_payload.get('candidates') or []:
        judgment = by_id.get(str(candidate.get('candidate_id')))
        if not judgment:
            continue
        emotion = int(judgment['emotion_score'])
        relevance = int(judgment['relevance_score'])
        dimensions = {
            'heat': int(candidate['heat_score']),
            'freshness': int(candidate['freshness_score']),
            'discussion': int(candidate['discussion_score']),
            'emotion': emotion,
            'relevance': relevance,
        }
        total = sum(dimensions.values()) * 2
        merged.append({
            **candidate,
            **{key: judgment[key] for key in REQUIRED_TEXT},
            'content_line': judgment['content_line'],
            'content_line_label': CONTENT_LINES[judgment['content_line']],
            'asset_value': int(judgment.get('asset_value') or 0),
            'six_question_pass_count': int(judgment.get('six_question_pass_count') or 0),
            'dimensions': dimensions,
            'writing_value_score': total,
            'level': level_for(total),
        })

    merged.sort(key=lambda item: (item['writing_value_score'], item['platform_count']), reverse=True)
    formal = [
        item for item in merged
        if item['writing_value_score'] >= 30
        and item['dimensions']['relevance'] >= 3
        and item['recommended_angle'].strip() != '不适用'
    ]
    target = min(maximum, len(formal))
    brand_counts: dict[str, int] = {}
    eligible_by_brand: list[dict[str, Any]] = []
    for item in formal:
        brand = item.get('brand') or ''
        if brand and brand_counts.get(brand, 0) >= 2:
            continue
        eligible_by_brand.append(item)
        if brand:
            brand_counts[brand] = brand_counts.get(brand, 0) + 1

    focus = [item for item in eligible_by_brand if item.get('layer') == 'focus']
    full_web = [item for item in eligible_by_brand if item.get('layer') == 'full_web']
    full_web_slots = min(3, len(full_web), max(0, target - min(5, len(focus))))
    focus_slots = target - full_web_slots
    selected = []
    auto_cap = target // 2
    for item in focus:
        if item.get('category') == 'auto' and sum(row.get('category') == 'auto' for row in selected) >= auto_cap:
            continue
        selected.append(item)
        if len(selected) >= focus_slots:
            break
    selected.extend(full_web[:full_web_slots])
    for item in eligible_by_brand:
        if item in selected or len(selected) >= target:
            continue
        if item.get('category') == 'auto' and sum(row.get('category') == 'auto' for row in selected) >= auto_cap:
            continue
        selected.append(item)
    while sum(item.get('category') == 'auto' for item in selected) > len(selected) // 2:
        lowest_auto = next(item for item in reversed(selected) if item.get('category') == 'auto')
        selected.remove(lowest_auto)
    selected.sort(key=lambda item: (item['writing_value_score'], item['platform_count']), reverse=True)

    reserve = [item for item in merged if item not in selected and item['writing_value_score'] >= 20][:3]
    return {
        'schema_version': 2,
        'run_id': candidate_run_id,
        'stats': {
            'candidate_count': len(candidates_payload.get('candidates') or []),
            'valid_model_judgments': len(by_id),
            'formal_recommendation_count': len(selected),
            'minimum_met': len(selected) >= 5,
            'content_line_counts': {
                line: sum(item.get('content_line') == line for item in selected)
                for line in CONTENT_LINES
            },
        },
        'recommendations': selected,
        'reserve': reserve,
    }


def render_markdown(result: dict[str, Any]) -> str:
    recommendations = result['recommendations']
    lines = ['# 选题建议', '']
    if recommendations:
        lines.append(f"结论：今天优先写《{recommendations[0]['title']}》。")
    else:
        lines.append('结论：本轮没有完成语义判断的合格选题。')
    if result.get('contract_error'):
        lines.extend(['', f"> 契约校验失败：{result['contract_error']}。拒绝复用上一轮模型判断。"])
    lines.extend(['', f"正式推荐 {len(recommendations)} 条，按内容线分组：", ''])
    for line, label in CONTENT_LINES.items():
        group = [item for item in recommendations if item.get('content_line') == line]
        lines.extend([f"## {label}（{len(group)} 条）", ''])
        if not group:
            lines.extend(['- 本轮没有足够强的候选题。', ''])
            continue
        for index, item in enumerate(group, 1):
            d = item['dimensions']
            lines.extend([
                f"### {index}. {item['title']} — {item['writing_value_score']}/50 — {item['level']}",
                '',
                f"- 五维：全网热度 {d['heat']}，时效性 {d['freshness']}，讨论热度 {d['discussion']}，情绪强度 {d['emotion']}，内容关联度 {d['relevance']}",
                f"- 内容线判断：{item['content_line_label']}，{item['line_reason']}",
                f"- 账号资产价值：{item['asset_value']}/5",
                f"- 核心判断：{item['core_judgment']}",
                f"- 推荐角度：{item['recommended_angle']}",
                f"- 反面理由：{item['risk']}",
                f"- 读者起点：{item['reader_start']}",
                f"- 下一步要求：{item['next_stage_requirement']}",
                f"- 原文：{item['url']}",
                '',
            ])
    if result['reserve']:
        lines.extend(['## 储备', ''])
        for item in result['reserve']:
            lines.append(f"- {item['title']} — {item['writing_value_score']}/50 — {item['level']}")
        lines.append('')
    if not result['stats']['minimum_met']:
        lines.append(f"> 本轮完整合格候选不足 5 条，实际 {len(recommendations)} 条；未用旧题或不完整判断凑数。")
    return '\n'.join(lines).rstrip() + '\n'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidates', default='/tmp/article-pipeline/01c-screening-candidates.json')
    parser.add_argument('--judgments', default='/tmp/article-pipeline/02a-model-judgments.json')
    parser.add_argument('--output-json', default='/tmp/article-pipeline/02-topic-suggestion.json')
    parser.add_argument('--output-md', default='/tmp/article-pipeline/02-topic-suggestion.md')
    parser.add_argument('--maximum', type=int, default=10)
    args = parser.parse_args()
    candidates = json.loads(Path(args.candidates).read_text(encoding='utf-8'))
    judgments = json.loads(Path(args.judgments).read_text(encoding='utf-8'))
    result = finalize(candidates, judgments, max(5, min(args.maximum, 10)))
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    output_md.write_text(render_markdown(result), encoding='utf-8')
    print(json.dumps(result['stats'], ensure_ascii=False))
    return 0 if result['stats']['minimum_met'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
