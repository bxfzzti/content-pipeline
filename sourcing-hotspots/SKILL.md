---
name: sourcing-hotspots
description: >
  热点数据抓取。启动 hot-aggregator 服务并调用多平台 API 拉取微博/知乎/抖音/头条/百度/B站 实时热点数据。
  输出原始热点列表。
  Triggers — "抓热点", "看看今天有什么热点", "热搜", "今天的热点", "有什么热点", "现在热点", "scan hotspots", "fetch trending"
---

# sourcing-hotspots

启动 hot-aggregator 服务 + 国际RSS源，拉取国内外实时热点数据，**按四品类体系（汽车 + 3C数码 + AI + 家居）分别过滤**，输出 8-12 条跨品类精选热点。

## 两分钟全覆盖入口（最高优先级）

每次热点抓取统一运行：

```bash
/Users/xxqq/.hermes/hermes-agent/.venv/bin/python \
  ~/.hermes/skills/sourcing-hotspots/scripts/full_hotspot_run.py \
  --output-dir /tmp/article-pipeline \
  --deadline-seconds 120
```

- 120 秒内结束热点阶段，不等待尾部慢源。
- 每个来源必须标记为 `live`、`cache`、`unavailable` 或 `disabled`。
- 服务健康时复用现有进程，只有健康检查失败时才启动，不再每次强制杀进程。
- 热点阶段只抓取、过滤和筛选，不运行 Linkly、zvec、深度网页核验、评论研究或生图。
- 产品体验结果写入本地后，飞书同步使用 `--sync-existing`，不得重新抓取。

## 禁止个人小红书登录态（最高优先级）

热点和研究阶段不得调用 `xhs-cli`、`xiaohongshu-mcp`、浏览器 Cookie、CDP 登录页、`~/.hermes/cookies/xhs.json` 或其他小红书登录态。即使只搜索公开笔记，也不得借用用户账号。

只允许处理用户主动提供的小红书链接、截图、导出内容，以及无需个人登录态的公开搜索索引。此规则覆盖本文所有历史说明；历史段落中出现的小红书 Cookie、MCP 或 CDP 方案均视为停用记录，不得执行。

## 产品体验线（2026-07-09 新增）

热点线之外，并行维护一条「产品体验/开箱/吐槽/横评」线，专门服务小红书二创选题。两条线不要混写：

- 热点线回答「今天大家在聊什么」，输出 `/tmp/article-pipeline/01-hotspots-raw.md`。
- 产品体验线回答「最近哪些科技/生活产品被用户体验、开箱、吐槽、横评」，输出 `/tmp/article-pipeline/01b-product-experience.md`。

优先使用 `daily-hot-mcp` 新增工具 `search-product-experience-posts`：

```json
{
  "keyword": "NAS",
  "limit": 20,
  "include_deals": false,
  "sources": "smzdm,sspai,chiphell"
}
```

默认主抓词来自什么值得买近期类目热度和实跑效果，不靠纯猜：

- 电脑数码：`NAS`、`耳机`、`键盘`、`路由器`、`显卡`、`显示器`、`手机`、`充电器`、`游戏本`
- 生活电器：`洗地机`、`咖啡机`、`扫地机器人`、`空气净化器`、`空调`、`冰箱`
- 家居/办公/车载：`浴霸`、`投影仪`、`3D打印机`、`车载冰箱`、`智能门锁`

观察词只在用户点名或扩展探索时抓：`蓝牙耳机`、`数据线`、`平板电脑`、`智能手表`、`笔记本电脑`、`台式机`、`电吹风`、`电动剃须刀`、`冲牙器`、`电动牙刷`、`美容仪`、`健康秤`、`按摩椅`、`洗衣机`、`汽车充电桩`、`车载支架`。

排序优先看 `creative_score` 和品类稳定分。`creative_score` 由关键词命中、来源可信度、内容类型、评论/收藏/点赞、近期性、具体型号组成；什么值得买当前接口未稳定提供阅读量，不要声称按阅读量排序。

飞书多维表格增补脚本：

```bash
python sourcing-hotspots/scripts/smzdm_product_topics.py --output-dir output
python sourcing-hotspots/scripts/smzdm_product_topics.py --output-dir output --sync-lark --sync-existing --base-token <base_token> --table-id <table_id>
```

相关文件：

- `daily-hot-mcp/tools/product_experience.py` — MCP 工具源码
- `sourcing-hotspots/scripts/smzdm_product_topics.py` — 每日抓取、去重、同步飞书 Base
- `sourcing-hotspots/references/lark_base_schema.json` — 飞书 Base 建表 schema
- `sourcing-hotspots/references/daily-hot-mcp-tools.md` — daily-hot-mcp 工具表
- `article-pipeline/references/data-flow.md` — 产物文件与阶段交接

> **数据源：**
> - `hot-aggregator` 端口 6688 — 国内69平台聚合（微博/知乎/抖音/头条/B站/ithome/geekpark等）
> - **国际RSS源**（48h时间窗口）— TechCrunch/TheVerge/Wired/ArsTechnica/MIT-TR/HN-AI/ProductHunt/9to5Mac/OpenAI Blog/Google AI
> - **家居补充RSS**（72h窗口）— IT之家RSS + 爱范儿RSS + TheVerge SmartHome + HomeKit News + Home Assistant Blog（hot-aggregator天然缺失家居内容）
> - **Twitter AI大佬追踪** — 用浏览器+cookie访问Twitter搜索，追踪AI行业核心声音（sama/karpathy/DarioAmodei/DrJimFan/ylecun/elonmusk/AndrewYNg/JeffDean/ilyasut），cookie存储在 `~/.hermes/cookies/twitter.json`
> - **什么值得买（SMZDM）** — 用cookie访问SMZDM好价/资讯，补充家居/3C品类数据，cookie存储在 `~/.hermes/cookies/smzdm.json`
> - **Twitter/X**（cookie登录态）— `~/.hermes/cookies/twitter.json`，可用于追踪AI行业大佬动态（替代关键词过滤）
> - **公众号搜索**（辅助源）— `wechat_downloader.py search "关键词" --no-read`，通过搜狗搜索微信公众号文章标题。用于发现 RSS/hot-aggregator 覆盖不到的深度内容。详见 `wechat_downloader` skill。
>
> ⚠️ **搜索引擎不可用**：DDG/Google/Bing均屏蔽服务器IP，热点搜索只能依赖RSS+hot-aggregator+cookie登录态平台。

## ⚠️ 执行规范（每次必须遵守）

