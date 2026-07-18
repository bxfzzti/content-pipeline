from prepare_screening_candidates import prepare


def item(title, *, age, platforms=3, category='auto', gate=True, url=''):
    return {
        'title': title,
        'url': url,
        'platform_count': platforms,
        'age_hours': age,
        'freshness_gate_pass': gate,
        'freshness_status': '0-24小时' if age is not None and age <= 24 else '24-48小时',
        'evidence_type': 'rss',
        'category': category,
    }


def test_prepare_rejects_stale_items_and_calculates_fixed_scores():
    payload = {
        'generated_at': '2026-07-18T00:00:00+00:00',
        'full_web': {'technology_ai': [item('新AI产品发布', age=5, platforms=5)]},
        'focus': {
            'auto': [item('旧车上市', age=60, platforms=7, gate=False)],
            '3c': [],
            'smart_home': [],
        },
    }
    result = prepare(payload)
    assert result['stats']['freshness_rejected'] == 1
    candidate = result['candidates'][0]
    assert candidate['heat_score'] == 5
    assert candidate['freshness_score'] == 5
    assert candidate['discussion_score'] == 5
    assert candidate['fixed_subtotal'] == 30


def test_prepare_deduplicates_same_url():
    duplicate = item('苹果音乐涨价', age=3, platforms=5, url='https://example.com/apple')
    payload = {
        'full_web': {'technology_ai': [duplicate]},
        'focus': {'auto': [], '3c': [{**duplicate, 'title': 'Apple Music宣布涨价'}], 'smart_home': []},
    }
    result = prepare(payload)
    assert result['stats']['eligible_after_dedup'] == 1


def test_prepare_caps_auto_shortlist():
    payload = {
        'full_web': {},
        'focus': {
            'auto': [item(f'品牌{i}新车正式上市', age=2, platforms=5, url=f'https://car/{i}') for i in range(10)],
            '3c': [item(f'手机{i}新品发布', age=2, platforms=4, url=f'https://phone/{i}') for i in range(5)],
            'smart_home': [],
        },
    }
    result = prepare(payload, limit=20)
    assert sum(candidate['category'] == 'auto' for candidate in result['candidates']) == 6


def test_prepare_preserves_focus_and_full_web_layers():
    payload = {
        'full_web': {
            'sports': [item(f'体育热点{i}', age=2, platforms=5, url=f'https://sports/{i}') for i in range(8)],
            'technology_ai': [item(f'AI热点{i}', age=2, platforms=4, url=f'https://ai/{i}') for i in range(4)],
        },
        'focus': {
            'auto': [item(f'车型{i}正式上市', age=2, platforms=2, url=f'https://car/{i}') for i in range(5)],
            '3c': [item(f'手机{i}新品发布', age=2, platforms=2, url=f'https://phone/{i}') for i in range(4)],
            'smart_home': [item(f'家电{i}新品发布', age=2, platforms=1, url=f'https://home/{i}') for i in range(3)],
        },
    }
    result = prepare(payload, limit=15)
    assert sum(candidate['layer'] == 'focus' for candidate in result['candidates']) >= 9
    assert sum(candidate['layer'] == 'full_web' for candidate in result['candidates']) >= 6


def test_prepare_merges_same_model_even_when_other_numbers_differ():
    payload = {
        'full_web': {},
        'focus': {
            'auto': [
                item('Model Y降价没用？24.99万的阿维塔07L来了', age=2, platforms=4, url='https://car/launch'),
                item('阿维塔07L预售后官方声明遭遇黑公关', age=3, platforms=3, url='https://car/legal'),
            ],
            '3c': [],
            'smart_home': [],
        },
    }
    result = prepare(payload)
    assert result['stats']['eligible_after_dedup'] == 1
