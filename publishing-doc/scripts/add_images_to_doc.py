#!/usr/bin/env python3
"""
向飞书文档在指定位置插入图片（三步流程）。
用法: python3 add_images_to_doc.py <doc_id> --after "文本内容" image.png [--after "文本内容" image2.png ...]
依赖: FEISHU_APP_ID + FEISHU_APP_SECRET 环境变量
"""
import json, urllib.request, os, sys, mimetypes

def get_token():
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["tenant_access_token"]

def get_doc_blocks(token, doc_id):
    """获取文档所有 block"""
    blocks = []
    page_token = ""
    while True:
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=100"
        if page_token:
            url += f"&page_token={page_token}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            items = result.get("data", {}).get("items", [])
            blocks.extend(items)
            if not result.get("data", {}).get("has_more"):
                break
            page_token = result["data"].get("page_token", "")
    return blocks

def extract_text_from_block(block):
    """从 block 中提取纯文本"""
    bt = block.get("block_type")
    text = ""
    # 尝试各种 text 容器
    for key in ["text", "heading1", "heading2", "heading3", "heading4",
                 "heading5", "heading6", "heading7", "heading8", "heading9",
                 "quote", "todo", "bullet", "ordered"]:
        container = block.get(key, {})
        elements = container.get("elements", [])
        for el in elements:
            tr = el.get("text_run", {})
            text += tr.get("content", "")
    return text.strip()

def find_block_index(blocks, search_text):
    """找到包含 search_text 的 block 的 index"""
    for i, block in enumerate(blocks):
        text = extract_text_from_block(block)
        if search_text in text:
            return i
    return -1

def create_image_block_at(token, doc_id, index):
    """在指定 index 创建空 image block，返回 block_id"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    payload = json.dumps({
        "index": index,
        "children": [{"block_type": 27, "image": {}}]
    }, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        assert result.get("code") == 0, f"创建image block失败: {result}"
        children = result["data"]["children"]
        for child in children:
            if child.get("block_type") == 27:
                return child["block_id"]
        return children[0]["block_id"]

def upload_image_to_block(token, image_path, block_id):
    """上传图片到指定 block，返回 file_token"""
    url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
    filename = os.path.basename(image_path)
    file_size = os.path.getsize(image_path)
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"

    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="file_name"\r\n\r\n{filename}',
        f'--{boundary}\r\nContent-Disposition: form-data; name="parent_type"\r\n\r\ndocx_image',
        f'--{boundary}\r\nContent-Disposition: form-data; name="parent_node"\r\n\r\n{block_id}',
        f'--{boundary}\r\nContent-Disposition: form-data; name="size"\r\n\r\n{file_size}',
    ]
    with open(image_path, 'rb') as f:
        file_data = f.read()
    body_text = '\r\n'.join(parts) + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {mime_type}\r\n\r\n'
    body_end = f'\r\n--{boundary}--\r\n'
    body = body_text.encode() + file_data + body_end.encode()

    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        assert result.get("code") == 0, f"上传图片失败: {result}"
        return result["data"]["file_token"]

def set_image_on_block(token, doc_id, block_id, file_token):
    """用 replace_image 把 file_token 设到 image block"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}"
    payload = json.dumps({"replace_image": {"token": file_token}}, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    req.get_method = lambda: "PATCH"
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        assert result.get("code") == 0, f"设置图片失败: {result}"
        return True

def main():
    # 解析参数: doc_id --after "text" img1.png --after "text2" img2.png
    if len(sys.argv) < 5:
        print(f"用法: {sys.argv[0]} <doc_id> --after \"文本内容\" image.png [--after \"文本内容\" image.png]")
        sys.exit(1)

    doc_id = sys.argv[1]
    args = sys.argv[2:]

    # 解析 --after + image 对
    insertions = []
    i = 0
    while i < len(args):
        if args[i] == "--after" and i + 2 < len(args):
            search_text = args[i + 1]
            image_path = args[i + 2]
            if not os.path.exists(image_path):
                print(f"文件不存在: {image_path}")
                sys.exit(1)
            insertions.append({"search_text": search_text, "image_path": image_path})
            i += 3
        else:
            print(f"参数错误: {args[i]}")
            sys.exit(1)

    token = get_token()

    # 获取文档所有 block
    print(f"📄 获取文档结构...")
    blocks = get_doc_blocks(token, doc_id)
    print(f"   共 {len(blocks)} 个 block")

    # 倒序插入（后面的图先插，不影响前面的 index）
    insertions.reverse()

    for ins in insertions:
        search_text = ins["search_text"]
        image_path = ins["image_path"]
        filename = os.path.basename(image_path)

        # 找到目标 block
        idx = find_block_index(blocks, search_text)
        if idx == -1:
            print(f"\n⚠️  未找到包含「{search_text[:30]}」的段落，跳过 {filename}")
            continue

        # 插入位置：目标 block 后面
        insert_index = idx + 1
        print(f"\n📷 插入: {filename}")
        print(f"   位置: 第 {insert_index} 个 block 之后（匹配: {search_text[:40]}...）")

        # Step 1: 创建空 image block
        print("   1/3 创建空block...", end=" ")
        block_id = create_image_block_at(token, doc_id, insert_index)
        print(f"✅")

        # Step 2: 上传图片
        print("   2/3 上传图片...", end=" ")
        file_token = upload_image_to_block(token, image_path, block_id)
        print(f"✅")

        # Step 3: 设置图片
        print("   3/3 设置素材...", end=" ")
        set_image_on_block(token, doc_id, block_id, file_token)
        print("✅")

    print(f"\n✅ 全部完成: https://feishu.cn/docx/{doc_id}")

if __name__ == "__main__":
    main()