1. **健康检查优先**：服务健康时直接复用；只有不可用时才启动。来源返回缓存时必须标记缓存时间。
2. **失败不重试同一路径**：单来源失败一次即读取最近有效缓存，没有缓存则标记 `unavailable`。
3. **大数据量先存文件**：hot-aggregator 返回 ~1.6MB，必须 `curl -o /tmp/hotspots.json` 再离线处理，禁止 pipe 直接解析。
4. **输出纪律：** 只输出两段式精选到对话（我关注的热点 + 全网热点）。原始数据、工具调用过程、中间结果不进聊天。KOL观点在 angle-selection 环节采集，不在抓热点阶段输出。
5. **⚠️ 必须覆盖多品类**：内容策略是 30%汽车+20%数码科技+20%家居+15%热点+15%AI。过滤时必须跑三类关键词体系，不能只跑汽车。用户明确要求过：「应该不只有汽车，科技的产品也是一个范畴」。

## 启动服务（如未运行）

⚠️ **Hermes terminal 不支持 `&` 后台化。** 必须用 `terminal(background=true)` 启动服务，再用 `terminal()` 做 health check：

```python
# 步骤1：后台启动
terminal("cd ~/.openclaw/workspace/hot-aggregator && node --import tsx index.mjs", background=True)

# 步骤2：等10秒后验证
terminal("sleep 10 && curl -s --connect-timeout 5 'http://localhost:6688/api/all' | head -c 200")
```

```bash
cd ~/.openclaw/workspace/hot-aggregator && node --import tsx index.mjs
```

端口：6688

> 启动后需等 5~10 秒完成首次数据抓取再调用 API。

## 抓取数据

```bash
# 保存到文件（响应约1.6MB，直接管道可能截断）
curl -s "http://localhost:6688/api/all" -o /tmp/hotspots.json
```

## KOL微博观点（已移至角度选择环节）

**⚠️ KOL微博观点分析已从「抓热点」移到「角度选择」环节（2026-06-15调整）。**

原因：KOL的声音价值在于提供**角度和定调参考**，而不是发现热点。热点应该从平台热榜+RSS+关键词搜索中发现，KOL的观点用来丰富已确认选题的切入角度。

**抓热点阶段：** 不运行 weibo-topic-signal。只从平台数据发现热点。
**角度选择阶段：** 用户确认选题后，运行 weibo-topic-signal 抓取相关KOL的48-72小时发言，作为角度参考。

详见 `article-pipeline` 的 Step 3 角度选择。

**API 响应格式（重要）：**
```json
{
  "total": 2905,
  "updateTime": "2026-05-30T03:21:23.781Z",
  "data": [
    {
      "name": "weibo",
      "title": "微博",
      "type": "热搜榜",
      "total": 52,
      "fromCache": true,
      "data": [
        {"id": "...", "title": "热点标题", "desc": "描述", "url": "..."}
      ]
    },
    ...
  ]
}
```
遍历路径：`response.data[].data[]` → 每个 item 有 `title`, `desc`, `url` 字段。

**国际RSS源（必须并行抓取，48h时间窗口）：**

```python
# 国际RSS源列表
RSS_SOURCES = [
    ("TechCrunch", "https://techcrunch.com/feed/"),           # 全球科技新闻
    ("TheVerge", "https://www.theverge.com/rss/index.xml"),   # 科技+消费电子
    ("Wired", "https://www.wired.com/feed/rss"),              # 科技文化
    ("ArsTechnica", "https://feeds.arstechnica.com/arstechnica/index"),  # 深度科技
    ("MIT-TR", "https://www.technologyreview.com/feed/"),     # MIT科技评论
    ("HN-AI", "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+Claude+OR+DeepSeek&count=30&points=20"),  # HN AI讨论
    ("ProductHunt", "https://www.producthunt.com/feed"),      # 每日新产品
    ("9to5Mac", "https://9to5mac.com/feed/"),                 # 苹果生态
    ("TheVerge-Gadgets", "https://www.theverge.com/rss/gadgets/index.xml"),  # 3C硬件
    ("TheVerge-Transport", "https://www.theverge.com/rss/transportation/index.xml"),  # 汽车
    ("GoogleAI", "https://blog.google/technology/ai/rss/"),   # Google AI
    ("36Kr", "https://36kr.com/feed"),                        # 36氪全球
    ("Engadget", "https://www.engadget.com/rss.xml"),         # 3C消费电子（2026-06-04新增）
    ("GSMArena", "https://www.gsmarena.com/rss-news-reviews.php3"),  # 手机评测（2026-06-04新增）
]
```

**RSS抓取注意事项：**
- 用 `xml.etree.ElementTree` 解析RSS/Atom
- **必须72h时间窗口过滤**：解析 `pubDate`/`updated`，丢弃超过72h的条目（否则OpenAI博客返回978条历史、arXiv返回全部论文）
- OpenAI博客特别处理：只保留标题含 `launch/announce/release/new/partnership/GPT/Sora` 等新闻信号的条目
- 超时10秒/源，失败跳过不重试

**⚠️ RSS源可靠性实测（2026-06-04 更新）：** RSS源可用性波动大，每次需实测。最新数据：
- **稳定出数据：** TheVerge(~10条), Wired(~50条), ProductHunt(~20条), TechCrunch(~20条), 9to5Mac(~49条), ArsTechnica(~20条), HN-AI(~25条), 36Kr(~30条), Engadget(~20条), GSMArena(~20条), cnBeta(~150条)
- **少量数据：** TheVerge-Gadgets(~6条), MIT-TR(~5条), TheVerge-Transport(~1条), GoogleAI(~1条)
- **家居补充源稳定：** IT之家(~60条), 爱范儿(~15条) — 连续3天出数据，可信赖
- **历史为0的源恢复：** Wired(6/1未测→6/4=50), 36Kr(6/1=0→6/4=30), 9to5Mac(6/1=0→6/4=49)
- **结论：** RSS源可用性随时间波动，不可假设某源永远不可用。每次抓取都应尝试全部源，超时10秒/源即跳过。详细历史数据见 `references/rss-source-reliability.md`。

**⚠️ SMZDM cookie抓取不可靠（2026-06-01）：** 用requests+cookie访问SMZDM热榜/搜索页，正则提取标题全部返回0条。原因：SMZDM页面结构变化频繁，正则模式失效。备选方案：(1) 尝试`BeautifulSoup`解析而非正则；(2) 接受SMZDM作为低优先级数据源，不依赖它。

**家居补充RSS（72h窗口，hot-aggregator天然缺失家居内容，2026-06-04扩充）：**
- IT之家RSS: `https://www.ithome.com/rss/`（含家电/清洁/个护，~60条/天）
- 爱范儿RSS: `https://www.ifanr.com/feed`（含智能家居/新品，~15条/天）
- **TheVerge SmartHome**: `https://www.theverge.com/rss/smart-home/index.xml`（~10条/天，智能家居产品评测）
- **HomeKit News**: `https://homekitnews.com/feed/`（~10条/天，Matter/HomeKit生态，含追觅/石头等产品评测）
- **Home Assistant Blog**: `https://www.home-assistant.io/atom.xml`（~20条/天，智能家居平台生态）
- 家居关键词：追觅/石头/云鲸/科沃斯/戴森/徕芬/添可/扫地机/洗地机/吸尘器/吹风机/净水器/智能门锁/智能马桶/空气炸锅/智能家居/米家/Aqara

