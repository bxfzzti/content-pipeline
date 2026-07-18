import pytest

from run_screening_once import build_prompt, parse_json_object, validate_payload


def payload():
    return {
        'run_id': 'run-1',
        'candidates': [{'candidate_id': 'C01', 'title': '新手机发布'}],
    }


def judgment():
    return {
        'run_id': 'run-1',
        'judgments': [{
            'candidate_id': 'C01', 'emotion_score': 4, 'relevance_score': 5,
            'core_judgment': '判断', 'recommended_angle': '角度', 'risk': '风险',
            'reader_start': '起点', 'six_question_pass_count': 5,
        }],
    }


def test_prompt_contains_run_id_and_candidate():
    prompt = build_prompt(payload())
    assert 'run-1' in prompt
    assert 'C01' in prompt


def test_parse_fenced_json():
    assert parse_json_object('```json\n{"run_id":"run-1"}\n```')['run_id'] == 'run-1'


def test_validate_rejects_missing_candidate():
    result = judgment()
    result['judgments'] = []
    with pytest.raises(ValueError, match='IDs mismatch'):
        validate_payload(result, payload())
