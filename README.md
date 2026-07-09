# 会自己找选题的内容流水线

很多内容工具的问题，不是不会写，而是只会在你给定题目之后写。

真正卡住人的地方通常在更前面：

- 今天到底写什么？
- 这个选题有没有传播价值？
- 能不能找到一个不俗的角度？
- 写完以后像不像 AI？
- 小红书图文要怎么拆？
- 产品体验、开箱、吐槽、横评这些素材，能不能每天自动沉淀？

这个仓库解决的是这条完整链路。

它不是一个「帮我写一篇」的 prompt 集合，而是一套多 Agent 内容生产流水线：从热点和产品体验素材开始，经过筛选、角度、标题、结构、正文、质检、小红书适配，最后沉淀到飞书多维表格。

## 它适合谁

适合想稳定做内容，但不想每天从空白页开始的人。

尤其适合这几类场景：

- 小红书图文选题
- 科技/数码/生活产品二创
- 什么值得买体验、开箱、吐槽、横评素材复用
- 热点转观点文章
- 长文转小红书笔记
- 用飞书 Base 管理每日选题池

如果你只是想让 AI 随便写一篇文章，这套东西会显得重。
如果你想把「找题、判断、写作、复盘」变成每天能跑的流程，它就正好。

## 这条流水线怎么跑

核心路径是：

```text
抓素材
  ↓
筛选题
  ↓
选角度
  ↓
定结构
  ↓
做标题
  ↓
写正文
  ↓
质检修稿
  ↓
小红书适配
  ↓
写入飞书选题池
```

它有两条上游输入。

第一条是热点线：回答「今天大家在聊什么」。
第二条是产品体验线：回答「最近哪些产品正在被体验、开箱、吐槽、横评」。

这两条线不要混在一起。热点适合做观点，产品体验适合做二创。

## 最新能力：产品体验选题池

这次新增的重点，是产品体验线。

它会从什么值得买为主的内容源里，抓取科技类和生活类产品的体验、开箱、横评、吐槽、新品信息，再用一套二创分数排序。

默认主抓词不是拍脑袋来的，而是从什么值得买近期类目热度和实跑结果里收敛出来的：

```text
NAS、耳机、键盘、路由器、显卡、显示器、手机、充电器、游戏本
洗地机、咖啡机、扫地机器人、空气净化器、空调、冰箱
浴霸、投影仪、3D打印机、车载冰箱、智能门锁
```

它会输出这些信息：

- 原文标题
- 原文链接
- 内容类型：体验/评测、横评/对比、吐槽/避坑、新品开箱等
- 内容短摘
- 二创切入
- 单篇分
- 关键词稳定分
- 评论/收藏/点赞
- 抓取时间

重点是：只给标题没意义，必须给链接和内容定位。
这套流程默认会把原文链接和短摘一起带出来，方便继续做小红书二创。

## 二创分怎么来的

`creative_score` 不按阅读量算，因为当前接口没有稳定返回阅读量。

它看的是更稳定的几个字段：

```text
关键词命中
来源可信度
内容类型
评论/收藏/点赞
近期性
是否包含具体型号
```

同时还有一个「关键词稳定分」：

```text
前 5 条平均单篇分 + 有效条数加成
```

这样可以避免某个品类只靠一篇互动异常高的文章冲到第一。
比如「浴霸」曾经因为单篇互动高排到第一，但从稳定性看，洗地机、耳机、手机、NAS、键盘这类品类更适合长期追。

## 快速运行

生成本地选题报告：

```bash
python sourcing-hotspots/scripts/smzdm_product_topics.py --output-dir output
```

会生成：

```text
output/smzdm_product_topics_report.md
output/smzdm_product_topics_items.json
output/smzdm_product_topics_rows.json
```

同步到飞书多维表格：

```bash
python sourcing-hotspots/scripts/smzdm_product_topics.py \
  --output-dir output \
  --sync-lark \
  --base-token <base_token> \
  --table-id <table_id>
```

创建飞书 Base：

```bash
cd sourcing-hotspots
scripts/create_lark_base.sh
```

安装每日刷新任务：

```bash
cd sourcing-hotspots
HERMES_TOPICS_PYTHON=/path/to/python \
scripts/install_daily_smzdm_topics_launchd.sh <base_token> <table_id>
```

默认每天 `09:20` 刷新一次。

## 仓库结构

| 模块 | 作用 |
|------|------|
| `article-pipeline/` | 总入口，定义完整内容生产流程 |
| `sourcing-hotspots/` | 热点线 + 产品体验线 |
| `daily-hot-mcp/` | daily-hot-mcp 扩展工具源码 |
| `screening-topics/` | 选题筛选 |
| `angle-selection/` | 角度选择 |
| `framing-article/` | 定调和结构 |
| `title-craft/` | 标题生成 |
| `writing-draft/` | 正文撰写 |
| `polishing-writing/` | 质检和修稿 |
| `xhs-adapter/` | 小红书图文适配 |
| `publishing-doc/` | 飞书文档发布 |
| `zvec/` | 本地向量知识库 |

## 一次真实输出长什么样

产品体验线会产出类似这样的候选：

```text
标题：花3000买咖啡机结果翻车？测评三款千元档，看完知道怎么选不踩坑
链接：https://post.smzdm.com/p/aqrge67p/
类型：吐槽/避坑
二创切入：适合做「咖啡机避坑/翻车复盘」方向
内容定位：买半自动咖啡机后，预热、萃取、奶泡、清洁都可能变成日常负担
```

然后可以继续二创成小红书笔记：

```text
我终于知道为什么很多人买了咖啡机就吃灰了
```

这就是这套流水线的目标：不是把原文搬过来，而是把原文变成可判断、可筛选、可改写、可追踪的内容资产。

## zvec 知识库

仓库内置 zvec 知识库接口，用来做：

1. 选题去重
2. 历史角度检索
3. 竞品内容检索
4. 风格锚点检查
5. 混合检索

命令示例：

```bash
/tmp/zvec-poc/bin/python zvec/zvec_kb.py dedup "咖啡机为什么会吃灰" 0.65
/tmp/zvec-poc/bin/python zvec/zvec_kb.py search_angles "洗地机 发臭 避坑" 5
/tmp/zvec-poc/bin/python zvec/zvec_kb.py check_style "文章前500字" 5
```

## 版本历史

见 [CHANGELOG.md](./CHANGELOG.md)。

当前重点版本：

- `v0.6.0`：新增产品体验选题池、什么值得买二创流、飞书 Base 每日增补。