**搜索引擎限制（重要）：** DDG/Google/Bing均屏蔽服务器IP（返回首页或验证码），热点搜索只能依赖RSS+hot-aggregator。不要浪费时间尝试搜索引擎。

## 处理流程

1. 合并两个来源的数据
2. **三品类分类过滤**（汽车 + 3C数码 + AI/机器人），规则见下方
3. **黑名单排除误匹配**（三星堆≠三星电子、眼镜王蛇≠眼镜产品、军事无人机≠消费无人机等）
4. **噪音平台过滤**（linuxdo/csdn/huggingFace等开发者社区只保留真正AI大新闻）
5. **去重+按关键词命中数排序**
6. 输出各品类 **5~8 条精选**，格式：

```
## 🚗 汽车热点精选
① [平台] 标题 — 一句话描述价值
...

## 🤖 科技/AI 热点精选
① [平台] 标题 — 一句话描述价值
...

## 🏠 家居/生活热点精选
① [平台] 标题 — 一句话描述价值
...
```

每个品类 3-5 条，总共 8-12 条精选。

### ⚠️ 关键词过滤策略（重要 pitfall）

**三品类关键词体系：**

| 品类 | 关键词类型 | 示例 |
|------|-----------|------|
| 汽车 | 品牌+事件双命中 | 比亚迪/蔚来/理想/问界/特斯拉 + 上市/发布/预售/大定/智驾/SUV |
| 汽车 | 品牌+人物 | 雷军/余承东/王传福/李斌/何小鹏 |
| 3C数码 | 三层过滤：品牌+事件双命中 → 排除游戏/汽车/OpenAI博客 → 排除噪音平台 | 苹果/iPhone/大疆/影石/OPPO/vivo + 发布/降价/新品（详见 `references/3c-noise-blacklist.md`） |
| AI | 品牌+事件双命中 | Claude/DeepSeek/OpenAI/Anthropic + 融资/估值/IPO/大模型/AGI/机器人/蒸馏/AI安全 |

**黑名单模式（排除误匹配）：**
- 三星 → 排除: 三星堆、三星海力士杠杆
- 眼镜 → 排除: 眼镜王蛇、眼镜蛇
- 充电 → 排除: 充电后自燃、充电起火
- 发布 → 排除: 停售通知、红色预警、主题曲、问责通告、律师函
- 稳定器 → 排除: 尼克尔(镜头≠稳定器)
- 无人机 → 排除: 袭击、残骸、军事(消费无人机≠军事无人机)

**噪音平台：** linuxdo/csdn/huggingFace/hostloc/v2ex/newsmth/nodeseek — 开发者社区只保留真正AI大新闻（需命中AI品牌词+事件词）

**家居补充RSS（72h窗口，hot-aggregator天然缺失家居内容，2026-06-04扩充）：**
- IT之家RSS: `https://www.ithome.com/rss/`（含家电/清洁/个护，~60条/天）
- 爱范儿RSS: `https://www.ifanr.com/feed`（含智能家居/新品，~15条/天）
- **TheVerge SmartHome**: `https://www.theverge.com/rss/smart-home/index.xml`（~10条/天，智能家居产品评测）
- **HomeKit News**: `https://homekitnews.com/feed/`（~10条/天，Matter/HomeKit生态，含追觅/石头等产品评测）
- **Home Assistant Blog**: `https://www.home-assistant.io/atom.xml`（~20条/天，智能家居平台生态）
- 家居关键词：追觅/石头/云鲸/科沃斯/戴森/徕芬/添可/扫地机/洗地机/吸尘器/吹风机/净水器/智能门锁/智能马桶/空气炸锅/智能家居/米家/Aqara

**RSS源完整列表、RSSHub部署、SMZDM cookie配置** 见 `references/rsshub-deployment.md`
**过滤器调优记录：** `references/filter-tuning-log.md`（2026-06-07，8项修复从23→42条，含英文AI事件词、72h时间窗口、趋势品类、去重逻辑等）

**RSS源可靠性实测数据** 见 `references/rss-source-reliability.md`（记录各源实际返回情况，优先使用可靠源）
**3C品类噪音黑名单** 见 `references/3c-noise-blacklist.md`（游戏/汽车/OpenAI博客/噪音平台的完整排除模式）
**家居品类覆盖缺口分析** 见 `references/home-category-coverage-gap.md`（结构性稀缺原因+备选方案）
**家居RSS源扩充调研** 见 `references/home-rss-expansion-research.md`（国际可用源+失败源+中文替代方案）
**过滤器调优历史** 见 `references/filter-tuning-history.md`（每次调优的具体变更、效果数据、后续方向）

**Twitter AI 大佬追踪（page-agent + CDP 混合方案，2026-06-23 更新）：**

CDP端口3456。Twitter 已登录（cookie `~/.hermes/cookies/twitter.json`）。

```bash
# 一键提取 AI 大佬推文（CDP 模式，自动绕过 x.com CSP）
python3 ~/.hermes/scripts/pa_web_extract.py --twitter --output /tmp/twitter_ai.json

# 指定账号
python3 ~/.hermes/scripts/pa_web_extract.py --twitter --accounts "sama,karpathy,DarioAmodei" --output /tmp/twitter_ai.json

# 附加关键词
python3 ~/.hermes/scripts/pa_web_extract.py --twitter --keyword "GPT" --output /tmp/twitter_ai.json
```

输出格式：
```json
{
  "source": "twitter_cdp",
  "timestamp": "2026-06-23T14:26:08Z",
  "total": 4,
  "tweets": [
    {"name": "Elon Musk", "handle": "@elonmusk", "text": "...", "time": "2026-06-18T16:30:39Z", "likes": "2.6万"},
    ...
  ]
}
```

