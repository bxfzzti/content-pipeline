# 飞书 Docx API 技术坑位（实测记录）

## 1. 列表块与 emoji/特殊字符不兼容

**现象：** `block_type=7`（ordered）和 `block_type=8`（unordered）的内容中如果包含 emoji（✅▸①②③等）或特殊 Unicode 字符，飞书 API 返回 400 Bad Request。不只是 emoji 前缀——内容任意位置的 emoji 都会触发。

**解决方案（已内置到 publish_to_feishu.py）：** 所有列表项统一转为普通段落（`block_type=2`），不再使用 `block_type=7/8`。这是最稳妥的方案，因为无法可靠预测哪些字符组合会触发 400。

**同时处理的 Unicode 字符：** em dash `—`（U+2014）、en dash `–`（U+2013）、省略号 `…`（U+2026）、弯引号 `''""`，在 `sanitize_text()` 中统一替换为 ASCII 等价物。

参考代码见 `scripts/publish_to_feishu.py` 中的 `sanitize_text()` 和 `md_to_blocks()`。

## 2. 引用块和分割线不支持

- `block_type=6`（引用块）→ 用斜体普通段落代替
- `block_type=16`（分割线）→ 用空格段落代替

## 3. 表格 block 写入受限

- `block_type=10/11`（table）有参数类型限制（9499 错误）
- 解决：转为文字段落「【表】列1 | 列2 | ...」格式

## 4. 50 blocks 批次限制

- `children` 数组每次最多 50 个，超出返回 `field validation failed`（code=99992402）
- 解决：分批调用

## 6. 读取飞书 Wiki 文档内容（2026-06-14 实测）

当用户给一个飞书 wiki 链接（`feishu.cn/wiki/xxx`），需要读取其内容时：

```python
# Step 1: 获取 tenant_access_token
import json, urllib.request, os
app_id = os.environ["FEISHU_APP_ID"]
app_secret = os.environ["FEISHU_APP_SECRET"]
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
    headers={"Content-Type": "application/json"}
)
token = json.loads(urllib.request.urlopen(req).read()).get("tenant_access_token")

# Step 2: wiki token → obj_token（wiki节点的实际文档token）
wiki_token = "从URL中提取"  # 例如 JjUuwhYk3iu69xk3u9Bc2OgsnVf
req2 = urllib.request.Request(
    f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={wiki_token}",
    headers={"Authorization": f"Bearer {token}"}
)
node = json.loads(urllib.request.urlopen(req2).read()).get("data", {}).get("node", {})
obj_token = node.get("obj_token")  # 文档的实际token
obj_type = node.get("obj_type")    # 通常是 "docx"

# Step 3: 读取文档原始内容
req3 = urllib.request.Request(
    f"https://open.feishu.cn/open-apis/docx/v1/documents/{obj_token}/raw_content",
    headers={"Authorization": f"Bearer {token}"}
)
content = json.loads(urllib.request.urlopen(req3).read()).get("data", {}).get("content", "")
```

**关键点：**
- wiki_token ≠ obj_token，必须先调 get_node 转换
- raw_content 返回纯文本（无格式），适合内容分析
- 如果需要结构化内容（标题/列表/表格），用 `GET /docx/v1/documents/{obj_token}/blocks` 分页获取
- `feishu_doc_read` 工具只在飞书评论上下文中可用，普通会话中需要用 API
- `web_extract` 对飞书域名返回空（被 block 为 private network）
- `browser_navigate` 需要 Chrome 以 `--remote-debugging-port` 启动才能连接

- 创建文档后需调用 `POST /drive/v1/permissions/{token}/members?type=docx` 给用户加 `full_access`
- 用户 open_id 从 `FEISHU_OWNER_OPENID` 环境变量读取
