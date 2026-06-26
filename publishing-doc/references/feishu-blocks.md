# Feishu Document Block Types (实测 2025-05-16，2026-05-16 修订)

## API 基础

- Base URL: `https://open.feishu.cn/open-apis`
- Auth: `tenant_access_token` via `POST /auth/v3/tenant_access_token/internal`
- 创建文档: `POST /docx/v1/documents`
- 写入 blocks: `POST /docx/v1/documents/{doc_id}/blocks/{doc_id}/children`
- 读取内容: `GET /docx/v1/documents/{doc_id}/raw_content`
- **每次最多50个 blocks，超出必须分批**

## Block Type 映射

| block_type | 名称 | 支持状态 | 飞书 Markdown | 备注 |
|-----------|------|---------|--------------|------|
| 1 | page | ✅ | — | 根 block，创建时自动生成 |
| 2 | text/paragraph | ✅ | 纯文本 | 普通段落 |
| 3 | heading1 | ✅ | `# 标题` | 一级标题 |
| 4 | heading2 | ✅ | `## 标题` | 二级标题 |
| 5 | heading3 | ✅ | `### 标题` | 三级标题 |
| 6 | quote | ❌ | `> 引用` | **API 不支持**，用斜体段落代替 |
| 7 | ordered_list | ✅ | `1. 列表` | 有序列表 |
| 8 | unordered_list | ✅ | `- 列表` | 无序列表 |
| 10 | table | ❌ | `\| 表 \|` | **实际转为文字段落**（见下方 `_parse_markdown_table`），API 限制 table_cell 嵌套返回 9499 |
| 11 | table_cell | ❌ | — | 表格单元格，table block 内部使用 |
| 12 | bullet | ✅ | 同 unordered_list | |
| 13 | code | ✅ | ` ```code``` ` | 代码块 |
| 16 | divider | ❌ | `---` | **API 不支持**，用空格段落代替 |

## md_to_blocks 完整实现