**⚠️ x.com CSP 限制：** page-agent 的 LLM API 调用被 x.com 的 CSP 拦截（Network request failed）。Twitter 必须用 CDP 直接提取模式（手写选择器），不能用 page-agent 的自然语言模式。其他站点（tophub/百度/SMZDM）可以用 page-agent。
```

追踪的AI大佬名单：见上方Twitter AI大佬追踪章节。

**Cookie存储：** Twitter/SMZDM 的既有配置只用于各自明确允许的适配器；内容创作流禁止读取任何小红书 Cookie。

**数据源优先级：** hot-aggregator(国内69平台) > 国际RSS(48h窗口) > Twitter AI大佬(cookie+CDP) > 家居RSS(IT之家+爱范儿) > SMZDM > RSSHub(少数派矩阵+36氪)。个人登录态小红书不在来源清单中。

**⚠️ Twitter CDP搜索返回空页面（2026-06-01）：** 页面导航成功（URL正确），但 `document.body.innerText.length` 为0。可能原因：(1) Twitter/X要求登录态才能显示搜索结果；(2) cookie注入方式不正确（cookie.json格式可能与CDP setCookie不兼容）；(3) 搜索结果页需要JS渲染但CDP未等待。**故障排除步骤：** 先检查bodyLen是否>0；如果为0，尝试先访问x.com/home确认登录态，再导航搜索页；仍然为空则跳过Twitter源。

**数据源优先级：** hot-aggregator(国内69平台) > 国际RSS(48h窗口，TheVerge系最可靠) > 家居RSS(IT之家+爱范儿，不稳定) > SMZDM > Twitter(CDP，需单独授权)。个人登录态小红书永久排除。
**搜索引擎不可用**（DDG/Google/Bing均屏蔽服务器IP），不要浪费时间尝试。
**⚠️ 数据时效性（2026-06-07 更新）：** 
- 时间窗口已从48h放宽到**72h**——热榜数据75%超过48h，放宽后保留量从591→627条，多捞出趋势类话题（新能源车涨价、二手油车崩盘等）。
- **已知异常：** `toutiao`（头条）的 timestamp 字段为负值或极小值，已自动跳过。
- **每次抓取仍必须：** 重启hot-aggregator → 拉最新数据 → 运行 filter 脚本。
- **时间戳格式详情** 见 `references/timestamp-format.md`。

**⚠️ RSS日期解析必须处理时区（2026-06-09 教训）：** `datetime.strptime()` 解析RSS日期时，部分格式返回 timezone-naive datetime（无tzinfo），与 timezone-aware 的 `cutoff` 比较会抛 `TypeError: can't compare offset-naive and offset-aware datetimes`。修法：解析后强制补时区：`if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)`。同样适用于Atom格式的 `updated`/`published` 字段。

**⚠️ RSS数据格式与过滤脚本不兼容（2026-06-03 发现）：** 内联RSS fetch脚本输出字段为 `source/title/url/date`，但 `scripts/filter_all_categories.py` 期望 `pubDate/desc`。解决方案：(1) 写内联过滤脚本直接处理；(2) 在fetch后做字段映射。用内联脚本更可靠，因为已有过滤脚本的RSS解析逻辑可能与实际fetch格式不一致。

**⚠️ OpenAI博客历史条目污染（2026-06-03 发现）：** 48h过滤后OpenAI博客仍返回大量历史文章（"GPT-4"、"Sora System Card"等），因为这些文章的pubDate可能在48h内被更新。修法：OpenAI博客条目额外过滤，只保留标题含 `launch/announce/release/new/partnership/introduce/deploy/2026` 等新闻信号的条目。

**⚠️ 交叉平台验证步骤（2026-06-03 新增）：** 在筛选阶段，用Python在hot-aggregator原始数据中搜索候选话题的关键词，统计跨平台出现次数。跨3+平台的话题传播势能更高，优先级应提升。此步骤应在五问审查之前执行，帮助判断传播势能。

**⚠️ AI品类后处理清理步骤（2026-06-03 新增）：** 初筛后AI品类可能仍有600+条，需二次清理：
1. **OpenAI博客过滤**：`source=='openai'` 的条目只保留标题含新闻信号词的（launch/announce/release/new/partnership/introduce/deploy/2026）
2. **噪音平台过滤**：linuxdo/csdn/huggingFace/v2ex/nodeseek/hostloc/tieba 的条目只保留score≥7的
3. **交叉品牌误匹配**：OPPO/Intel/nova/ROG等短品牌词容易误匹配英文标题，需在AI品类中排除纯英文标题的误命中

**⚠️ 新发现的误匹配模式（2026-06-03）：**
- **"理想"品牌误命中**：AUTO品类中"理想"匹配了"尼克尔镜头开发者访谈"（镜头描述中出现"理想"一词）。修法：AUTO品牌词"理想"需搭配汽车语境（车/SUV/轿车/交付/销量等）才归类
- **"龙头"误命中**：HOME品类中"龙头"匹配了"联想要当中小企业AI时代的摆渡人"。修法：HOME品类词"龙头"（水龙头）需搭配卫浴/厨房语境才归类
- **"RTX"误匹配**：3C品类中"RTX"匹配了OpenAI博客文章。修法：英伟达相关关键词需在中文语境中出现才归3C

**⚠️ AI品类过滤天花板（2026-05-30~31 实测）：** v1=763条→v3=211条，品牌+事件双命中+噪音平台排除+跨品类分流后，AI仍有211条。根因：hot-aggregator 69平台中大量科技新闻含"芯片""推理""训练"，关键词过滤无法区分AI大模型新闻和普通半导体新闻。**解决方案：AI品类切换到Twitter/X数据源**——用xurl追踪AI行业大佬（Sam Altman/Karpathy/Dario Amodei等），信号密度远高于关键词过滤。见 `references/ai-twitter-sourcing.md`。xurl已安装在 `~/.local/bin/xurl`，需用户配置X API凭证后启用。

**⚠️ 48h时间窗口必须生效（2026-06-04 修复）：** hot-aggregator 的"热榜"75%数据超过48小时。筛选脚本 filter_all_categories.py 已内置 timestamp 过滤（line 209-227），但需注意：toutiao 等平台 timestamp 格式异常（负值），会被自动跳过。

**⚠️ 新闻聚合源只用标题分类（2026-06-04 修复）：** geekpark/36Kr/ifanr 等"极客早知道"类文章的 desc 包含多个不相关话题，用 desc 分类会产生误匹配（如孙正义文中出现"丰田"+"上市"被误判为汽车上市）。ROUNDUP_SOURCES 列表中的源只用 title 做分类。

**⚠️ "上市"关键词太宽泛（2026-06-04 修复）：** auto_events 中的"上市"会匹配股市IPO/上市申请等非汽车语境。已改为"新车上市|正式上市|车型上市"。

**⚠️ 3C弱匹配噪音多（2026-05-30 教训）：** 3C类纯品牌命中（无事件信号）产出大量误匹配：华硕→纹眉、OPPO→母亲节文案、索尼→PSN头像、路由器→怎么摆。修法：3C必须有事件信号(发布/降价/上市等)才归类，纯品牌丢弃。见3C黑名单模式。

