# xiaohongshu-mcp 部署笔记

## 部署状态（2026-05-16）

### 环境
- macOS ARM64（Apple Silicon）
- xiaohongshu-mcp 版本：v2026.05.15.0445-dee6c25
- 部署方式：二进制直接运行（非 Docker）

### 关键路径
```
~/xiaohongshu-mcp/
├── xiaohongshu-mcp-darwin-arm64   # 主程序
├── xiaohongshu-login-darwin-arm64 # 登录工具
└── cookies.json                   # 工作目录下（不是 data/）
```

### Cookie 格式要求
MCP binary 期望 **Chrome NetworkCookie 数组格式**（`[]`），不是 key-value 格式（`{}`）。

原始 cookies 在 `~/.xiaohongshu-cli/cookies.json`（key-value 格式，21个字段）。

转换脚本：
```python
import json, httpx

raw = json.load(open(os.path.expanduser("~/.xiaohongshu-cli/cookies.json")))
converted = [{"name": k, "value": v, "domain": ".xiaohongshu.com",
               "path": "/", "secure": True, "httpOnly": False,
               "sameSite": "None", "session": False}
              for k, v in raw.items()]
json.dump(converted, open("cookies.json", "w"))
```

**⚠️ 放在工作目录，不是 data/ 子目录。** Binary 读取当前工作目录的 `cookies.json`。

### Cookie 数量
21个 cookies，转换后数组长度 = 21。

### 启动
```bash
cd ~/xiaohongshu-mcp
./xiaohongshu-mcp-darwin-arm64
# 默认 port: 18060
# 13 个 MCP 工具注册完成
```

### MCP 工具列表（13个）
check_login_status, delete_cookies, favorite_feed, get_feed_detail,
get_login_qrcode, like_feed, list_feeds, post_comment_to_feed,
publish_content, publish_with_video, reply_comment_in_feed,
search_feeds, user_profile

### API 调用限制
- `search_feeds`：只支持 `keyword` 参数，不支持 `page`/`page_size`
- `user_profile`：需要 `user_id`（必填），无默认值
- `list_feeds`：不支持分页参数

## Hermes 集成（via httpx 直连）

MCP SDK 的 `streamable_http_client` 在 anyio 4.12.1 + Python 3.11 下有兼容性问题（超时）。绕过方案：直接用 `httpx.Client` 同步发 HTTP 请求。

### 关键 headers
```python
_HEADERS = {
    "Content-Type": "application/json",
    "Mcp-Protocol-Version": "2025-03-26",
}
```

### Session 流程
```
POST /mcp  {method: initialize}           → Mcp-Session-Id header
POST /mcp  {method: notifications/initialized}
POST /mcp  {method: tools/call}           → 带上 Mcp-Session-Id
```

### 工具封装（tools/xiaohongshu_tool.py）
- `check_login_status()` → 验证登录
- `search_feeds(keyword)` → 搜索笔记
- `get_feed_detail(feed_id)` → 笔记详情
- `publish_content(title, content, images, topics)` → 发布图文

### Registry 注册问题
`xiaohongshu_tool.py` 的 `registry.register()` 包裹在 `try` 块里。
`discover_builtin_tools()` 的 AST 扫描默认不进入 `ast.Try` 节点。
需要在 `tools/registry.py` 的 `_is_registry_register_call()` 里增加对 `ast.Try` 的处理。