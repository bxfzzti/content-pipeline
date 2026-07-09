# daily-hot-mcp 工具清单与分类

## 📰 新闻 (12 tools)

| 工具名 | 描述 | 领域 |
|--------|------|------|
| `get-baidu-trending` | 百度热榜 - 实时热搜、社会热点、科技新闻 | 综合 |
| `get-toutiao-trending` | 今日头条热榜 - 时政、社会、国际、科技 | 综合 |
| `get-ithome-trending` | IT之家热榜 - 科技资讯、数码产品 | 科技/3C |
| `get-36kr-trending` | 36氪热榜 - 创业、商业、科技、投融资 | 商业/科技 |
| `get-netease-news-trending` | 网易新闻热点榜 - 时政、社会、财经、科技 | 综合 |
| `get-infoq-news` | InfoQ - 软件开发、架构、云、AI | 技术/AI |
| `get-thepaper-trending` | 澎湃新闻热榜 - 深度报道 | 综合 |
| `get-tencent-news-trending` | 腾讯新闻热点榜 - 国内外时事 | 综合 |
| `get-bbc-news` | BBC News - 全球、英国、商业、科技 | 国际 |
| `get-theverge-news` | The Verge - 科技创新、评测 | 科技/英文 |
| `get-9to5mac-news` | 9to5Mac - 苹果相关新闻 | 科技/苹果 |
| `get-ifanr-news` | 爱范儿科技快讯 - 科技产品、数码设备 | 科技/3C |

## 📱 社交媒体 (9 tools)

| 工具名 | 描述 | 领域 |
|--------|------|------|
| `get-weibo-trending` | 微博热搜榜 - ⚠️ 可能403被反爬 | 综合 |
| `get-zhihu-trending` | 知乎热榜 - 时事、科技、娱乐 | 综合/深度 |
| `get-douyin-trending` | 抖音热搜 - ⚠️ 可能403被反爬 | 综合 |
| `get-kuaishou-trending` | 快手热榜 - 热门短视频 | 综合 |
| `get-xiaohongshu-trending` | 小红书热榜 - 时尚美妆、生活方式 | 消费/生活 |
| `get-bilibili-trending` | B站热门视频 | 综合/年轻 |
| `get-hupu-trending` | 虎扑热榜 - 体育、男性生活 | 体育/生活 |
| `get-so360-trending` | 360热搜榜 - ⚠️ 可能403 | 综合 |
| `get-sogou-trending` | 搜狗热搜榜 - ⚠️ 可能403 | 综合 |

## 🎮 娱乐内容 (4 tools)

| 工具名 | 描述 | 领域 |
|--------|------|------|
| `get-bilibili-rank` | B站视频排行榜 - 动画、音乐、游戏 | 娱乐 |
| `get-douban-rank` | 豆瓣实时热门 - 图书、电影、电视剧 | 文化 |
| `get-weread-rank` | 微信读书排行榜 - 小说、畅销书 | 阅读 |
| `get-gcores-new` | 机核网 - 游戏资讯、评测 | 游戏 |

## 🚗 汽车 (1 tool)

| 工具名 | 描述 | 领域 |
|--------|------|------|
| `get-autohome-trending` | 汽车之家热榜 - 汽车新闻、新车、购车、试驾 | 汽车 |

## 🛒 生活方式 (2 tools)

| 工具名 | 描述 | 领域 |
|--------|------|------|
| `get-smzdm-rank` | 什么值得买热门 - 商品推荐、优惠、评测；不支持关键词 | 消费 |
| `search-product-experience-posts` | 产品体验搜索 - 按关键词搜索什么值得买原创/文章，补充少数派/Chiphell近期体验、开箱、横评、吐槽内容；返回 `creative_score` 和 `score_breakdown` | 产品体验/二创 |

> 注：少数派当前没有独立注册的 `get-sspai-rank` 工具；需要产品体验/数码生活补充时，统一通过 `search-product-experience-posts` 的 `sources="sspai"` 或默认组合源获取。
> 注：`search-product-experience-posts` 的二创分不使用阅读量；当前稳定字段是评论、收藏、点赞、发布时间、来源和内容类型。

## 🌐 其他 (2 tools)

| 工具名 | 描述 |
|--------|------|
| `custom-rss` | 自定义RSS订阅源（需配置 `TRENDS_HUB_CUSTOM_RSS_URL`） |
| `crawl_website` | 爬取网站内容（需配置 `FIRECRAWL_API_KEY`） |

## MCP 调用方式

所有工具通过 HTTP MCP 协议调用。Python 示例：

```python
import httpx, json

BASE = "http://localhost:8000/mcp"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

client = httpx.Client(timeout=30)

# 初始化会话
resp = client.post(BASE, headers=HEADERS, json={
    "jsonrpc": "2.0", "method": "initialize",
    "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "hermes", "version": "1.0"}},
    "id": 1
})
sid = resp.headers.get("mcp-session-id")

# 发送 initialized 通知
client.post(BASE, headers={**HEADERS, "Mcp-Session-Id": sid}, json={
    "jsonrpc": "2.0", "method": "notifications/initialized", "params": {}, "id": 2
})

# 调用工具
def call_tool(name, args=None):
    resp = client.post(BASE, headers={**HEADERS, "Mcp-Session-Id": sid}, json={
        "jsonrpc": "2.0", "method": "tools/call",
        "params": {"name": name, "arguments": args or {}},
        "id": 99
    })
    for line in resp.text.split('\n'):
        if line.startswith('data: '):
            d = json.loads(line[6:])
            c = d.get('result',{}).get('content',[])
            return c[0]['text'] if c else str(d.get('error',''))
    return None

# 用法: 所有工具需要传 {"args": {}}
result = call_tool("get-autohome-trending", {"args": {}})
result = call_tool("get-36kr-trending", {"args": {}})
```