**⚠️ 3C品类跨域噪音严重（2026-06-04 实测）：** 即使品牌+事件双命中，3C仍有225条噪音。根因：
- **OpenAI博客污染**：大量文章标题含"NVIDIA"（如"How NVIDIA engineers build with Codex"），但实际是AI基建内容不是3C产品新闻。修法：`source=='openai'` 的条目**不归3C**，只归AI。
- **游戏内容泄漏**：PS5/Steam/Switch/王者荣耀/LPL等匹配"索尼""任天堂"品牌词。修法：3C黑名单必须包含完整游戏关键词列表（王者荣耀|英雄联盟|LPL|原神|鸣潮|明日方舟|崩铁|宝可梦|二次元|动漫|电竞|选手|战队|喜加一|免费领|兑换码）。
- **汽车内容泄漏**：华为乾崑/奕境等含"华为"品牌词。修法：华为相关条目需排除汽车语境（问界|智界|享界|尊界|途灵|乾崑|奕境|比亚迪|蔚来|小鹏|理想|零跑|特斯拉|汽车|车型|SUV|轿车|大定|交付|销量|智驾）。
- **噪音平台漏网**：huggingFace技术博客匹配"Intel""NVIDIA"。修法：噪音平台（huggingFace/nodeseek/linuxdo/csdn/v2ex/ngabbs/douban-group/tieba/newsmth/hostloc/guokr/hackernews）的3C条目**全部排除**，只对AI品类保留。
- **结论：3C需要三层过滤**：(1)品牌+事件双命中 → (2)排除游戏/汽车/OpenAI博客 → (3)排除噪音平台。

**⚠️ 家居品类扩充后仍偏少（2026-06-04 更新）：** 经扩充3个国际家居RSS源（TheVerge-SmartHome/HomeKit-News/HomeAssistant）+ 英文关键词后，家居品类从2条提升到**6条**（含追觅扫地机/SwitchBot收购/Matter窗帘电机等）。但仍远少于汽车(12)/3C(30)/AI(28)。根因：中文家居媒体（好好住/住小帮/一条/良仓）**全都没有RSS**，家居数据只能靠国际智能家居媒体+IT之家/爱范儿少量内容。选题筛选时家居<10条是常态，不强求配比；进一步扩充使用 SMZDM 和公开 RSS，不使用个人登录态小红书。

**⚠️ 新增可用RSS源（2026-06-04 验证）：** Engadget(20条/天, 3C消费电子)、GSMArena(20条/天, 手机评测)、cnBeta(150条/天, 科技综合)。已纳入国际RSS抓取列表。

**⚠️ 家居高频词误匹配（2026-05-30 教训，2026-06-04 更新）：** "美的""老板""海尔""格力""石头"是中文高频词，"杨紫说想多尝试不完美的角色"命中"美的"、"老板说要涨薪了"命中"老板"、"李晨 被误会的心形石头"命中"石头"、"格力电器持股变动"命中"格力"。修法：高频词必须有家居上下文(家电/家居/厨卫/卫浴/清洁等)才归类。

**⚠️ 英文品牌误匹配（2026-06-04 教训）：** "Shark"匹配电竞队名"天禄 vs sharks"、"Ring"匹配普通英文单词"ring ring"。修法：Ring/Nest 从品牌列表移除（改为产品关键词匹配）；Shark 加黑名单（vs/战队/esports）。黑名单检查改为大小写不敏感。

**⚠️ 飞利浦显示器误匹配（2026-06-04 教训）：** "飞利浦"品牌匹配了显示器新闻。修法：飞利浦加黑名单（显示器/显示屏/Monitor）。

**⚠️ 英文RSS源需要英文关键词（2026-06-04 教训）：** filter_all_categories.py 原本只有中文关键词，国际家居RSS（TheVerge-SmartHome/HomeKit-News/HomeAssistant）的英文内容被静默丢弃，家居品类从5源78条RSS中只筛出1条。修法：家居品类的 brand 和 products 正则必须同时包含中英文关键词（Dreame/Roborock/SwitchBot/robot vacuum/smart lock/matter/homekit 等），且 `re.search` 需加 `re.I` 标志。

**⚠️ 过滤规则调优记录（2026-06-07 教训）：** 用户反馈"按照现在的规则没什么可写的"——诊断发现5个结构性问题导致2900条原始数据只筛出23条可用：
1. **时间窗口太严：** 48h过滤掉79%数据。热榜是"正在热门"不是"刚发布"，放宽到72h。
2. **AI事件关键词只有中文：** 英文RSS（TechCrunch/Wired/ArsTechnica等）的品牌命中但事件未命中，OpenAI/Anthropic大新闻被漏。修法：ai_events正则加入英文事件词（launch/announce/release/unveil/raise/funding/valuation/acquire/partnership/deploy/security/regulation/billion/million等）。
3. **汽车品牌列表缺漏：** 红旗、捷途、星途、银河、极越、奕境、极石不在列表。修法：定期检查并补充新品牌。
4. **事件关键词太窄：** "涨价""新能源""电动车""造车""车企"等汽车行业通用词不在auto_events中。"成本""能耗""效率""数据中心"等AI行业词不在ai_events中。修法：扩充事件词列表。
5. **无"趋势/行业"品类：** "多款新能源车涨价了""美国芯片股集体下跌""AI监考"等无品牌但有行业趋势信号的条目无法归类。修法：在classify()函数末尾新增趋势品类，用高信号关键词（趋势auto: 新能源车涨价|造车新势力|车市|动力电池|固态电池等；趋势AI: AI监考|AI就业|AI成本|芯片股|算力中心等）匹配。

**调优效果：** 23条→51条（+122%），AI品类从1→22条。

**⚠️ 噪音平台过滤要适度（2026-06-07 教训）：** NOISE_PLATFORMS硬排除了linuxdo/nodeseek等平台的所有内容（仅允许核心AI大新闻），但这些平台偶尔有高质量技术讨论。当前策略"只保留核心AI品牌词命中"是合理的，不需要放宽。

**⚠️ 常见英文单词做品牌名的误匹配（2026-06-04 教训）：** Ring（智能门铃）和 Nest（智能恒温器）是常见英文单词，带 `re.I` 匹配时会命中大量无关文章（"ring ring"、"bird's nest"等）。Shark（扫地机品牌）匹配电竞队名。修法：**从品牌列表中移除 Ring/Nest/Shark**，改用产品关键词匹配（video doorbell/smart thermostat），或将这些词加入黑名单的大小写不敏感检查。

