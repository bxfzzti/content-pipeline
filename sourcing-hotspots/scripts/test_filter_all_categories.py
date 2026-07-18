import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name('filter_all_categories.py')


def test_presentation_is_full_web_first_and_keeps_links(tmp_path):
    domestic = {
        'data': [
            {'name': 'weibo', 'data': [
                {'title': '世界杯决赛开赛', 'url': 'https://example.com/sports'},
                {'title': '台风登陆多地停课', 'url': 'https://example.com/social'},
                {'title': '小米手机新品正式发布', 'url': 'https://example.com/phone'},
                {'title': '路人见义勇为获奖', 'desc': '摘要中提到小米汽车正式上市'},
                {'title': 'Stop saying that AI matters', 'desc': 'not a smart-home story'},
            ]},
            {'name': 'zhihu', 'data': [
                {'title': '世界杯决赛开赛', 'url': 'https://example.com/sports-2'},
                {'title': '台风登陆多地停课', 'url': 'https://example.com/social-2'},
                {'title': '小米手机新品正式发布', 'url': 'https://example.com/phone-2'},
            ]},
        ]
    }
    domestic_path = tmp_path / 'domestic.json'
    intl_path = tmp_path / 'intl.json'
    home_path = tmp_path / 'home.json'
    domestic_path.write_text(json.dumps(domestic, ensure_ascii=False), encoding='utf-8')
    intl_path.write_text('[]', encoding='utf-8')
    home_path.write_text('[]', encoding='utf-8')

    subprocess.run(
        [sys.executable, str(SCRIPT), str(domestic_path), str(intl_path), str(home_path), str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads((tmp_path / '01-hotspots-presentation.json').read_text(encoding='utf-8'))
    markdown = (tmp_path / '01-hotspots-presentation.md').read_text(encoding='utf-8')
    assert payload['display_order'] == ['full_web', 'focus']
    assert payload['validation']['valid'] is True
    assert list(payload['focus']) == ['auto', '3c', 'smart_home']
    assert payload['full_web']['sports'][0]['platform_count'] == 2
    assert payload['full_web']['sports'][0]['freshness_verified'] is True
    assert payload['full_web']['sports'][0]['freshness_status'] == '实时热榜（发布时间未提供）'
    assert payload['full_web']['sports'][0]['freshness_gate_pass'] is True
    assert payload['full_web']['sports'][0]['recommendation_status'] == '今日候选'
    assert payload['focus']['3c'][0]['url'] == 'https://example.com/phone'
    assert 'published_at' in payload['focus']['3c'][0]
    assert 'age_hours' in payload['focus']['3c'][0]
    assert all(item['title'] != '路人见义勇为获奖' for items in payload['focus'].values() for item in items)
    assert all(item['title'] != 'Stop saying that AI matters' for item in payload['focus']['smart_home'])
    assert markdown.index('# 第一部分：全网热点') < markdown.index('# 第二部分：我关注的方向')
    assert 'https://example.com/sports' in markdown
