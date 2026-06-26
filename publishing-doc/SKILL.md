---
name: publishing-doc
description: >
  飞书文档发布。接收正文markdown → 按飞书兼容排版 → feishu_create_doc → feishu_fetch_doc 回读校验。
  输出文档链接。
  Triggers — "发布", "创建文档", "飞书", "发文章", "publish", "create doc", "上传飞书"
---

# publishing-doc

接收正文 markdown → 按飞书兼容格式排版 → 创建/更新飞书文档 → 回读校验 → 输出文档链接。

## 飞书 Markdown 限制

只能用以下确定支持的元素：

| 元素 | 语法 | 用途 |
|------|------|------|
| 标题 | `## 标题` | 章节分界 |
| 引用块 | `> 内容` | 金句、引语 |
| 表格 | `| A | B |` | 对比数据 |
| 加粗 | `**文字**` | 关键词强调 |
| 行内代码 | `` `code` `` | 术语、参数 |
| 分割线 | `---` | 呼吸感 |
| 斜体 | `*文字*` | 外文、轻强调 |

**禁止使用：** `<callout>` `<grid>` `<text>` 等 Lark 扩展标签。会被存为纯文本。

**列表块已禁用（2026-06-08 修复）：** 飞书 `block_type=7`（有序列表）和 `block_type=8`（无序列表）与 emoji、特殊 Unicode 字符不兼容（返回 400）。`publish_to_feishu.py` 已将所有列表项统一转为普通段落（`block_type=2`），彻底避免此问题。无需在文章中规避列表语法。

**Unicode 字符自动清理：** `publish_to_feishu.py` 在转 blocks 之前自动将 em dash `—`、省略号 `…`、弯引号 `''""` 替换为 ASCII 等价物，避免 400 错误。无需手动预处理。

**注意：表格（block_type=10/11）** 飞书 docx API 的 table block 写入存在参数类型限制（9499 错误），**当前无法通过 API 创建表格**。文章含表格时，统一转为文字段落格式。有两种转换方式：

1. **简表用文字行：** `价格 | 华为FreeArc ¥499 | 小米耳夹 ¥799`（每行一组数据，用 `|` 分隔）
2. **对比表用加粗标签：** `**场景：** 运动跑步 → **推荐：** 华为FreeArc ¥499`

实测效果：2026-06-08 耳机横评文发布时，原稿有完整markdown表格，publish_to_feishu.py 自动跳过表格block，最终文档中表格部分以纯文本形式呈现。用户侧无明显感知差异，因为飞书文档中的文字排版本身就有对比效果。

如需真正表格，建议手动在飞书文档中插入。详见 `references/feishu-blocks.md`。

**注意：图片（block_type=27）** 飞书插入图片需要三步流程：
1. 创建空 image block：`{"block_type": 27, "image": {}}` → 拿到 block_id
2. 用 block_id 作为 parent_node 上传图片到 drive API → 拿到 file_token
3. 用 PATCH API 的 `replace_image` 把 file_token 设到 block 上

脚本：`scripts/add_images_to_doc.py`（三步流程已实现）
配图生成：`scripts/gen_chart.py`（柱状图/参数表/封面图）
XHS好物文配图：`scripts/gen_xhs_images.py`（HTML渲染→浏览器截图，9张产品卡片）




**禁止的行为：** 空行生成全角空格 block（`content: "　"`）来"模拟空行"——会导致文章出现大量多余空换挡。空行必须直接跳过，不生成任何 block。


**⚠️ 自动授权已内置：** `publish_to_feishu.py` 创建文档后自动给 `FEISHU_OWNER_OPENID`（默认 `ou_f735f02495560fb7243ca0f4d49f3d7b`）添加 full_access 编辑权限。无需手动操作。

**引用块和分割线限制：** 飞书 docx API 不支持 `block_type=6`（引用块）和 `block_type=16`（分割线）。引用块用斜体段落代替，分割线用空格段落代替。详见 `references/feishu-blocks.md`。

## 排版标准

1. **开篇引用块：** 必须是定调的提炼
2. **2-5个二级标题：** 章节分界
3. **必要时用表格：** 承载对比数据或结构拆解
4. **金句可加引用块：** 每个关键章节可用一句引用块收住
5. **不加固定尾部：** 文章写完直接结束。署名只用最小形式「—— 作者名」

## 发布步骤

### 前置检查（必做，不可跳过）

### 前置检查（必做）

发布前确认以下三项已通过：
- [ ] 数据验证（verify_facts.py）→ 无未验证的关键事实
- [ ] 独立质检（delegate_task）→ 无🔴必须修改项
- [ ] 配图已生成（gen_chart.py）→ 至少1张对比图或封面图

⚠️ **发布前必须先质检（2026-06-10教训）：** 曾经直接跳过质检发布3篇文章，用户指出「这三篇都没有走质检吧」。质检是发布前的硬性门槛，不能因为赶时间或文章看起来没问题就跳过。即使用户催着要，也必须先跑质检再发布。

