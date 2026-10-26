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
    'next_stage_requirement',
)
CONTENT_LINES = {
    'hot_take': '热点观点线',
    'decision': '消费决策线',
    'experience': '经验沉淀线',
}
LEGACY_LINE_ALIASES = {'framework': 'experience'}
LINE_TIE_PRIORITY = {'decision': 3, 'hot_take': 2, 'experience': 1}

LINE_WEIGHTS = {
    'hot_take': {
        'heat': 0.25,
        'freshness': 0.25,
        'discussion': 0.20,
        'emotion': 0.20,
        'sharpness': 0.10,
    },
    'decision': {
        'purchase_confusion': 0.25,
        'choice_cost': 0.20,
        'evidence': 0.20,
        'actionability': 0.25,
        'save_value': 0.10,
    },
    'experience': {
        'reusability': 0.25,
        'step_clarity': 0.20,
        'operability': 0.20,
        'case_transfer': 0.20,
        'long_tail': 0.15,
    },
}


def level_for(score: int) -> str:
    if score >= 80:
        return 'S级'
    if score >= 65:
        return 'A级'
    if score >= 50:
        return 'B级/储备'
    return '不推荐'


def normalize_line(line: Any) -> str:
    value = str(line or '')
    return LEGACY_LINE_ALIASES.get(value, value)


def int_score(value: Any) -> int:
    score = int(value)
    if not 1 <= score <= 5:
        raise ValueError('score out of range')
    return score


def score_from_factors(factors: dict[str, int], weights: dict[str, float]) -> int:
    total = sum((factors[name] / 5) * weight * 100 for name, weight in weights.items())
    return int(round(total))


def nested_scores(payload: dict[str, Any], key: str, names: tuple[str, ...]) -> dict[str, int]:
    group = payload.get(key)
    if not isinstance(group, dict):
        raise ValueError(f'missing {key}')
    return {name: int_score(group[name]) for name in names}


