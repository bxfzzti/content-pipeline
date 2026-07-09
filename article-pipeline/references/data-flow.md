# 数据流总图

每两个 Skill 之间传递的数据：

```
【用户输入：话题/指令】
        │
        ▼
┌─────────────────┐
│ sourcing-hotspots │ ───→ 原始热点列表（平台+标题+热度）
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ screening-topics  │ ───→ 选题建议（S/A/B级 + writing_value_score + 六问/内容策略）
└─────────────────┘
        │  ←──【用户确认选题】
        ▼
┌─────────────────┐
│ angle-selection   │ ───→ 角度选择（推荐角度+SPOV评分+标题/定调方向指引）
└─────────────────┘
        │  ←──【用户确认角度】
        ▼
┌─────────────────┐
│ framing-article   │ ───→ 写作思路（认知交付卡+定调+引用块+论点大纲+收尾）
└─────────────────┘   ┌──────────────┐
        │  ←──【用户确认思路】 │ writing-style │（风格参考，按需加载）
        ▼               └──────────────┘
┌─────────────────┐
│ title-craft       │ ───→ 标题方案（5-8个，跨3种触发器）
└─────────────────┘
        │  ←──【用户选标题】
        ▼
┌─────────────────┐
│ writing-draft     │ ───→ 完整正文 markdown
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ polishing-writing│ ───→ 质检报告 + 修改建议
└─────────────────┘
        │
   ┌────┴────┐
   ▼         ▼
 不通过      通过
   │         │
   │         │
   │         │ 通过
   │         ▼
   │    ┌─────────────────┐
   │    │ xhs-adapter      │（小红书平台发布前必经；非小红书跳过）
   │    └─────────────────┘
   │            │
   │            ▼
   │    ┌─────────────────┐
   │    │ publishing-doc    │ ───→ 飞书文档链接（最终交付）
   │    └─────────────────┘
   │            │
   │            ▼
   │    ┌─────────────────┐
   │    │ bitable-tracker  │ ───→ 写入多维表格 + 设置7天提醒
   │    └─────────────────┘
   │            │
   │            ▼
   │       回复用户
   │  （写作思路 + 文档链接 + 表格已更新）
   │
   │ 不通过
   ▼
┌─────────────────┐
│ writing-draft     │（按质检建议修稿后重新质检）
└─────────────────┘
        │
        └──→ polishing-writing
```

## 每个环节的数据传递物

| 环节 | 输入 | 输出 | 本地文件 | Obsidian |
|------|------|------|---------|----------|
| sourcing-hotspots | 用户指令 | 原始热点列表 | /tmp/article-pipeline/01-hotspots-raw.md | 汽车行业/流水线/01-hotspots-raw.md |
| sourcing-hotspots | 产品关键词/默认品类 | 产品体验/开箱/吐槽候选池 | /tmp/article-pipeline/01b-product-experience.md | 汽车行业/流水线/01b-product-experience.md |
| screening-topics | 原始热点列表 + 产品体验候选池 | 选题建议 | /tmp/article-pipeline/02-topic-suggestion.md | 汽车行业/流水线/02-topic-suggestion.md |
| angle-selection | 选题方向 | 角度选择 | /tmp/article-pipeline/02b-angle-selection.md | 汽车行业/流水线/02b-angle-selection.md |
| framing-article | 选题方向+角度选择 | 写作思路 | /tmp/article-pipeline/03-article-framework.md | 汽车行业/流水线/03-article-framework.md |
| title-craft | 写作思路 | 标题方案 | /tmp/article-pipeline/03b-title-options.md | 汽车行业/流水线/03b-title-options.md |
| writing-draft | 写作思路 | 完整正文 | /tmp/article-pipeline/04-article-draft.md | 汽车行业/流水线/04-article-draft.md |
| polishing-writing | 完整正文 | 质检报告 | /tmp/article-pipeline/05-quality-report.md | 汽车行业/流水线/05-quality-report.md |
| xhs-adapter | 完整正文+质检报告 | 小红书标题/封面/关键词/发布时间建议 | /tmp/article-pipeline/05b-xhs-adaptation.md | 汽车行业/流水线/05b-xhs-adaptation.md |
| publishing-doc | 完整正文 | 飞书链接 | — | — |
| bitable-tracker | 飞书链接+原始标题+最终标题 | 多维表格记录+7天提醒 | — | — |
| growing-from-mistakes | 错误描述 | 复盘记录 | /tmp/article-pipeline/06-mistake-reflection.md | 写作资料/反思记录/ |

**文件化规则：** 每个 Skill 执行完成后，必须将产出写入本地 `/tmp/article-pipeline/`。后一个 Skill 读取本地文件作为输入，同时主 Agent 也要把完整文本传给子 Agent，避免隔离环境读不到文件。

**落盘自检：**

```bash
test -s /tmp/article-pipeline/01-hotspots-raw.md
test -s /tmp/article-pipeline/01b-product-experience.md
test -s /tmp/article-pipeline/02-topic-suggestion.md
test -s /tmp/article-pipeline/02b-angle-selection.md
test -s /tmp/article-pipeline/03-article-framework.md
test -s /tmp/article-pipeline/03b-title-options.md
test -s /tmp/article-pipeline/04-article-draft.md
test -s /tmp/article-pipeline/05-quality-report.md
```

直接跑完整流程时，最终报告必须包含上述自检结果。缺任一文件时，不能声称「全流程跑通」。
