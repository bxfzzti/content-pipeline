import json
from pathlib import Path

import validate_stage


def write_hotspots(root: Path):
    payload = {
        'display_order': ['full_web', 'focus'],
        'full_web': {'sports': [{'title': 'A'}], 'finance': [{'title': 'B'}]},
        'focus': {'auto': [], '3c': [], 'smart_home': []},
    }
    (root / '01-hotspots-presentation.json').write_text(json.dumps(payload), encoding='utf-8')
    (root / '01-hotspots-presentation.md').write_text(
        '# 第一部分：全网热点\n\n# 第二部分：我关注的方向\n', encoding='utf-8'
    )
    (root / '01c-screening-candidates.json').write_text(
        json.dumps({'candidates': [{'candidate_id': f'C{i:02d}'} for i in range(1, 6)]}),
        encoding='utf-8',
    )


def test_hotspot_gate_rejects_reverse_order(tmp_path):
    write_hotspots(tmp_path)
    (tmp_path / '01-hotspots-presentation.md').write_text(
        '# 第二部分：我关注的方向\n\n# 第一部分：全网热点\n', encoding='utf-8'
    )
    assert 'markdown must show full-web hotspots before focus areas' in validate_stage.validate_hotspots(tmp_path)


def test_screening_gate_requires_suggestion(tmp_path):
    write_hotspots(tmp_path)
    assert any('02-topic-suggestion.md' in error for error in validate_stage.validate_screening(tmp_path))
    (tmp_path / '02-topic-suggestion.md').write_text('选题建议', encoding='utf-8')
    line_scores = {
        'hot_take': {'score': 80, 'factors': {'heat': 4}},
        'decision': {'score': 70, 'factors': {'purchase_confusion': 4}},
        'experience': {'score': 60, 'factors': {'reusability': 3}},
    }
    recommendations = [
        {
            'candidate_id': f'C{i:02d}',
            'dimensions': {'heat': 4},
            'line_scores': line_scores,
            'writing_value_score': 80,
            'score_scale': 100,
            'content_line': 'hot_take',
            'line_reason': '测试内容线',
        }
        for i in range(1, 6)
    ]
    (tmp_path / '02-topic-suggestion.json').write_text(
        json.dumps({'stats': {'minimum_met': True}, 'recommendations': recommendations}),
        encoding='utf-8',
    )
    assert validate_stage.validate_screening(tmp_path) == []