### 发布文档

**方式一（推荐）：用复用脚本**

```bash
source ~/.hermes/hermes-agent/.venv/bin/activate
python3 ~/.hermes/skills/publishing-doc/scripts/publish_to_feishu.py /tmp/article-pipeline/04-article-draft.md "文章标题"
```

脚本自动完成：获取token → 创建文档 → md转blocks → 分批写入 → 回读校验 → **自动授权编辑权限**。输出 doc_id 和链接。

**自动权限：** 脚本会自动给 `FEISHU_OWNER_OPENID`（默认 `ou_f735f02495560fb7243ca0f4d49f3d7b`）添加 full_access 编辑权限，无需手动操作。

**方式二：手动分步调用**

> **2025-05-16 实测注意：** Hermes Agent 没有 `feishu_create_doc` / `feishu_fetch_doc` 工具。必须直接调 Feishu Open API（curl 或 Python `urllib`），需要 `FEISHU_APP_ID` + `FEISHU_APP_SECRET` 环境变量。

##### 1. 获取 tenant_access_token

```python
import urllib.request, json
app_id = os.getenv("FEISHU_APP_ID", "")
app_secret = os.getenv("FEISHU_APP_SECRET", "")
url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as resp:
    token = json.loads(resp.read())["tenant_access_token"]
```

#### 2. 创建文档

```python
create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
payload = json.dumps({"title": "文章标题"}).encode()
req2 = urllib.request.Request(create_url, data=payload, headers={
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
})
with urllib.request.urlopen(req2, timeout=10) as resp:
    doc = json.loads(resp.read())["data"]["document"]
    doc_id = doc["document_id"]   # 例如 "VHYNdueFOobzXAxRbZkcfyXBnNf"
```

#### 3. 写入内容块

`md_to_blocks()` 函数将 Markdown 转为 Feishu block 列表（见 `references/feishu-blocks.md` 中的完整实现）。

**⚠️ 50 blocks 批次限制：** `children` 数组每次最多 50 个，超出必须分批调用，否则返回 `field validation failed`（code=99992402，`"the max len is 50"`）。参考实现已内置分批逻辑。

**注意：** `block_type=6`（引用块）和 `block_type=16`（分割线）API 不支持。用普通段落代替：
- 引用块 → 加斜体样式的普通段落
- 分割线 → 空格段落

#### 4. 回读校验

```python
read_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/raw_content"
req4 = urllib.request.Request(read_url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req4, timeout=10) as resp:
    content = json.loads(resp.read()).get("data", {}).get("content", "")
    assert len(content) > 0, "文档内容为空"
```

**文档链接格式：** `https://feishu.cn/docx/{doc_id}`

### 回读检查项

- [ ] 文档标题是否符合规范
- [ ] 是否有开篇引用块
- [ ] 是否有2-5个二级标题
- [ ] 是否只用标准 Markdown 元素
- [ ] 是否有必要的表格/引用块/分割线
- [ ] 是否误用了 `<callout>` 等扩展标签

## 输出格式

**文档：** <链接>

## 飞书多维表格（Bitable）—— 文章效果追踪

**多维表格地址：** https://qcnlzzutz1e2.feishu.cn/base/<YOUR_APP_TOKEN>
**table_id：** <YOUR_TABLE_ID>

### 字段设计

| 字段 | 类型 | 说明 |
|------|------|------|
| 选题 | 文本 | 同一批文章共享一个选题标签 |
| 原始标题 | 文本 | AI取的标题（用于回溯对比） |
| 小红书标题 | 文本 | 用户最终修改后的标题 |
| 文章概要 | 文本 | 50字以内的核心论点 |
| 文章链接 | URL | 飞书文档链接 |
| 发布日期 | 日期 | Unix时间戳（毫秒） |
| 一周后阅读量 | 数字 | 发布7天后补填 |
| 一周后点赞数 | 数字 | 发布7天后补填 |
| 一周后收藏数 | 数字 | 发布7天后补填 |
| 一周后评论数 | 数字 | 发布7天后补填 |
| 备注 | 文本 | 其他需要记录的信息 |

### 双标题追踪（2026-06-25 新增）

**铁律：发布后必须读取用户修改后的飞书文档，获取最终版标题，不能直接用AI写的标题。**

流程：
1. AI写完文章 → 发布到飞书文档
2. 用户修改文档（标题、正文、排版）
3. **读取用户修改后的文档** → 提取最终版标题
4. 写入多维表格：「原始标题」= AI取的，「小红书标题」= 用户改的
5. 设7天定时提醒 → 提醒用户补数据

**为什么要双标题：** 回溯时对比「AI标题 vs 用户标题」的差异，分析标题修改对数据的影响，持续优化标题能力。

### API操作（Bitable记录CRUD）