**⚠️ 过滤器优化汇总（2026-06-08 更新）：** `filter_all_categories.py` 经过以下优化后，从 23 条提升到 42 条（+83%）：
1. **时间窗口 48h→72h**：热榜数据 79% 超过 48h，放宽到 72h 多保留 36 条
2. **AI 英文事件关键词**：新增 30+ 英文词（unveil/equity/stake/comply/launch/announce 等），国际 RSS 的 AI 品类从 1→13 条
3. **汽车品牌扩充**：新增红旗/捷途/星途/银河/极越/奕境/极石
4. **汽车事件词扩充**：新增涨价/新能源/电动车/造车/车企/硬派
5. **趋势品类**：新增无品牌趋势关键词（AI监考/AI搜题/芯片股/太空算力/新能源车涨价/二手油车崩盘），需在标题中命中
6. **噪音平台收紧**：要求品牌+事件双命中才放行（之前只看品牌）
7. **OpenAI 博客过滤**：营销/case study 内容排除
8. **RSS 长文源**：Wired/ArsTechnica/TechCrunch 等只用标题匹配（避免 desc 误匹配）
9. **去重**：标题词重叠>30% 只保留第一条
10. **AI 黑名单扩充**：开发者教程/宠物故事/使用教程/无关行业

**⚠️ 黑名单检查必须大小写不敏感（2026-06-04 教训）：** filter_all_categories.py 的全局黑名单检查 `if kw in text` 是大小写敏感的，但品类匹配用了 `re.I`。导致 "shark"（小写）命中品牌词但 "Shark"（大写黑名单key）在 `text` 中找不到 → 黑名单失效。修法：(1) 全局黑名单检查改为 `kw.lower() in text.lower()`；(2) `is_blacklisted()` 函数内部也改为大小写不敏感比较。

**⚠️ 家居高频词扩展（2026-06-04 更新）：** HOME_HIGH_FREQ 除原有的"美的/老板/海尔"外，还需加入"格力"和"石头"——"格力"是中文"风格/力度"的常用词，"石头"是人名/普通名词。高频词必须搭配家居上下文（家电/清洁/扫地/智能家居等）才归类。

**⚠️ 飞利浦跨品类误匹配（2026-06-04 教训）：** "飞利浦"既是家居品牌（电动牙刷/空气净化器）也是3C品牌（显示器/显示器）。修法：家居黑名单中添加"飞利浦→排除：显示器/显示屏/Monitor"。

**⚠️ 英文源需要英文关键词（2026-06-04 修复）：** filter_all_categories.py 原来只有中文关键词，TheVerge-SmartHome/HomeKit-News/HomeAssistant 等英文RSS的内容被静默丢弃。已添加英文品牌名(Dreame/Roborock/SwitchBot/Dyson/iRobot等)+英文产品词(robot vacuum/smart lock/matter/homekit等)。家居品类从1→5条。

**⚠️ 黑名单检查必须大小写不敏感（2026-06-04 修复）：** "Shark"品牌匹配了电竞队名"天禄 vs sharks"，因为黑名单key首字母大写而匹配词小写。已改为全局大小写不敏感检查。同理，高频词"格力""石头"加入HOME_HIGH_FREQ需上下文验证（格力电器股价≠家电，石头Roborock≠普通"石头"一词）。

**⚠️ 家居品类扩充（2026-06-04）：** 新增3个国际RSS源：TheVerge-SmartHome、HomeKit-News、HomeAssistant Blog。家居从2源→5源，筛选结果从1→6条。详见 `references/rss-source-reliability.md`。

**⚠️ 品类过滤优化（2026-06-07 更新）：** 过滤脚本经历5轮调优，从23条→42条（+83%）：
- **英文AI事件词**：国际RSS用英文写标题，原脚本只有中文事件词导致AI品类仅1条。加了30+英文词（unveil/equity/stake/comply/launch/announce等）后AI从1→13。
- **汽车品牌补全**：红旗/捷途/星途/银河/极越/奕境/极石等缺失品牌已补入。
- **趋势品类**：新增无品牌趋势关键词（"新能源车涨价""AI监考""芯片股暴跌"等），解决58条有关键词但无法归类的问题。趋势关键词**必须在标题中命中**，不能只在desc中。
- **噪音平台收紧**：linuxdo/csdn等噪音平台现在要求品牌+事件双命中才放行（之前只要品牌有AI关键词就放行，导致开发者教程被保留）。
- **RSS长文源**：Wired/ArsTechnica/TechCrunch等长文源改为只用标题匹配（避免desc中的无关话题导致误匹配）。
- **OpenAI博客过滤**：营销内容（How.*redesign/case study/leveraging）被过滤，只保留新闻。
- **去重逻辑**：标题词重叠>30%的同品类条目只保留第一条。

**⚠️ 中文标题聚类必须用关键词提取，不能用空格分词（2026-06-14教训）：** `title_words()` 用空格分词对中文无效（中文标题没有空格），导致「凡人修仙传前2集」和「凡人这两集」overlap=0，同一话题无法聚类。修法：溢出热点检测改用 `extract_keywords()` 提取2-4字连续中文实体词，用关键词交集做相似度匹配。详见 `scripts/filter_all_categories.py` 中的 `char_ngrams()` 和 `topic_cluster()` 函数。

**⚠️ 中文标题聚类必须用关键词提取，不能用空格分词（2026-06-14教训）：** `title_words()` 用空格分词对中文无效——「凡人修仙传前2集」和「凡人这两集」分词结果完全不同，overlap=0，聚类失败。改用 `extract_keywords()` 提取2-4字连续中文片段作为关键词，再做交集匹配。已修复到 filter_all_categories.py 的溢出检测模块。

**⚠️ 用户明确要求：丰富技能/改善漏洞类操作无需确认直接执行（2026-06-14）。** filter_all_categories.py 现在会自动检测跨3+平台的未归类超级热点。使用中文关键词提取（2-4字实体词）做话题聚类，输出在筛选结果末尾的「🔥 溢出热点」区域。溢出数据同步存入 `/tmp/filtered_daily.json` 的 `overflow` 字段。典型场景：凡人修仙传（娱乐）、世界杯（体育）、SpaceX评论（国际）等不在四品类内但热度极高的话题。

**不要用单字关键词**如"车""汽""发布""上市"——命中率极高但绝大部分是噪音（"上京东买手机""发布会""上市辅导"等）。

**正确做法：两层过滤**（已有脚本 `scripts/filter_all_categories.py` 已实现此逻辑，直接运行即可）
1. **第一层：品牌/人物/事件硬关键词**（必须命中至少1个）
2. **第二层：上下文验证**——检查匹配词周围是否有汽车语境，排除误命中

⚠️ **必须使用已有脚本：** `scripts/filter_all_categories.py`（v3：含跨品类品牌分流+3C黑名单+AI收紧规则+噪音平台硬排除）。**不要从头写过滤脚本**——直接运行：
```bash
python3 scripts/filter_all_categories.py /tmp/hotspots.json /tmp/rss_international.json /tmp/rss_home.json
```
脚本自动处理：噪音词排除、黑名单、跨品类品牌分流（华为/小米/三星/英伟达等）、3C黑名单、AI品牌+事件双命中、家居高频词上下文验证、趋势品类、去重。

