# 政策类热点关键词 — 待加入 filter_all_categories.py

## 背景（2026-06-18 教训）
用户指出"新能源汽车下乡"等重要政策热点未被发现。当前过滤脚本的趋势品类只覆盖市场类趋势，缺少政策类关键词。

## 待添加到 trend_auto 的关键词

```python
trend_auto = r'新能源车涨价|新能源车降价|造车新势力|车市|汽车市场格局|车企淘汰|智驾普及|充电桩涨价|电池涨价|动力电池|固态电池|二手车.*崩盘|油车.*崩盘|汽车下乡|下乡补贴|下乡活动|以旧换新|置换补贴|购置税|国补|车船税减免|充换电设施|县域充电|工信部.*通知|商务部.*通知|国务院.*汽车|减免购置税|购车补贴|报废更新'
```

## 需要新增的数据源

### 政府/央媒 RSS
- 中国政府网: `http://www.gov.cn/rss/govall.xml`（需验证可用性）
- 工信部官网: 无RSS，需用web_search补充
- 商务部官网: 无RSS，需用web_search补充
- 人民日报: `http://paper.people.com.cn/rmrb/images/`（PDF格式，不便于RSS解析）

### 补盲搜索关键词（每次抓热点后额外跑一轮）
```python
POLICY_KEYWORDS = [
    "新能源汽车 下乡 2026",
    "汽车 购置税 政策 2026", 
    "以旧换新 汽车 补贴 2026",
    "工信部 汽车 通知 2026",
    "商务部 汽车 政策 2026",
]
```

## 执行方式
在 sourcing-hotspots 的抓取流程末尾，新增一步：
```python
from hermes_tools import web_search
for kw in POLICY_KEYWORDS:
    r = web_search(kw, limit=3)
    # 将结果合并到热点数据中
```

## 状态
- [ ] 将 trend_auto 关键词更新到 filter_all_categories.py
- [ ] 验证政府RSS源可用性
- [ ] 在抓取流程中添加政策补盲搜索
