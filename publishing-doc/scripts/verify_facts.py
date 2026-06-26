#!/usr/bin/env python3
"""
数据验证脚本：从文章中提取事实性声明，标记未验证项。
用法：python3 verify_facts.py <article.md>
输出：验证报告（已验证/未验证/存疑）
"""
import re, sys, json, os
from datetime import datetime

def extract_facts(text):
    """从文章中提取所有事实性声明"""
    facts = []
    
    # 1. 提取含具体数字的句子
    number_patterns = [
        # 百分比
        (r'([^。！？\n]*?\d+\.?\d*%[^。！？\n]*)', 'percentage'),
        # 金额
        (r'([^。！？\n]*?\d+\.?\d*[万亿]*元[^。！？\n]*)', 'money'),
        # 台/辆/个等量词
        (r'([^。！？\n]*?\d+\.?\d*[万]*[台辆个人次个][^。！？\n]*)', 'quantity'),
        # 时间（年/月/天）
        (r'([^。！？\n]*?\d+[年个月天日][^。！？\n]*)', 'time'),
        # 城市数/覆盖数
        (r'([^。！？\n]*?\d+[多]*个[^。！？\n]*)', 'count'),
        # 价格
        (r'([^。！？\n]*?\d+\.?\d*万[元起][^。！？\n]*)', 'price'),
    ]
    
    for pattern, fact_type in number_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            m = m.strip()
            if len(m) > 10 and len(m) < 200:  # 过滤太短或太长的
                facts.append({
                    'text': m,
                    'type': fact_type,
                    'status': 'unverified',
                    'source': None
                })
    
    # 2. 提取对比性声明
    comparison_patterns = [
        r'([^。！？\n]*?比[^。！？\n]*[快高低大强多慢小低弱少][^。！？\n]*)',
        r'([^。！？\n]*?[超超过越]过[^。！？\n]*)',
        r'([^。！？\n]*?是[^。！？\n]*的\d+倍[^。！？\n]*)',
    ]
    
    for pattern in comparison_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            m = m.strip()
            if len(m) > 10 and len(m) < 200:
                facts.append({
                    'text': m,
                    'type': 'comparison',
                    'status': 'unverified',
                    'source': None
                })
    
    # 3. 去重
    seen = set()
    unique_facts = []
    for f in facts:
        key = f['text'][:30]
        if key not in seen:
            seen.add(key)
            unique_facts.append(f)
    
    return unique_facts

def check_against_sources(facts, sources_files):
    """用已有数据源交叉验证"""
    source_data = []
    for f in sources_files:
        if os.path.exists(f):
            try:
                with open(f, 'r') as fh:
                    source_data.append(fh.read())
            except:
                pass
    
    if not source_data:
        return facts
    
    combined = '\n'.join(source_data)
    
    for fact in facts:
        # 提取事实中的关键词
        keywords = re.findall(r'[\u4e00-\u9fff]+|[A-Za-z]+|\d+', fact['text'])
        # 检查有多少关键词出现在数据源中
        matches = sum(1 for kw in keywords if kw in combined and len(kw) > 2)
        if matches >= 3:
            fact['status'] = 'source_match'
            fact['source'] = 'hot-aggregator/RSS'
    
    return facts

def generate_report(facts, article_path):
    """生成验证报告"""
    verified = [f for f in facts if f['status'] == 'source_match']
    unverified = [f for f in facts if f['status'] == 'unverified']
    
    report = []
    report.append(f"# 数据验证报告")
    report.append(f"**文章：** {article_path}")
    report.append(f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**提取事实点：** {len(facts)} 个")
    report.append(f"**已验证：** {len(verified)} 个")
    report.append(f"**未验证：** {len(unverified)} 个")
    report.append("")
    
    if unverified:
        report.append("## ⚠️ 未验证的事实声明（需人工确认）")
        for i, f in enumerate(unverified, 1):
            report.append(f"{i}. [{f['type']}] {f['text'][:100]}")
        report.append("")
    
    if verified:
        report.append("## ✅ 有数据源支撑的事实")
        for i, f in enumerate(verified[:10], 1):
            report.append(f"{i}. {f['text'][:100]}")
    
    return '\n'.join(report)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 verify_facts.py <article.md>")
        sys.exit(1)
    
    article_path = sys.argv[1]
    with open(article_path, 'r') as f:
        text = f.read()
    
    # 提取事实
    facts = extract_facts(text)
    print(f"提取到 {len(facts)} 个事实性声明")
    
    # 用已有数据源验证
    sources = [
        '/tmp/hotspots.json',
        '/tmp/rss_international.json',
        '/tmp/rss_home.json',
        '/tmp/filtered_daily_clean.json'
    ]
    facts = check_against_sources(facts, sources)
    
    # 生成报告
    report = generate_report(facts, article_path)
    print(report)
    
    # 保存报告
    report_path = '/tmp/article-pipeline/06-fact-check.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\n报告已保存到 {report_path}")

if __name__ == '__main__':
    main()
