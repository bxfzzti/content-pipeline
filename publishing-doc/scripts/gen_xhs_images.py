#!/usr/bin/env python3
"""
小红书种草文配图生成器：从电商抓产品图→拼成XHS风格多图。
用法: python3 gen_xhs_images.py --products products.json --output /tmp/xhs_images/

products.json 格式:
[
  {"name": "品胜真空吸盘式手机支架", "price": "¥89", "keyword": "品胜手机支架车载", "highlight": "稳固不抖"},
  ...
]
"""
import json, os, sys, re, urllib.request, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ======== 字体 ========
def get_cn_font(size=24):
    candidates = [
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
    ]
    for f in candidates:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except:
                continue
    return ImageFont.load_default()

# ======== 图片下载 ========
def download_image(url, save_path):
    """下载图片"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://www.jd.com/'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            with open(save_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"  下载失败: {e}")
        return False

def search_jd_product_image(keyword):
    """从京东搜索获取商品主图URL"""
    # 京东搜索API
    search_url = f"https://search.jd.com/Search?keyword={urllib.request.quote(keyword)}&enc=utf-8"
    try:
        req = urllib.request.Request(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # 提取商品图片URL
            # 京东图片格式: //img14.360buyimg.com/.../*.jpg
            imgs = re.findall(r'//img\d+\.360buyimg\.com/[^"\']+\.(?:jpg|png|webp)', html)
            # 过滤出商品主图（通常是n1/目录下的）
            product_imgs = [i for i in imgs if '/n1/' in i or '/s1/' in i]
            if product_imgs:
                return 'https:' + product_imgs[0]
    except Exception as e:
        print(f"  京东搜索失败: {e}")
    return None

# ======== 图片处理 ========
def resize_keep_ratio(img, max_size):
    """保持比例缩放"""
    ratio = min(max_size / img.width, max_size / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    return img.resize(new_size, Image.LANCZOS)

def create_product_card(product_img, name, price, highlight, card_size=(540, 720)):
    """创建单品卡片"""
    card = Image.new('RGB', card_size, '#FFFFFF')
    draw = ImageDraw.Draw(card)
    
    # 产品图居中
    if product_img:
        max_img_h = card_size[1] - 200
        resized = resize_keep_ratio(product_img, max_img_h)
        x = (card_size[0] - resized.width) // 2
        y = 30
        card.paste(resized, (x, y))
    
    # 底部信息区
    y_info = card_size[1] - 180
    
    # 产品名
    font_name = get_cn_font(28)
    font_price = get_cn_font(36)
    font_highlight = get_cn_font(22)
    
    # 名称（居中，超长则截断）
    if len(name) > 18:
        name = name[:18] + '...'
    bbox = draw.textbbox((0, 0), name, font=font_name)
    name_w = bbox[2] - bbox[0]
    draw.text(((card_size[0] - name_w) // 2, y_info), name, fill='#333333', font=font_name)
    
    # 价格（红色，居中）
    bbox = draw.textbbox((0, 0), price, font=font_price)
    price_w = bbox[2] - bbox[0]
    draw.text(((card_size[0] - price_w) // 2, y_info + 45), price, fill='#FF4444', font=font_price)
    
    # 卖点（灰色，居中）
    bbox = draw.textbbox((0, 0), highlight, font=font_highlight)
    hl_w = bbox[2] - bbox[0]
    draw.text(((card_size[0] - hl_w) // 2, y_info + 95), highlight, fill='#888888', font=font_highlight)
    
    # 底部红色装饰线
    draw.rectangle([card_size[0]//2 - 30, card_size[1] - 20, card_size[0]//2 + 30, card_size[1] - 16], fill='#FF4444')
    
    return card

def create_cover_grid(products, images, grid_size=(1080, 1440)):
    """创建封面图：产品平铺网格"""
    cover = Image.new('RGB', grid_size, '#F5F5F5')
    draw = ImageDraw.Draw(cover)
    
    # 标题区
    font_title = get_cn_font(48)
    font_sub = get_cn_font(28)
    
    title = "车上8件好物"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = bbox[2] - bbox[0]
    draw.text(((grid_size[0] - title_w) // 2, 40), title, fill='#333333', font=font_title)
    
    sub = "总价约¥1300 · 每一件都用了半年以上"
    bbox = draw.textbbox((0, 0), sub, font=font_sub)
    sub_w = bbox[2] - bbox[0]
    draw.text(((grid_size[0] - sub_w) // 2, 100), sub, fill='#888888', font=font_sub)
    
    # 装饰线
    draw.rectangle([grid_size[0]//2 - 50, 145, grid_size[0]//2 + 50, 148], fill='#FF4444')
    
    # 4x2 网格
    cols, rows = 4, 2
    margin = 40
    gap = 20
    cell_w = (grid_size[0] - margin * 2 - gap * (cols - 1)) // cols
    cell_h = (grid_size[1] - 180 - margin * 2 - gap * (rows - 1)) // rows
    
    for i, (product, img) in enumerate(zip(products, images)):
        row = i // cols
        col = i % cols
        x = margin + col * (cell_w + gap)
        y = 180 + row * (cell_h + gap)
        
        # 白色卡片背景
        draw.rounded_rectangle([x, y, x + cell_w, y + cell_h], radius=12, fill='#FFFFFF')
        
        # 产品图
        if img:
            resized = resize_keep_ratio(img, min(cell_w - 20, cell_h - 80))
            img_x = x + (cell_w - resized.width) // 2
            img_y = y + 10
            cover.paste(resized, (img_x, img_y))
        
        # 价格标签
        font_price = get_cn_font(20)
        price = product.get('price', '')
        bbox = draw.textbbox((0, 0), price, font=font_price)
        pw = bbox[2] - bbox[0]
        draw.text((x + (cell_w - pw) // 2, y + cell_h - 40), price, fill='#FF4444', font=font_price)
    
    # 底部标注
    font_note = get_cn_font(18)
    note = "村长不开车 | 自用好物分享"
    bbox = draw.textbbox((0, 0), note, font=font_note)
    nw = bbox[2] - bbox[0]
    draw.text(((grid_size[0] - nw) // 2, grid_size[1] - 35), note, fill='#AAAAAA', font=font_note)
    
    return cover

def main():
    # 默认产品列表
    products = [
        {"name": "品胜真空吸盘式手机支架", "price": "¥89", "highlight": "稳固不抖", "img": None},
        {"name": "朗界出风口车载香薰", "price": "¥99", "highlight": "不漏液", "img": None},
        {"name": "南极人前挡遮阳伞", "price": "¥49", "highlight": "5秒展开", "img": None},
        {"name": "倍思67W车载充电器", "price": "¥79", "highlight": "双口快充", "img": None},
        {"name": "摩飞MR3200车载吸尘器", "price": "¥239", "highlight": "大吸力", "img": None},
        {"name": "佳奥记忆棉汽车腰靠", "price": "¥119", "highlight": "长途不累", "img": None},
        {"name": "70迈A810行车记录仪", "price": "¥599", "highlight": "夜视强", "img": None},
        {"name": "绿联座椅背挂式纸巾盒", "price": "¥39", "highlight": "不占空间", "img": None},
    ]
    
    output_dir = '/tmp/xhs_images'
    os.makedirs(output_dir, exist_ok=True)
    
    # 尝试下载产品图
    print("📦 下载产品图片...")
    product_images = []
    for p in products:
        print(f"  {p['name']}...", end=" ")
        img_path = os.path.join(output_dir, f"{p['name'][:6]}.jpg")
        
        # 先检查缓存
        if os.path.exists(img_path):
            product_images.append(Image.open(img_path))
            print("✅ (缓存)")
            continue
        
        # 尝试从京东搜索
        url = search_jd_product_image(p['name'])
        if url and download_image(url, img_path):
            product_images.append(Image.open(img_path))
            print("✅")
        else:
            product_images.append(None)
            print("❌ 无图")
    
    # 生成封面图
    print("\n🎨 生成封面图...")
    cover = create_cover_grid(products, product_images)
    cover_path = os.path.join(output_dir, 'cover.png')
    cover.save(cover_path, quality=95)
    print(f"  ✅ {cover_path}")
    
    # 生成单品卡片
    print("\n🎨 生成单品卡片...")
    for i, (p, img) in enumerate(zip(products, product_images)):
        card = create_product_card(img, p['name'], p['price'], p['highlight'])
        card_path = os.path.join(output_dir, f'product_{i+1}.png')
        card.save(card_path, quality=95)
        print(f"  ✅ {card_path}")
    
    print(f"\n✅ 配图全部生成到 {output_dir}")
    print(f"   共 {len(os.listdir(output_dir))} 张图片")

if __name__ == '__main__':
    main()