```bash
# 获取token
export APP_ID="<YOUR_APP_ID>"
export APP_SECRET="<YOUR_APP_SECRET>"
export APP_TOKEN="<YOUR_APP_TOKEN>"
export TABLE_ID="<YOUR_TABLE_ID>"

TOKEN=*** -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d "{\"app_id\":\"$APP_ID\",\"app_secret\":\"$APP_SECRET\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

# 添加记录
curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/records/batch_create" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"records":[{"fields":{"选题":"...","小红书标题":"...","文章概要":"...","文章链接":{"link":"https://...","text":"飞书文档"},"发布日期":1750867200000}}]}'

# 更新记录
curl -s -X PUT "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/records/<record_id>" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"fields":{"原始标题":"...","小红书标题":"..."}}'

# 添加字段
curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/fields" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"field_name":"字段名","type":1}'
```

### 7天数据回填提醒

发布文章后，用 cronjob 设定发布日期+7天的提醒：
```python
cronjob(action='create', name='文章数据回填提醒',
  schedule='<发布日期+7天>T09:00:00',
  prompt='提醒用户回填文章数据，列出文章标题和链接')
```

### 读取用户修改后的飞书文档

```bash
# 获取文档标题
curl -s "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_id>" \
  -H "Authorization: Bearer *** \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['document']['title'])"

# 获取文档内容（前10个block）
curl -s "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_id>/blocks?page_size=10" \
  -H "Authorization: Bearer *** \
  | python3 -c "
import sys,json
for b in json.load(sys.stdin).get('data',{}).get('items',[])[:5]:
    bt=b.get('block_type')
    if bt==2:
        els=b.get('text',{}).get('elements',[])
        print(''.join(e.get('text_run',{}).get('content','') for e in els)[:200])
"
```

## 数据流

```
【消费】完整正文 markdown（来自 writing-draft 或 polishing-writing）
【产出】飞书文档链接
```

## ⚠️ 发布后追踪：多维表格 + 标题回溯（2026-06-25 新增）

**每次发布文章后，必须更新多维表格记录。** 表格不仅记录发布信息，更重要的是建立**学习闭环**——对比AI取的标题和用户最终修改的标题，分析差异，持续优化。

**多维表格结构（bitable）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| 选题 | 文本 | 话题/事件名称 |
| 原始标题 | 文本 | AI取的标题（用于回溯对比） |
| 小红书标题 | 文本 | 用户最终修改的标题 |
| 文章概要 | 文本 | 一句话核心论点 |
| 文章链接 | URL | 飞书文档链接 |
| 发布日期 | 日期 | timestamp毫秒 |
| 封面图 | URL | 从飞书文档第一张图提取 |
| 一周后阅读量 | 数字 | 发布7天后回填 |
| 一周后点赞数 | 数字 | 发布7天后回填 |
| 一周后收藏数 | 数字 | 发布7天后回填 |
| 一周后评论数 | 数字 | 发布7天后回填 |
| 备注 | 文本 | 其他观察 |

**回溯机制：**
1. 发布时记录AI取的「原始标题」和用户修改的「小红书标题」
2. 7天后补数据（设cron定时提醒）
3. 对比两个标题的差异，分析用户修改的方向（更口语？更短？更有冲突感？）
4. 把分析结论沉淀到 title-craft skill

**封面图提取流程：**
1. 用飞书API获取文档blocks：`GET /docx/v1/documents/{doc_id}/blocks`
2. 找第一个 block_type=27（Image block）的 `image.token`
3. 图片下载URL：`https://open.feishu.cn/open-apis/drive/v1/medias/{token}/download`
4. 存入bitable的URL字段

**Bitable API 操作要点：**
- app_id/secret 在环境变量 FEISHU_APP_ID/FEISHU_APP_SECRET
- 获取token：`POST /auth/v3/tenant_access_token/internal`
- 创建记录：`POST /bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create`
- 更新记录：`PUT /bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}`
- 添加字段：`POST /bitable/v1/apps/{app_token}/tables/{table_id}/fields`
- URL字段格式：`{"link": "https://...", "text": "显示文本"}`
- 日期字段格式：timestamp毫秒（如 1750867200000）

**⚠️ Bitable API坑位：**
- shell里curl+python3 -c的引号转义经常出问题 → 写成.py脚本文件再执行更可靠
- token过期后需要重新获取，不能缓存太久
- 新增字段时 type=15 是URL类型，type=1 是文本，type=2 是数字，type=5 是日期

## 数据流
【依赖】writing-draft（必须正文齐全）
         可选 polishing-writing（发布前建议先自检）
```

## 边界

**不做：** 修改正文逻辑、写作自检。正文内容和质检在写入前必须已经完成。如果发现内容有问题，提示用户先调用 `polishing-writing`。

## 参考

- 完整内容生产流水线：`references/content-pipeline.md`（从热点抓取到发布的全流程）
- 飞书Block API参考：`references/feishu-blocks.md`
