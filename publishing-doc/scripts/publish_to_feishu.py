#!/usr/bin/env python3
"""
飞书文档发布脚本 — 从 Markdown 到飞书文档。
用法: python3 publish_to_feishu.py <markdown_file> <title>
依赖: FEISHU_APP_ID + FEISHU_APP_SECRET 环境变量

自动处理:
  - Smart quotes / em dash / 省略号 → ASCII 等价物（避免 400）
  - 列表项统一转为普通段落（飞书 list block 不兼容 emoji）
  - 表格转为文字段落（API 不支持 table block）
  - 自动授权编辑权限
"""
import re, json, urllib.request, os, sys


def sanitize_text(text):
    """替换导致飞书 API 400 的 Unicode 字符为 ASCII 等价物。"""
    return (text
        .replace('\u2014', '-')    # em dash
        .replace('\u2013', '-')    # en dash
        .replace('\u2026', '...')  # 省略号
        .replace('\u2018', "'")    # left single quote
        .replace('\u2019', "'")    # right single quote
        .replace('\u201c', '"')    # left double quote
        .replace('\u201d', '"')    # right double quote
    )


def get_token():
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["tenant_access_token"]

def create_doc(token, title):
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    payload = json.dumps({"title": title}).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["data"]["document"]["document_id"]

def md_to_blocks(md_text):
    """将 Markdown 转为 Feishu block 列表。支持: 标题、加粗、斜体、行内代码、引用块(转斜体)、分割线。列表项转为普通段落（规避 list block emoji 400 错误）。"""
    blocks = []
    lines = md_text.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        # 分割线
        if line.strip() == "---":
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": "　", "text_element_style": {}}}], "style": {}}})
            i += 1
            continue
        # 标题
        if line.startswith("### "):
            blocks.append({"block_type": 5, "heading3": {"elements": [{"text_run": {"content": line[4:], "text_element_style": {}}}], "style": {}}})
            i += 1
            continue
        if line.startswith("## "):
            blocks.append({"block_type": 4, "heading2": {"elements": [{"text_run": {"content": line[3:], "text_element_style": {}}}], "style": {}}})
            i += 1
            continue
        if line.startswith("# "):
            blocks.append({"block_type": 3, "heading1": {"elements": [{"text_run": {"content": line[2:], "text_element_style": {}}}], "style": {}}})
            i += 1
            continue
        # 引用块 → 斜体段落（API不支持block_type=6）
        if line.startswith(">"):
            text = "「" + line[1:].strip() + "」"
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": text, "text_element_style": {"italic": True}}}], "style": {}}})
            i += 1
            continue
        # 有序列表 → 普通段落（飞书 list block 不兼容 emoji 等特殊字符）
        m = re.match(r'^(\d+)\.\s+(.*)', line)
        if m:
            content = m.group(1) + ". " + m.group(2)
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": content, "text_element_style": {}}}], "style": {}}})
            i += 1
            continue
        # 无序列表 → 普通段落
        if re.match(r'^[-*]\s+', line):
            content = line[2:].strip()
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": content, "text_element_style": {}}}], "style": {}}})
            i += 1
            continue
        # 表格 → 文字段落（API不支持table block）
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            blocks.extend(_parse_table(table_lines))
            continue
        # 普通文本（处理加粗、斜体、行内代码）
        parts = []
        last_end = 0
        for m in re.finditer(r'\*\*(.+?)\*\*', line):
            if m.start() > last_end:
                parts.append({"text_run": {"content": line[last_end:m.start()], "text_element_style": {}}})
            parts.append({"text_run": {"content": m.group(1), "text_element_style": {"bold": True}}})
            last_end = m.end()
        if last_end < len(line):
            remaining = line[last_end:]
            remaining_parts = []
            rem_last = 0
            for m in re.finditer(r'`(.+?)`|\*(.+?)\*', remaining):
                if m.start() > rem_last:
                    remaining_parts.append({"text_run": {"content": remaining[rem_last:m.start()], "text_element_style": {}}})
                if m.group(1) is not None:
                    remaining_parts.append({"text_run": {"content": m.group(1), "text_element_style": {"inline_code": True}}})
                else:
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
    return blocks

def _parse_table(table_lines):
    rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.match(r'^[-:]+$', c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return []
    blocks = []
    header_str = "【表】" + " | ".join(rows[0])
    blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": header_str, "text_element_style": {"bold": True}}}], "style": {}}})
    for row in rows[1:]:
        row_str = "　　" + " | ".join(row)
        blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": row_str, "text_element_style": {}}}], "style": {}}})
    return blocks

def write_blocks(token, doc_id, blocks):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    for batch_start in range(0, len(blocks), 50):
        batch = blocks[batch_start:batch_start + 50]
        payload = json.dumps({"children": batch}, ensure_ascii=False).encode()
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            assert result.get("code") == 0, f"写入失败(批次{batch_start//50+1}): {result}"

def verify_doc(token, doc_id):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/raw_content"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        content = json.loads(resp.read()).get("data", {}).get("content", "")
        assert len(content) > 0, "文档内容为空"
        return len(content)

def grant_edit_permission(token, doc_id, user_openid):
    """给用户添加 full_access 编辑权限。"""
    url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{doc_id}/members?type=docx"
    payload = json.dumps({
        "member_type": "openid",
        "member_id": user_openid,
        "perm": "full_access"
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        if result.get("code") == 0:
            return True
        else:
            print(f"⚠️ 授权失败: {result.get('msg', result)}", file=sys.stderr)
            return False

def main():
    if len(sys.argv) < 3:
        print(f"用法: {sys.argv[0]} <markdown_file> <title>")
        sys.exit(1)
    md_file, title = sys.argv[1], sys.argv[2]
    with open(md_file) as f:
        md_text = sanitize_text(f.read())
    token = get_token()
    doc_id = create_doc(token, title)
    blocks = md_to_blocks(md_text)
    write_blocks(token, doc_id, blocks)
    content_len = verify_doc(token, doc_id)
    # 自动给用户加编辑权限
    owner_id = os.getenv("FEISHU_OWNER_OPENID", "ou_f735f02495560fb7243ca0f4d49f3d7b")
    perm_ok = grant_edit_permission(token, doc_id, owner_id)
    print(f"doc_id: {doc_id}")
    print(f"blocks: {len(blocks)}")
    print(f"content_len: {content_len}")
    print(f"编辑权限: {'✅ 已授权' if perm_ok else '⚠️ 授权失败'}")
    print(f"链接: https://feishu.cn/docx/{doc_id}")

if __name__ == "__main__":
    main()
