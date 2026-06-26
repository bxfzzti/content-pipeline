# 完整内容生产流水线（2026-05-31 验证）

## 流程总览

```
sourcing-hotspots（热点抓取）
  → screening-topics（选题筛选，S/A/B级）
  → framing-article（定调+论点结构）
  → writing-draft（写正文，≥1500字）
  → [数据验证 + 配图生成]（并行）
  → [独立质检]（delegate_task，对抗式审稿）
  → [修改]（如有🔴问题）
  → publishing-doc（发布飞书，含图片插入）
```

## 各步骤详解

### 1. 热点抓取
- hot-aggregator（端口6688）+ 国际RSS + 家居RSS
- 四品类过滤：汽车/3C/AI/家居
- 输出：8-12条跨品类精选热点

### 2. 选题筛选
- 五问审查：事实层/争议空间/趋势关联/独特角度/消费决策
- 传播势能判断：跨平台热度/评论情绪/时间窗口
- 输出：S/A/B级选题建议

### 3. 定调
- 创作立场 → 定调 → 引用块 → 论点结构
- 涉及具体车企/车型时禁止负面倾向

### 4. 写正文
- 口语化风格：口语化、短句、有判断、不居高临下
- 每段一个核心观点+一个例子+一句收住
- ≥1500字，每个论点有具体数据支撑

### 5. 数据验证（并行）
```bash
python3 ~/.hermes/skills/publishing-doc/scripts/verify_facts.py <article.md>
```
- 提取事实性声明 → 交叉验证数据源 → 标记未验证项

### 6. 配图生成（并行）
```bash
python3 ~/.hermes/skills/publishing-doc/scripts/gen_chart.py --type bar --data '{...}' --output /tmp/chart.png
python3 ~/.hermes/skills/publishing-doc/scripts/gen_chart.py --type table --data '{...}' --output /tmp/table.png
python3 ~/.hermes/skills/publishing-doc/scripts/gen_chart.py --type header --data '{...}' --output /tmp/header.png
```

### 7. 独立质检（阻断发布）
```python
delegate_task(
    goal="审稿：找出文章中的所有问题。你是一个挑剔的资深汽车编辑。",
    context=f"文章正文：{article}\n审稿标准：事实准确性/逻辑漏洞/立场偏颇/论据厚度/读者价值/风格问题\n输出🔴🟡🟢三级报告。"
)
```
- 🔴 必须修改 → 阻断发布
- 🟡 建议修改 → 不阻断
- 🟢 通过项

### 8. 发布飞书
```bash
source ~/.hermes/hermes-agent/.venv/bin/activate
python3 ~/.hermes/skills/publishing-doc/scripts/publish_to_feishu.py <article.md> "标题"
```

### 9. 插入图片（三步流程）
```bash
python3 ~/.hermes/skills/publishing-doc/scripts/add_images_to_doc.py <doc_id> \
  --after "匹配文本" /tmp/chart.png \
  --after "匹配文本2" /tmp/table.png
```
飞书图片插入三步：创建空block → 上传drive → PATCH replace_image

## Cookie 登录态

| 平台 | 文件 | 用途 |
|------|------|------|
| 小红书 | `~/.hermes/cookies/xhs.json` | 内容搜索、热榜 |
| Twitter | `~/.hermes/cookies/twitter.json` | AI大佬追踪 |
| SMZDM | 待提供 | 家居品类补源 |

## 已知限制

- 搜索引擎（DDG/Google/Bing）从服务器IP被屏蔽
- 飞书API不支持直接创建表格block（用文字替代）
- 飞书API不支持直接创建引用块和分割线
- XHS需要浏览器登录态或正确的API签名（直接curl被反爬）
