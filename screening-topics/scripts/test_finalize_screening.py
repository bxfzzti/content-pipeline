from finalize_screening import finalize, render_markdown


RUN_ID = 'run-current'


def candidate_payload(items):
    return {'run_id': RUN_ID, 'candidates': items}


def judgment_payload(items, run_id=RUN_ID):
    return {'run_id': run_id, 'judgments': items}


def candidate(index, category='3c', brand=''):
    return {
        'candidate_id': f'C{index:02d}',
        'title': f'候选{index}',
        'url': f'https://example.com/{index}',
        'layer': 'focus',
        'category': category,
        'brand': brand,
        'platform_count': 4,
        'heat_score': 4,
        'freshness_score': 5,
        'discussion_score': 4,
    }


def judgment(index, emotion=4, relevance=5):
    return {
        'candidate_id': f'C{index:02d}',
        'emotion_score': emotion,
        'relevance_score': relevance,
        'content_line': 'decision',
        'line_reason': f'内容线理由{index}',
        'asset_value': 4,
        'core_judgment': f'判断{index}',
        'recommended_angle': f'角度{index}',
        'risk': f'风险{index}',
        'reader_start': f'起点{index}',
        'next_stage_requirement': f'下一步{index}',
        'six_question_pass_count': 5,
    }


def test_finalize_calculates_total_in_code():
    result = finalize(candidate_payload([candidate(1)]), judgment_payload([judgment(1)]))
    item = result['recommendations'][0]
    assert item['writing_value_score'] == 44
    assert item['level'] == 'S级'
    assert item['content_line'] == 'decision'
    assert item['content_line_label'] == '消费决策线'


def test_finalize_requires_complete_model_judgment():
    incomplete = judgment(1)
    incomplete['risk'] = ''
    result = finalize(candidate_payload([candidate(1)]), judgment_payload([incomplete]))
    assert result['stats']['valid_model_judgments'] == 0
    assert result['stats']['minimum_met'] is False


def test_finalize_requires_content_line():
    incomplete = judgment(1)
    incomplete.pop('content_line')
    result = finalize(candidate_payload([candidate(1)]), judgment_payload([incomplete]))
    assert result['stats']['valid_model_judgments'] == 0


def test_finalize_enforces_brand_and_auto_diversity():
    candidates = [candidate(i, 'auto' if i <= 7 else '3c', '小米' if i <= 3 else '') for i in range(1, 11)]
    judgments = [judgment(i) for i in range(1, 11)]
    result = finalize(candidate_payload(candidates), judgment_payload(judgments))
    selected = result['recommendations']
    assert sum(item['brand'] == '小米' for item in selected) <= 2
    assert sum(item['category'] == 'auto' for item in selected) <= len(selected) // 2
    assert result['stats']['minimum_met'] is True


def test_render_warns_instead_of_padding_when_fewer_than_five():
    candidates = [candidate(i) for i in range(1, 4)]
    judgments = [judgment(i) for i in range(1, 4)]
    result = finalize(candidate_payload(candidates), judgment_payload(judgments))
    markdown = render_markdown(result)
    assert '实际 3 条' in markdown
    assert '## 消费决策线（3 条）' in markdown


def test_low_relevance_cannot_enter_formal_recommendations():
    candidates = [candidate(i) for i in range(1, 7)]
    judgments = [judgment(1, emotion=5, relevance=1)] + [judgment(i) for i in range(2, 7)]
    result = finalize(candidate_payload(candidates), judgment_payload(judgments))
    assert all(item['candidate_id'] != 'C01' for item in result['recommendations'])


def test_focus_candidates_are_not_crowded_out_by_full_web_heat():
    candidates = [candidate(i) for i in range(1, 11)]
    for item in candidates[:7]:
        item['layer'] = 'focus'
    for item in candidates[7:]:
        item['layer'] = 'full_web'
    judgments = [judgment(i) for i in range(1, 11)]
    result = finalize(candidate_payload(candidates), judgment_payload(judgments))
    assert sum(item['layer'] == 'focus' for item in result['recommendations']) >= 7


def test_finalize_rejects_stale_judgments_from_another_run():
    result = finalize(
        candidate_payload([candidate(1)]),
        judgment_payload([judgment(1)], run_id='run-old'),
    )
    assert result['stats']['valid_model_judgments'] == 0
    assert result['stats']['minimum_met'] is False
    assert 'run_id' in result['contract_error']