def compute_line_scores(candidate: dict[str, Any], judgment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    hot_take_factors = {
        'heat': int_score(candidate['heat_score']),
        'freshness': int_score(candidate['freshness_score']),
        'discussion': int_score(candidate['discussion_score']),
        'emotion': int_score(judgment['emotion_score']),
        **nested_scores(judgment, 'hot_take_factors', ('sharpness',)),
    }
    decision_factors = nested_scores(
        judgment,
        'decision_factors',
        ('purchase_confusion', 'choice_cost', 'evidence', 'actionability', 'save_value'),
    )
    experience_factors = nested_scores(
        judgment,
        'experience_factors',
        ('reusability', 'step_clarity', 'operability', 'case_transfer', 'long_tail'),
    )
    return {
        'hot_take': {
            'score': score_from_factors(hot_take_factors, LINE_WEIGHTS['hot_take']),
            'factors': hot_take_factors,
            'weights': LINE_WEIGHTS['hot_take'],
        },
        'decision': {
            'score': score_from_factors(decision_factors, LINE_WEIGHTS['decision']),
            'factors': decision_factors,
            'weights': LINE_WEIGHTS['decision'],
        },
        'experience': {
            'score': score_from_factors(experience_factors, LINE_WEIGHTS['experience']),
            'factors': experience_factors,
            'weights': LINE_WEIGHTS['experience'],
        },
    }


def choose_primary_line(line_scores: dict[str, dict[str, Any]]) -> str:
    return max(
        line_scores,
        key=lambda line: (int(line_scores[line]['score']), LINE_TIE_PRIORITY[line]),
    )


def factor_summary(line: str, factors: dict[str, int]) -> str:
    if line == 'hot_take':
        names = ('heat', 'freshness', 'discussion', 'emotion', 'sharpness')
    elif line == 'decision':
        names = ('purchase_confusion', 'choice_cost', 'evidence', 'actionability', 'save_value')
    else:
        names = ('reusability', 'step_clarity', 'operability', 'case_transfer', 'long_tail')
    return '、'.join(f'{name}={factors[name]}' for name in names if name in factors)


def computed_line_reason(primary_line: str, line_scores: dict[str, dict[str, Any]]) -> str:
    score = int(line_scores[primary_line]['score'])
    factors = line_scores[primary_line]['factors']
    return f"按三线权重复算，{CONTENT_LINES[primary_line]}得分最高（{score}/100），关键因子是 {factor_summary(primary_line, factors)}。"


def computed_line_tradeoff(primary_line: str, line_scores: dict[str, dict[str, Any]]) -> str:
    ordered = sorted(
        line_scores.items(),
        key=lambda pair: (int(pair[1]['score']), LINE_TIE_PRIORITY[pair[0]]),
        reverse=True,
    )
    if len(ordered) < 2:
        return '只有一条内容线完成评分，按最高分进入主线。'
    second_line, second_data = ordered[1]
    primary_score = int(line_scores[primary_line]['score'])
    second_score = int(second_data['score'])
    gap = primary_score - second_score
    if gap <= 5:
        return f"与{CONTENT_LINES[second_line]}只差 {gap} 分，主线按得分和并列优先级确定，副线可作为备选角度。"
    return f"比{CONTENT_LINES[second_line]}高 {gap} 分，说明这条选题当前最适合按{CONTENT_LINES[primary_line]}生产。"


def valid_judgment(judgment: dict[str, Any]) -> bool:
    try:
        int_score(judgment['emotion_score'])
        int_score(judgment['relevance_score'])
        int_score(judgment.get('asset_value'))
        nested_scores(judgment, 'hot_take_factors', ('sharpness',))
        nested_scores(
            judgment,
            'decision_factors',
            ('purchase_confusion', 'choice_cost', 'evidence', 'actionability', 'save_value'),
        )
        nested_scores(
            judgment,
            'experience_factors',
            ('reusability', 'step_clarity', 'operability', 'case_transfer', 'long_tail'),
        )
    except (KeyError, TypeError, ValueError):
        return False
    content_line = normalize_line(judgment.get('content_line'))
    line_reasons = judgment.get('line_reasons') or {}
    return (
        content_line in CONTENT_LINES
        and all(str(judgment.get(name) or '').strip() for name in REQUIRED_TEXT)
        and isinstance(line_reasons, dict)
        and all(str(line_reasons.get(line) or '').strip() for line in CONTENT_LINES)
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
        line_scores = compute_line_scores(candidate, judgment)
        primary_line = choose_primary_line(line_scores)
        primary_score = int(line_scores[primary_line]['score'])
        secondary_lines = [
            line for line, data in sorted(
                line_scores.items(),
                key=lambda pair: int(pair[1]['score']),
                reverse=True,
            )
            if line != primary_line and int(data['score']) >= 70 and primary_score - int(data['score']) <= 15
        ]
        line_reasons = judgment.get('line_reasons') or {}
        merged.append({
            **candidate,
            **{key: judgment[key] for key in REQUIRED_TEXT},
            'content_line': primary_line,
            'content_line_label': CONTENT_LINES[primary_line],
            'model_content_line': normalize_line(judgment.get('content_line')),
            'secondary_content_lines': secondary_lines,
            'line_scores': line_scores,
            'line_reason': computed_line_reason(primary_line, line_scores),
            'model_line_reason': line_reasons[primary_line],
            'line_tradeoff': computed_line_tradeoff(primary_line, line_scores),
            'model_line_tradeoff': judgment.get('line_tradeoff') or '',
            'asset_value': int(judgment.get('asset_value') or 0),
            'relevance_score': int(judgment.get('relevance_score') or 0),
            'six_question_pass_count': int(judgment.get('six_question_pass_count') or 0),
            'dimensions': line_scores[primary_line]['factors'],
            'writing_value_score': primary_score,
            'score_scale': 100,
            'level': level_for(primary_score),
        })

    merged.sort(key=lambda item: (item['writing_value_score'], item['platform_count']), reverse=True)
    formal = [
        item for item in merged
        if item['writing_value_score'] >= 60
        and item['relevance_score'] >= 3
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

    reserve = [item for item in merged if item not in selected and item['writing_value_score'] >= 45][:3]
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
                f"### {index}. {item['title']} — {item['writing_value_score']}/100 — {item['level']}",
                '',
                f"- 三线得分：热点观点 {item['line_scores']['hot_take']['score']}，消费决策 {item['line_scores']['decision']['score']}，经验沉淀 {item['line_scores']['experience']['score']}",
                f"- 主线因子：{', '.join(f'{key}={value}' for key, value in d.items())}",
                f"- 内容线判断：{item['content_line_label']}，{item['line_reason']}",
                f"- 路线取舍：{item.get('line_tradeoff') or '主线得分最高，副线仅作备选。'}",
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
            lines.append(f"- {item['title']} — {item['writing_value_score']}/100 — {item['level']}")
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
