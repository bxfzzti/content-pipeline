#!/usr/bin/env python3
"""
文章配图生成器：为XHS文章生成数据对比图/参数表。
用法：python3 gen_chart.py --type bar|table|header --data '{"..."}' --output /tmp/chart.png

支持的图表类型：
- bar: 柱状对比图（销量/参数对比）
- table: 参数对比表
- header: 文章标题封面图
"""
import sys, json, os, argparse
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("需要: pip install matplotlib pillow")
    sys.exit(1)

# 设置中文字体
def get_cn_font():
    """找一个可用的中文字体"""
    candidates = [
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    ]
    for f in candidates:
        if os.path.exists(f):
            return f
    # fallback: 尝试matplotlib内置
    return fm.findfont(fm.FontProperties(family='sans-serif'))

CN_FONT = get_cn_font()

def gen_bar_chart(data, output, title='', figsize=(10, 6)):
    """生成柱状对比图
    
    data格式: {"labels": ["A", "B", "C"], "values": [100, 200, 150], "unit": "台"}
    """
    labels = data.get('labels', [])
    values = data.get('values', [])
    unit = data.get('unit', '')
    colors = data.get('colors', ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
    
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    bars = ax.bar(range(len(labels)), values, color=colors[:len(labels)], 
                  width=0.6, edgecolor='white', linewidth=0.5)
    
    # 标签
    font_prop = fm.FontProperties(fname=CN_FONT, size=12)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontproperties=font_prop, color='white', fontsize=12)
    ax.tick_params(axis='y', colors='white', labelsize=10)
    
    # 数值标注
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(values)*0.02,
                f'{val:,.0f}{unit}', ha='center', va='bottom', color='white', fontsize=11,
                fontproperties=font_prop)
    
    # 标题
    if title:
        ax.set_title(title, fontproperties=fm.FontProperties(fname=CN_FONT, size=16),
                     color='white', pad=20)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333')
    ax.spines['bottom'].set_color('#333')
    ax.grid(axis='y', alpha=0.2, color='white')
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"✅ 柱状图已保存: {output}")

def gen_comparison_table(data, output, title=''):
    """生成参数对比表图片
    
    data格式: {
        "headers": ["参数", "问界M9", "宝马X5"],
        "rows": [
            ["价格", "46.98万起", "60.5万起"],
            ["智驾", "城区NCA 300+城", "L2辅助"]
        ]
    }
    """
    headers = data.get('headers', [])
    rows = data.get('rows', [])
    
    # 计算尺寸
    n_cols = len(headers)
    n_rows = len(rows) + 1  # +1 for header
    col_width = 280
    row_height = 55
    table_width = col_width * n_cols + 40
    table_height = row_height * n_rows + 80
    
    img = Image.new('RGB', (table_width, table_height), '#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(CN_FONT, 18)
        font_bold = ImageFont.truetype(CN_FONT, 20)
    except:
        font = ImageFont.load_default()
        font_bold = font
    
    # 标题
    if title:
        draw.text((20, 15), title, fill='#FFD93D', font=font_bold)
        y_start = 55
    else:
        y_start = 20
    
    # 表头
    for j, h in enumerate(headers):
        x = 20 + j * col_width
        y = y_start
        draw.rectangle([x, y, x + col_width - 5, y + row_height], fill='#16213E', outline='#333')
        draw.text((x + 15, y + 15), h, fill='#FFD93D', font=font_bold)
    
    # 数据行
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            x = 20 + j * col_width
            y = y_start + (i + 1) * row_height
            bg = '#0f3460' if i % 2 == 0 else '#1a1a2e'
            draw.rectangle([x, y, x + col_width - 5, y + row_height], fill=bg, outline='#333')
            color = '#4ECDC4' if j > 0 else 'white'
            draw.text((x + 15, y + 15), str(cell), fill=color, font=font)
    
    img.save(output, quality=95)
    print(f"✅ 对比表已保存: {output}")

def gen_header_image(text, output, subtitle='', width=1080, height=720):
    """生成文章标题封面图（适合XHS）"""
    img = Image.new('RGB', (width, height), '#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype(CN_FONT, 48)
        font_sub = ImageFont.truetype(CN_FONT, 24)
    except:
        font_title = ImageFont.load_default()
        font_sub = font_title
    
    # 装饰线
    draw.rectangle([60, 280, width - 60, 283], fill='#FF6B6B')
    
    # 标题（自动换行）
    lines = wrap_text(text, font_title, width - 120, draw)
    y = 300
    for line in lines:
        draw.text((60, y), line, fill='white', font=font_title)
        y += 65
    
    # 副标题
    if subtitle:
        draw.text((60, y + 20), subtitle, fill='#888', font=font_sub)
    
    # 底部品牌
    draw.rectangle([60, height - 80, width - 60, height - 77], fill='#333')
    try:
        font_brand = ImageFont.truetype(CN_FONT, 18)
    except:
        font_brand = ImageFont.load_default()
    draw.text((60, height - 65), '村长不开车 | 小红书', fill='#666', font=font_brand)
    
    img.save(output, quality=95)
    print(f"✅ 封面图已保存: {output}")

def wrap_text(text, font, max_width, draw):
    """简单的文字换行"""
    lines = []
    current = ''
    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines

def main():
    parser = argparse.ArgumentParser(description='文章配图生成')
    parser.add_argument('--type', choices=['bar', 'table', 'header'], required=True)
    parser.add_argument('--data', type=str, help='JSON格式数据')
    parser.add_argument('--title', type=str, default='', help='图表标题')
    parser.add_argument('--subtitle', type=str, default='', help='副标题（header类型用）')
    parser.add_argument('--output', type=str, required=True, help='输出路径')
    args = parser.parse_args()
    
    data = json.loads(args.data) if args.data else {}
    
    if args.type == 'bar':
        gen_bar_chart(data, args.output, args.title)
    elif args.type == 'table':
        gen_comparison_table(data, args.output, args.title)
    elif args.type == 'header':
        text = data.get('text', args.title)
        gen_header_image(text, args.output, args.subtitle)

if __name__ == '__main__':
    main()