**⚠️ filter_all_categories.py 关键修复（2026-06-07 更新）：**

5个结构性修复，将筛选结果从23条提升到42条（+83%）：

| 修复 | 改动 | 效果 |
|------|------|------|
| 时间窗口 | 48h→72h（热榜数据79%超48h） | 国内保留591→627条 |
| AI英文事件词 | 加30+英文词（unveil/equity/stake/comply等） | AI品类1→13条 |
| 汽车品牌 | +红旗/捷途/星途/银河/极越/奕境/极石 | 红旗G919首次命中 |
| 趋势品类 | 新增无品牌趋势关键词（标题必须命中） | +5条行业趋势文 |
| 噪音平台 | 要求品牌+事件双命中才放行 | 过滤开发者教程 |
| OpenAI博客 | 过滤营销/case study内容 | 去掉How.*redesign等 |
| RSS长文源 | Wired/Ars/TechCrunch等只用标题匹配 | 去掉desc误匹配 |
| 去重 | 标题词重叠>30%只保留第一条 | Trump/OpenAI去重 |

**关键pitfall：趋势关键词必须在标题中命中，不能只在desc中。** 实测"教育部高考十问十答"的desc含"AI监考"但标题无关，被误归AI。

**⚠️ 仍需同步更新（来自 references/）：** 新增的3C噪音模式（游戏/汽车/OpenAI博客/噪音平台）已记录在 `references/3c-noise-blacklist.md`，需同步到脚本的黑名单变量中。当前脚本可能缺少以下模式：
- 游戏黑名单：王者荣耀|英雄联盟|LPL|原神|鸣潮|崩铁|宝可梦|二次元|电竞|喜加一
- 汽车跨域排除：问界|智界|途灵|乾崑|奕境|汽车|车型|SUV|智驾
- OpenAI博客排除：source=='openai' 不归3C
- 噪音平台全面排除：huggingFace/nodeseek/linuxdo/csdn/v2ex/ngabbs/guokr/hackernews

## 公众号辅助搜索（可选，按需启用）

当 RSS + hot-aggregator 对某个品类覆盖不足时，用搜狗搜索公众号文章标题补充：

```bash
# 搜索特定品类的公众号文章（只搜标题不读正文，速度快）
python3 ~/.hermes/scripts/wechat_downloader.py search "智能家居 新品" --pages 1 --no-read
python3 ~/.hermes/scripts/wechat_downloader.py search "爱范儿 AI 芯片" --pages 1 --no-read
```

**使用场景：**
- 家居品类 RSS 只有 5-6 条 → 搜「智能家居」「扫地机器人」补充标题
- 深度选题需要更多角度 → 搜「虎嗅 汽车」「36氪 AI」看媒体视角
- 确认选题后需要素材 → 用 `read` 命令读取正文

**注意：** 搜狗搜索返回的是标题+链接，正文需要额外用 `read` 命令读取。搜狗反爬有时会失败（成功率 ~60-80%），失败即跳过。

**⚠️ Sogou WeChat反爬升级（2026-06-04 实测）：** headless Chrome 访问搜狗微信搜索 100% 被拦截（弹验证码页）。原因：搜狗检测 headless 浏览器指纹。即使在脚本中修改 CDP 端口、添加 `--remote-allow-origins=*` 也无法绕过。**解法**：(1) 用用户日常 Chrome（非 headless）+ remote debugging port，但需用户手动开启；(2) 直接用目标公众号的官网替代（如爱范儿→ifanr.com），官网无反爬；(3) 用 RSS feed 获取文章列表。**不要在 headless Chrome 上反复尝试搜狗搜索**，浪费时间。

## 周期性热点源（不依赖热榜，按日历主动触发）

有些热点不是「碰巧上了热搜」，而是每个月/每个季度固定会出现的。这些应该作为**主动触发的热点源**写入流程，不依赖 hot-aggregator 偶然抓到。

### 月初销量公布（每月1-3号）

**触发条件：** 每月1-3号自动执行，或用户说「看看上个月销量」时执行。

**数据源：**
- 各品牌官方公告（蔚来/理想/小鹏/零跑/比亚迪/问界等）
- 乘联会/中汽协月度数据
- 微博KOL转发和解读（weibo-topic-signal）

**热点判断标准：**
- 某品牌月销破纪录（如零跑首次月销8万+）
- 某品牌月销异常波动（环比下降30%+）
- 排名变化（某品牌首次超越另一品牌）
- 同比增长异常（翻倍增长或负增长）

**产出逻辑：** 销量数据本身不是文章，但可以从中提炼出标题先行的核心论点。例如：
- 零跑8万辆 → 「8万辆之后，零跑不再是新势力」（用丰田类比）
- 理想4万辆 → 「理想卖了4万台L8，但李想不开心」（用内部视角切入）
- 比亚迪30万辆 → 「比亚迪一个月卖30万台，但利润只有XX」（用成本结构切入）

**从热点到文章的完整路径：**
```
月初销量数据（热点）→ 筛选题（哪个数字最有故事？）→ 定标题（从数字里提炼反差/悬念/判断）→ 拆核心论点 → 找支柱类比 → 写正文
```

### 其他周期性热点源（按需补充）

- **新车发布会**（提前1-2天关注预售信息，发布会当天写快评）
- **财报季**（季度财报发布后48小时内）
- **车展/技术日**（北京/上海/广州车展，品牌技术日）
- **政策变化**（购置税、补贴、排放标准等政策公布时）

**问题：** hot-aggregator只抓已经登上热榜的内容。新车发布、价格公布等事件在发布初期尚未形成热点，会被过滤掉（如乐道L60上市当天未被抓到）。

**解决方案：** 新增一层关键词主动搜索。每次抓热点时，用品牌+车型+事件关键词组合搜索最新消息，捕获「刚发生还没火」的事件。

**关键词库：** `references/car-model-keywords.json`
- 涵盖新势力（蔚来/理想/小米/小鹏/零跑）、华为系（问界/智界/享界/尊界）、比亚迪系、传统+合资、数码科技、AI 六大品类
- 每个品牌含具体车型名（ES8、L60、YU7等）
- 事件关键词：上市、发布、预售、申报、交付、降价、碰撞测试、召回等

**搜索脚本：** `scripts/search_car_keywords.py`

**执行规范：**
```bash
# 在 hot-aggregator + RSS 抓取完成后，额外跑一轮关键词搜索
python3 scripts/search_car_keywords.py --hours 24 --max-searches 30 --output /tmp/car_keyword_results.json
```

**输出格式：** 按品牌分组的最新消息，可直接与 hot-aggregator 结果合并。

