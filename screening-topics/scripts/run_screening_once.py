#!/usr/bin/env python3
"""Run semantic screening in one dedicated model request, then finalize in code."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from openai import OpenAI

from finalize_screening import finalize, render_markdown, valid_judgment


def load_env_value(name: str) -> str:
    value = os.getenv(name, '').strip()
    if value:
        return value
    env_path = Path.home() / '.hermes' / '.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            if line.startswith(f'{name}='):
                return line.split('=', 1)[1].strip().strip('"\'')
    return ''


def compact_candidates(payload: dict) -> list[dict]:
    keys = (
        'candidate_id', 'title', 'url', 'layer', 'category', 'category_label',
        'candidate_type', 'platform_count', 'freshness_status', 'default_content_line',
        'default_content_line_label', 'line_hint', 'product_keyword', 'product_content_type',
    )
    return [{key: row.get(key) for key in keys} for row in payload.get('candidates') or []]


def build_prompt(payload: dict) -> str:
    contract = {
        'run_id': payload.get('run_id'),
        'judgments': [{
            'candidate_id': 'C01',
            'emotion_score': '1-5整数',
            'relevance_score': '1-5整数',
            'content_line': 'hot_take / decision / experience 三选一，模型建议线；最终由代码按三线得分复算',
            'hot_take_factors': {'sharpness': '1-5整数，观点锋利度'},
            'decision_factors': {
                'purchase_confusion': '1-5整数，购买困惑强度',
                'choice_cost': '1-5整数，选择成本',
                'evidence': '1-5整数，产品/价格/对比证据完整度',
                'actionability': '1-5整数，能否给出买/不买/等/怎么选',
                'save_value': '1-5整数，收藏/搜索价值',
            },
            'experience_factors': {
                'reusability': '1-5整数，经验是否可复用',
                'step_clarity': '1-5整数，是否能写成清晰步骤',
                'operability': '1-5整数，读者能否照着做',
                'case_transfer': '1-5整数，能否迁移到多个案例',
                'long_tail': '1-5整数，长期搜索价值',
            },
            'line_reasons': {
                'hot_take': '作为热点观点线的理由',
                'decision': '作为消费决策线的理由',
                'experience': '作为经验沉淀线的理由',
            },
            'line_tradeoff': '为什么主线优于另外两条线',
            'asset_value': '1-5整数，衡量对账号长期资产/信任/复用的价值',
            'core_judgment': '一句明确、锐利、可证成的判断',
            'recommended_angle': '最值得写的角度；不适合则写“不适用”',
            'risk': '最严重的反面理由',
            'reader_start': '读者看到话题的第一反应',
            'next_stage_requirement': '进入下一步前必须补什么证据或选择什么模板',
            'six_question_pass_count': '0-6整数',
        }],
    }
    return (
        '你是小红书科技与生活产品选题编辑。对每条候选做语义判断，不搜索、不计算总分。\n'
        '对每条候选分别评估三条内容线，代码会按权重计算三线得分并选择最终主线。\n'
        'hot_take=热点观点线，适合借公共情绪和冲突表达锐利判断；'
        'decision=消费决策线，适合买不买、怎么选、避坑、体验、横评和产品判断；'
        'experience=经验沉淀线，适合分享大家都可以用的经验、步骤、避坑和更聪明的做法。\n'
        '内容线按“读者承诺”判断，不按品类硬分：同一个汽车、3C或智能家居选题，都可以是观点、决策或经验。\n'
        '账号定位是“一个有行业判断力的消费者，带用户用内部视角做消费决策”。'
        '分流时先问：读者要我怎么看，还是要怎么选，还是要怎么做更聪明。'
        '读者要我怎么看=hot_take；读者要怎么选=decision；读者要怎么做更聪明=experience。\n'
        'experience 有硬门槛：必须能写成可复用经验、至少3个步骤，并能用案例演示。'
        '例如“怎么买 iPhone 18 最划算”是 experience，不是 decision；因为用户已决定买，问题是怎么买更聪明。\n'
        '汽车是高客单价产品，不要因为来源是汽车媒体就默认归为 hot_take。'
        '如果核心承诺是“这车/这个配置/这个价格该不该买、该等还是该避”，归 decision；'
        '如果核心承诺是“这类事情怎么做更划算、更少踩坑、更可复用”，归 experience；'
        '只有核心承诺是“我对这件新事实或公共情绪怎么看”，才归 hot_take。\n'
        'candidate_type=product_experience 的题默认优先考虑 decision，但如果只是单篇弱体验，可以降低关联度或写“不适用”。\n'
        '内容关联度优先衡量：科技产品、汽车、3C、智能家居、消费决策是否值得二创。'
        '公共灾害、纯政治、体育等即使很热，关联度也应低。角度必须是结论，不是题材复述。\n'
        '每条必须输出三组 factors、line_reasons、line_tradeoff、asset_value、next_stage_requirement。'
        '只返回一个 JSON 对象，不要 Markdown，不要解释。必须覆盖全部 candidate_id，run_id 原样复制。\n'
        f'输出契约：{json.dumps(contract, ensure_ascii=False)}\n'
        f'候选：{json.dumps(compact_candidates(payload), ensure_ascii=False)}'
    )


def parse_json_object(text: str) -> dict:
    text = (text or '').strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.I | re.S)
    start, end = text.find('{'), text.rfind('}')
    if start < 0 or end < start:
        raise ValueError('model did not return a JSON object')
    return json.loads(text[start:end + 1])


def validate_payload(result: dict, candidates: dict) -> None:
    if result.get('run_id') != candidates.get('run_id'):
        raise ValueError('model returned a mismatched run_id')
    expected = {row['candidate_id'] for row in candidates.get('candidates') or []}
    judgments = result.get('judgments') or []
    actual = {row.get('candidate_id') for row in judgments if isinstance(row, dict)}
    if actual != expected:
        raise ValueError(f'model judgment IDs mismatch: expected {sorted(expected)}, got {sorted(actual)}')
    if not all(valid_judgment(row) for row in judgments):
        raise ValueError('model returned incomplete or invalid judgments')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidates', default='/tmp/article-pipeline/01c-screening-candidates.json')
    parser.add_argument('--judgments', default='/tmp/article-pipeline/02a-model-judgments.json')
    parser.add_argument('--output-json', default='/tmp/article-pipeline/02-topic-suggestion.json')
    parser.add_argument('--output-md', default='/tmp/article-pipeline/02-topic-suggestion.md')
    parser.add_argument('--model', default=os.getenv('HERMES_SCREENING_MODEL', 'deepseek-v4-flash'))
    parser.add_argument('--timeout', type=float, default=75.0)
    args = parser.parse_args()

    candidates = json.loads(Path(args.candidates).read_text(encoding='utf-8'))
    api_key = load_env_value('DEEPSEEK_API_KEY')
    if not api_key:
        raise SystemExit('DEEPSEEK_API_KEY is not configured')

    client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com/v1', timeout=args.timeout, max_retries=1)
    response = client.chat.completions.create(
        model=args.model,
        messages=[{'role': 'user', 'content': build_prompt(candidates)}],
        response_format={'type': 'json_object'},
        max_tokens=6000,
        stream=False,
        extra_body={'thinking': {'type': 'disabled'}},
    )
    judgments = parse_json_object(response.choices[0].message.content or '')
    validate_payload(judgments, candidates)
    Path(args.judgments).write_text(json.dumps(judgments, ensure_ascii=False, indent=2), encoding='utf-8')

    result = finalize(candidates, judgments, 10)
    Path(args.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    Path(args.output_md).write_text(render_markdown(result), encoding='utf-8')
    print(json.dumps({'model': args.model, **result['stats']}, ensure_ascii=False))
    return 0 if result['stats']['minimum_met'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
