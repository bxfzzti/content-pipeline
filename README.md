# 内容创作流水线 (Content Pipeline)

多 Agent 协同的内容创作流水线，用于小红书等平台的内容生产。

## 架构

```
主Agent（纯调度）
  ├── Step 1: sourcing-hotspots（热点抓取）
  ├── Step 1.2: hotspot-agent（数据质量评估）
  ├── Step 1.5: screening-agent（筛选 + zvec 去重）
  ├── Step 2: 用户确认选题 → 存入 zvec
  ├── Step 3: angle-selection（角度选择 + zvec 历史角度查询）
  ├── Step 3.5: structure-agent（结构分析）
  ├── Step 4: framing-article（定调）
  ├── Step 5: writing-agent（写正文）
  ├── Step 5.5/6: quality-agent（质检 + zvec 风格检查）
  ├── Step 6.5: fix-agent（修复）
  ├── Step 7: publishing-agent（发布）
  └── Step 8: 存入 zvec 知识库（风格锚点 + 选题库）
```

## 模块说明

| 模块 | 功能 |
|------|------|
| `article-pipeline/` | 主流水线 SKILL + 所有 Agent prompt |
| `angle-selection/` | 角度选择 Skill（三轴旋转法 + SPOV 评分） |
| `screening-topics/` | 选题筛选 Skill（50 分制评分） |
| `sourcing-hotspots/` | 热点抓取 Skill（多平台聚合） |
| `title-craft/` | 标题创作 Skill |
| `xhs-adapter/` | 小红书平台适配 Skill |
| `zvec/` | 本地向量知识库模块（选题去重、角度库、风格锚点、竞品库） |

## zvec 知识库

基于阿里开源的 zvec（向量搜索界的 SQLite），提供 5 个能力：

1. **选题去重** — 新选题和历史选题做向量相似度匹配
2. **角度库** — 搜索历史角度避免重复
3. **竞品内容库** — 搜索竞品是否写过类似内容
4. **风格锚点** — 检查文章风格是否符合要求
5. **混合检索** — 向量 + 关键词跨库搜索

### 使用方式

```bash
# Python 环境
/tmp/zvec-poc/bin/python zvec/zvec_kb.py <command> <args>

# 命令列表
add_topic <id> <text> [source]          # 添加选题
add_angle <id> <text> <topic> [score]   # 添加角度
add_competitor <id> <text> <author>     # 添加竞品文章
add_style <id> <text> [good|bad]        # 添加风格锚点
dedup <query> [threshold]               # 选题去重检查
search_angles <query> [topk]            # 搜索相似角度
search_competitor <query> [topk]        # 搜索竞品内容
check_style <draft_text> [topk]         # 检查风格相似度
```

## 版本历史

见 [CHANGELOG.md](./CHANGELOG.md)