**⚠️ DDG搜索引擎限制：** DDG/Google/Bing均屏蔽服务器IP。search_ddg()可能返回空结果。**实际执行时应该在execute_code中用hermes_tools的web_search替代**，而不是用search_car_keywords.py的DDG lite。脚本作为关键词库的读取器仍可用，但搜索部分改用web_search。

```python
# 在execute_code中用web_search跑关键词搜索
from hermes_tools import web_search
import json
data = json.load(open('/Users/xxqq/.hermes/skills/sourcing-hotspots/references/car-model-keywords.json'))
for brand in ["乐道", "理想", "小米汽车", "问界", "比亚迪"]:
    r = web_search(f"{brand} 上市 发布 {datetime.now().strftime('%Y年%m月')}", limit=3)
    # process results...
```

**⚠️ 政策类热点是结构性盲区（2026-06-18 教训）：**
用户指出"新能源汽车下乡"等重要热点未被发现。根因：
1. hot-aggregator的关键词过滤是"品牌+事件双命中"——政策类新闻（汽车下乡、购置税调整、以旧换新、补贴政策）没有具体品牌词，只有行业趋势词
2. 政策新闻走的是国务院/工信部/商务部官网+央媒首发（人民日报、新华社），不在微博/知乎热榜上
3. 当前趋势品类关键词只覆盖了`新能源车涨价|新能源车降价`等市场类趋势，缺少政策类关键词

**修复方向（待实施）：**
- 在 filter_all_categories.py 的 trend_auto 中新增政策类关键词：`汽车下乡|下乡补贴|以旧换新|购置税|国补|车船税减免|充换电设施|县域充电|工信部.*通知|商务部.*通知|国务院.*汽车`
- 考虑新增政策类RSS源：中国政府网RSS、工信部官网、商务部官网
- 每次抓热点后，额外用 web_search 跑一轮政策类关键词搜索补盲

## 数据流：Skill 之间的数据传递

```
【消费】用户输入的指令/话题
【产出】原始热点列表（平台+标题+热度）
【本地】/tmp/article-pipeline/01-hotspots-raw.md
【Obsidian】~/Documents/Obsidian/汽车行业/流水线/01-hotspots-raw.md
【转发】→ screening-topics（用户说「筛一下」时）
          → framing-article（用户说「写这个」时）
【依赖】hot-aggregator 服务运行中
```

## 已知数据质量问题

**hot-aggregator 缓存问题（根因已修复 2026-06-01）：** 服务长时间运行后，大部分平台返回 `fromCache: True` 的陈旧数据。**每次抓取必须先 kill 再重启**，不能直接复用旧进程。健康检查脚本：`~/.hermes/scripts/check_hot_aggregator.py`（每2小时自动检查，缓存超30分钟自动重启）。**单独依赖 hot-aggregator 不够**，需配合国际RSS源补充。

**微博热搜 API 限制：** `weibo.com/ajax/side/hotSearch` 返回 `band_list: []`，被反爬。直接搜微博热点不可行，需通过 DuckDuckGo 或 tophub.today 绕行。

**百度/抖音/B站部分平台数据为空：** 正常现象，这些平台反爬严重。数据为空时以其他平台为主。

## 执行规范（必须遵守）

1. **调服务前先健康检查：** `curl -s --connect-timeout 3 http://localhost:6688/api/all -o /dev/null -w "%{http_code}"`，不通就尝试启动，启动后仍不通就跳过
2. **大数据量存文件再处理：** hot-aggregator 返回 ~1.6MB，禁止 pipe 到 Python 直接解析（会截断）。必须先 `curl -o /tmp/hotspots.json`，再离线 Python 处理
3. **禁止个人小红书登录态：** 不启动、不健康检查、不调用任何小红书 MCP、CLI、Cookie 或 CDP 路径。
4. **输出只发精选结果：** 原始数据不进对话，只输出最终 5-8 条精选 + 分类统计
5. **过滤时排除噪音：** 跳过含"喜加一"、"Epic"、"Steam"、"源码"、"开源软件"等无关条目

**小红书历史方案已停用：** 过去使用过 MCP、CLI、Cookie 和 CDP，但这些路径会借用个人登录态，现已全部禁止。小红书搜索结果也不是热榜，不得作为热点强度依据。

## 两段式热点输出

每次抓热点输出两个部分：

### 1. 我关注的热点

来源：hot-aggregator + RSS + 关键词搜索
执行：`python3 scripts/filter_all_categories.py /tmp/hotspots.json`
输出：汽车/3C/AI/家居四品类精选

### 2. 全网热点

来源：filter脚本自动检测（跨3+平台未归类条目）
执行：同上，自动输出在筛选结果末尾
输出：不在四品类内但热度很高的话题

**KOL微博观点不在抓热点阶段采集。** 在 angle-selection 的「第零步」采集（选题确认后），用于丰富角度和定调。

**两部分合并输出，格式：**
```
--- 我关注的热点 ---
（四品类内容）

--- 全网热点 ---
（溢出内容）
```

### 3. 结构化输出（供筛选Agent使用）+ 数据质量评估

热点数据输出后，必须经过**热点数据Agent**质量评估，然后生成结构化格式供筛选Agent使用。

**热点数据Agent prompt**：`references/hotspot-agent-prompt.md`（v2）

**热点数据Agent的职责**：
- 评估数据完整性、时效性、覆盖度
- **自动去重**：发现重复热点时合并
- **自动纠正分类**：足球/体育/娱乐归入全网热点
### 3. 结构化输出（供筛选Agent使用）

热点数据输出后，必须同时生成一份结构化格式，供筛选Agent使用。格式见 `references/message-format.md` 的"主Agent → 筛选Agent"部分。

**结构化格式模板：**
```
## 热点数据

- 编号: [数字]
- 标题: [一句话描述]
- 来源: [平台名称，如IT之家、微博、知乎]
- 时间: [今天/昨天/N天前]
- 平台数: [几个平台在讨论]
- 情绪强度: [高/中/低，如有评论数据可补充说明]
- 关键数据: [核心数字或事实]
```

**情绪强度判断标准：**
- 高：涉及品牌对比、价格争议、政策变化、人物争议，评论区有激烈讨论
- 中：有讨论但不激烈，主要是信息传递
- 低：几乎没有讨论，只是新闻报道

**主Agent负责从筛选结果中提取结构化数据，传给筛选Agent。**

**⚠️ 已知问题（2026-06-17 测试发现，已修复）：**
- 筛选Agent评分已升级为50分制（含全网热度维度），两层筛选（先全网后领域）
- 筛选Agent必须标注切入方向类型（故事/分析/预判/站队/类比）
- 主Agent应检查筛选Agent的输出是否符合格式要求，不符合就打回重来
- 「筛一下」→ 调用 `screening-topics`
- 「帮我看看这个能不能写」→ 先 `screening-topics`，再 `framing-article`
- 「直接写这个」→ 调用 `framing-article`
