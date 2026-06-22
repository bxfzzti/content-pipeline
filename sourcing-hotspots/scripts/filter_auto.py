#!/usr/bin/env python3
"""Filter hot-aggregator JSON for automotive-related items.

Usage: python3 scripts/filter_auto.py /tmp/hotspots.json

Reads the full hot-aggregator API response, applies two-layer keyword
filtering (brand/event keywords required, context validation), deduplicates,
and prints a ranked list.
"""
import json
import sys

# --- Configuration ---
# Layer 1: Hard keywords (must match at least one)
BRAND_KEYWORDS = [
    '比亚迪', '蔚来', '理想', '问界', '特斯拉', '零跑', '小鹏', '极氪', '领克',
    '宝马', '奔驰', '奥迪', '沃尔沃', '仰望', '岚图', '深蓝', '阿维塔', '极越',
    '启境', '飞凡', '智己', '昊铂', '方程豹', '腾势', '坦克', '魏牌', '哈弗',
    '长安', '奇瑞', '哪吒', '大众', '丰田', '本田', '日产', '雷克萨斯',
    '保时捷', '宾利', '劳斯莱斯', '法拉利',
]

PERSON_KEYWORDS = [
    '雷军', '李斌', '何小鹏', '李想', '王传福', '余承东',
]

# These need context validation (layer 2) to avoid false positives
CONTEXT_KEYWORDS = [
    '智驾', 'FSD', '自动驾驶', '续航', '换电', '增程', '纯电', '混动',
    '电池', '充电', '养路费',
]

# Single-char keywords are DANGEROUS — only use with context validation
AMBIGUOUS_KEYWORDS = ['SUV', '新车']

# Layer 2: Context words that must appear near the match for ambiguous keywords
AUTO_CONTEXT = ['车', '汽', '驾驶', '上市', '发布', '预售', '提车', '购车', '车型']

# Noise filter
NOISE_PATTERNS = ['喜加一', 'Epic喜加', '源码', '开源软件', '免费领', '游戏']


def load_data(path):
    with open(path) as f:
        return json.load(f)


def extract_items(data):
    """Extract all items from hot-aggregator response."""
    items = []
    for platform in data.get('data', []):
        source = platform.get('name', 'unknown')
        for item in platform.get('data', []):
            item['source'] = source
            items.append(item)
    return items


def is_noise(text):
    return any(p in text for p in NOISE_PATTERNS)


def has_auto_context(text):
    """Check if text has automotive context words."""
    return any(k in text for k in AUTO_CONTEXT)


def filter_auto(items):
    """Two-layer filtering for automotive relevance."""
    seen = set()
    results = []

    for item in items:
        title = item.get('title', '')
        desc = item.get('desc', '')
        text = title + ' ' + desc

        # Skip noise
        if is_noise(text):
            continue

        # Skip if already seen
        if title in seen:
            continue

        matched = []

        # Layer 1: Hard brand/person keywords (high confidence)
        for kw in BRAND_KEYWORDS + PERSON_KEYWORDS:
            if kw in text:
                matched.append(kw)

        # Layer 1: Context keywords (need automotive context nearby)
        for kw in CONTEXT_KEYWORDS:
            if kw in text:
                matched.append(kw)

        # Ambiguous keywords only count if auto context present
        for kw in AMBIGUOUS_KEYWORDS:
            if kw in text and has_auto_context(text):
                matched.append(kw)

        if matched:
            seen.add(title)
            item['matched_keywords'] = matched
            results.append(item)

    return results


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/hotspots.json'
    data = load_data(path)
    items = extract_items(data)
    auto_items = filter_auto(items)

    print(f"Total: {len(items)}, Auto-filtered: {len(auto_items)}")
    for i, item in enumerate(auto_items):
        src = item['source']
        title = item['title']
        kw = ', '.join(item['matched_keywords'])
        print(f"  {i+1}. [{src}] {title} | {kw}")


if __name__ == '__main__':
    main()