```python
import re, json, urllib.request
from typing import List

def md_to_blocks(md_text: str, token: str, doc_id: str) -> list[dict]:
    """
    将 Markdown 文本转为 Feishu block 列表并写入文档。
    - 每次最多50个 blocks，自动分批
    - 支持: 标题、加粗、斜体、列表、表格、分割线、引用块（转斜体）
    - 表格行数无限制，按实际行数创建 table block
    """
    blocks = []
    lines = md_text.strip().split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # 空行 → 不写入 block（段落之间的自然分隔）
        if not line.strip():
            i += 1
            continue

        # 分割线 --- → 空格段落
        if line.strip() == "---":
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": "　", "text_element_style": {}}}], "style": {}}})
            i += 1
            continue

        # 一级标题 ###
        if line.startswith("### "):
            blocks.append({"block_type": 5, "heading3": {"elements": [{"text_run": {"content": line[4:], "text_element_style": {}}}], "style": {}}})
            i += 1
            continue

        # 二级标题 ##
        if line.startswith("## "):
            blocks.append({"block_type": 4, "heading2": {"elements": [{"text_run": {"content": line[3:], "text_element_style": {}}}], "style": {}}})
            i += 1
            continue

        # 一级标题 #
        if line.startswith("# "):
            blocks.append({"block_type": 3, "heading1": {"elements": [{"text_run": {"content": line[2:], "text_element_style": {}}}], "style": {}}})
            i += 1
            continue

        # 引用块 > → 斜体段落（block_type=6 不支持）
        if line.startswith(">"):
            text = "「" + line[1:].strip() + "」"
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": text, "text_element_style": {"italic": True}}}], "style": {}}})
            i += 1
            continue

        # 有序列表 1. 2. 3.
        m = re.match(r'^(\d+)\.\s+(.*)', line)
        if m:
            blocks.append({"block_type": 7, "ordered": {"elements": [{"text_run": {"content": m.group(2), "text_element_style": {}}}], "style": {}}})
            i += 1
            continue

        # 无序列表 - 或 *
        if re.match(r'^[-*]\s+', line):
            content = line[2:].strip()
            blocks.append({"block_type": 8, "unordered": {"elements": [{"text_run": {"content": content, "text_element_style": {}}}], "style": {}}})
            i += 1
            continue

        # 表格 | A | B | → 跨多行收集后统一处理
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            table_blocks = _parse_markdown_table(table_lines)
            blocks.extend(table_blocks)
            continue

        # 普通文本：处理 **加粗**、*斜体* 和 `行内代码`
        parts = []
        last_end = 0
        # 加粗优先
        for m in re.finditer(r'\*\*(.+?)\*\*', line):
            if m.start() > last_end:
                parts.append({"text_run": {"content": line[last_end:m.start()], "text_element_style": {}}})
            parts.append({"text_run": {"content": m.group(1), "text_element_style": {"bold": True}}})
            last_end = m.end()
        # 剩余内容处理 *斜体* 和 `行内代码`
        if last_end < len(line):
            remaining = line[last_end:]
            remaining_parts = []
            rem_last = 0
            for m in re.finditer(r'`(.+?)`|\*(.+?)\*', remaining):
                if m.start() > rem_last:
                    remaining_parts.append({"text_run": {"content": remaining[rem_last:m.start()], "text_element_style": {}}})
                if m.group(1) is not None:
                    # 行内代码
                    remaining_parts.append({"text_run": {"content": m.group(1), "text_element_style": {"inline_code": True}}})
                else:
                    # 斜体
                    remaining_parts.append({"text_run": {"content": m.group(2), "text_element_style": {"italic": True}}})
                rem_last = m.end()
            if rem_last < len(remaining):
                remaining_parts.append({"text_run": {"content": remaining[rem_last:], "text_element_style": {}}})
            parts.extend(remaining_parts)
        if parts:
            blocks.append({"block_type": 2, "text": {"elements": parts, "style": {}}})
        else:
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": line, "text_element_style": {}}}], "style": {}}})
        i += 1

    # 分批写入（每次最多50个 blocks）
    write_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    for batch_start in range(0, len(blocks), 50):
        batch = blocks[batch_start:batch_start + 50]
        payload = json.dumps({"children": batch}, ensure_ascii=False).encode()
        req = urllib.request.Request(write_url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            assert result.get("code") == 0, f"写入失败（第{batch_start//50+1}批）: {result}"

    return blocks


def _parse_markdown_table(table_lines: List[str]) -> List[dict]:
    """
    将 markdown 表格转为 Feishu 段落列表（文字描述格式）。
    注：飞书 docx block API 的 table block（type=10/11）存在参数类型限制，
    table_cell 的嵌套结构在 POST /blocks 时持续返回 9499 错误。
    因此表格统一转为普通文字段落，格式为："【表头】单元格1 | 单元格2 | ..."
    如需真正表格，建议手动在飞书中插入，或将表格截图作为图片发布。
    """
    rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if all(re.match(r'^[-:]+$', c) for c in cells):
            continue
        rows.append(cells)

    if not rows:
        return []

    header = rows[0]
    col_count = len(header)

    blocks = []
    # 第一行：表头描述
    header_str = "【表】" + " | ".join(header)
    blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": header_str, "text_element_style": {"bold": True}}}], "style": {}}})

    # 数据行
    for row in rows[1:]:
        row_str = "　　" + " | ".join(row)
        blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": row_str, "text_element_style": {}}}], "style": {}}})

    # 空行分隔
    blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": "　", "text_element_style": {}}}], "style": {}}})

    return blocks
```

## 已知限制

1. **引用块（block_type=6）** — API 不支持。统一转为斜体段落，文字两侧加「」书名号。

2. **分割线（block_type=16）** — API 不支持。用全角空格段落（`　`）代替。

3. **加粗 `**text**`** — 正常工作。

4. **斜体 `*text*`** — 正常工作（与加粗同时存在时，加粗优先匹配）。

5. **有序/无序列表** — 支持，对应 block_type 7 和 8。但飞书编辑器显示效果可能与标准 Markdown 有差异。

6. **表格（block_type=10/11）** — docx block API 的 table block 写入存在参数类型限制（type=11 table_cell 的嵌套结构持续返回 9499 错误）。**当前无法通过 API 创建表格**，统一转为文字段落「【表】列1 | 列2 | 列3」格式。如需真正表格，建议手动在飞书文档中插入。

7. **doc_id 不是 URL-safe** — 文档链接格式是 `https://feishu.cn/docx/{doc_id}`，直接拼接。

8. **50 blocks 批次限制** — 超出必须分批，不分批会返回 `field validation failed`（code=99992402），`"the max len is 50"`。

9. **旧文档测试数据残留** — 写入测试时留垃圾数据，删掉旧文档重创建，不要试图清理旧 blocks。
