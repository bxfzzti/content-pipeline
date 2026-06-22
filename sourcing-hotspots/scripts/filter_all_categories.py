#!/usr/bin/env python3
"""
四品类热点过滤器 v3：汽车 + 3C数码 + AI + 家居
含跨品类品牌分流、3C黑名单、AI收紧规则、噪音平台硬排除

用法:
  python3 filter_all_categories.py /tmp/hotspots.json [rss_intl.json] [rss_home.json]

输出: 各品类条目 + 汇总统计，结果保存到 /tmp/filtered_daily.json
"""
import json, sys, re
from datetime import datetime, timezone, timedelta

domestic_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/hotspots.json"
intl_file = sys.argv[2] if len(sys.argv) > 2 else None
home_file = sys.argv[3] if len(sys.argv) > 3 else None

# ===== 噪音词（匹配即丢弃）=====
NOISE_WORDS = [
    '欧冠','进球','破门','比赛','联赛','决赛','阿森纳','NBA','马刺','雷霆','姆巴佩',
    '王菲','谢霆锋','鹿晗','综艺','选秀','偶像','桃花坞','演唱会',
    '印度','高温','投弃权票','选举','国会','核电站','俄罗斯','乌克兰','古巴','特朗普',
    '牙齿','早睡','减肥','养生','仅退款','榴莲','杨梅','塌陷','排泄',
    '天猫618','京东618','优惠券','发新券','红包','秒杀',
    '喜加一','Epic免费','Steam免费','源码','arxiv','GPIC','npm supply','TanStack',
    '月嫂','ICU','虐猫','虐童','戒网瘾','学术造假','院长','追尾货车','撞向路人',
    'pizza oven','steroid','Arduboy','Steam Controller','Backrooms',
    'CarPlay','怎么连','求教','Raskin','Visionary Behind','母亲节文案','问责通告',
]

# ===== 黑名单（关键词命中但实际无关）=====
BLACKLIST = {
    '三星': ['三星堆', '三星海力士杠杆'],
    '眼镜': ['眼镜王蛇', '眼镜蛇'],
    '充电': ['充电后自燃', '充电起火'],
    '发布': ['停售通知', '红色预警', '主题曲', '问责通告', '律师函', '虐猫影像'],
    '稳定器': ['尼克尔'],
    '飞利浦': ['显示器', '显示器', '显示屏', 'Monitor'],
    '无人机': ['袭击', '残骸', '军事', '美军人形'],
    'Shark': ['vs', 'sharks', '战队', 'esports'],
}

# ===== 噪音平台（硬排除）=====
NOISE_PLATFORMS = {'csdn', 'linuxdo', 'hostloc', 'v2ex', 'newsmth', 'nodeseek'}

# ===== 3C黑名单模式 =====
C3_BLACKLIST = [
    r'纹眉|整容|医美',           # 华硕误匹配
    r'母亲节|父亲节|文案|发声',    # OPPO母亲节争议
    r'喜加一|免费领|Epic|Steam.*免费',  # 游戏促销
    r'潜艇|军事|武器',            # 智能手表军事泄密
    r'怎么摆|怎么设置|教程|入门',  # 路由器教程
    r'跑酷|游戏发售|头像',        # 游戏相关
    r'SHARE|创作密码|盛典|赋能',  # 活动误匹配
    r'规范精讲|开发者访谈',        # 技术文档
    r'出\s|卖\s|求购|转让',      # 二手交易
]

# ===== AI黑名单模式 =====
AI_BLACKLIST = [
    r'感谢.*制裁|制裁.*感谢',    # 宏观政治新闻
    r'土区|接码|plus.*便宜',     # 买号接码
    r'解决方案|错误.*解决|debug|排查',  # 技术问答
    r'对比.*网站|价格对比',       # 工具站
    r'请求体|deserialize|JSON.*body',  # API调试
    r'depth解析|后缀到底|深度解析.*API',  # 开发者教程
    r'gateway to building|pet was',  # 个人故事/宠物
    r'the better way to use|怎么用|使用教程',  # 使用教程
    r'peptide|crypto.*lab|booming',  # 无关行业
]

# ===== 跨品类品牌分流 =====
CROSS_BRANDS = {
    '华为': {
        'auto': r'问界|智界|尊界|鸿蒙智行|车|SUV|轿车|智驾|乾崑|途灵|底盘|大定|交付|余承东',
        'ai': r'韬定律|芯片|麒麟|昇腾|盘古|大模型|AI|何庭波|半导体|制程|晶体管|算力|推理芯片',
        '3c': r'手机|Mate|P系列|MatePad|耳机|穿戴|手表|手环|平板|笔记本|MateBook|鸿蒙|HarmonyOS',
    },
    '小米': {
        'auto': r'YU7|SU7|SU7 Ultra|汽车|车|造车|交付|大定|底盘|续航|智驾',
        'ai': r'MiMo|大模型|AI|机器人|推理|训练',
        '3c': r'手机|小米17|小米16|Redmi|红米|平板|Pad|手表|手环|耳机|电视|路由器|充电宝',
        'home': r'扫地机|洗地机|空气净化|净水|智能门锁|米家|智能家居|空调|冰箱|洗衣机',
    },
    '三星': {
        '3c': r'Galaxy|手机|折叠|平板|手表|耳机|显示器|SSD|存储|芯片|Exynos|半导体',
        'ai': r'AI|大模型|Galaxy AI|半导体|HBM',
        'home': r'电视|冰箱|洗衣机|空调|烘干机',
    },
    '百度': {
        'ai': r'文心|大模型|AI|自动驾驶|萝卜快跑|Apollo|芯片|昆仑|智能云',
    },
    '阿里': {
        'ai': r'通义|大模型|AI|达摩|智能云|Qwen',
    },
    '英伟达': {
        'ai': r'GPU|AI|算力|芯片|训练|推理|CUDA|H100|H200|B100|B200|Blackwell',
        '3c': r'显卡|GeForce|RTX|游戏',
    },
}

# ===== 家居高频词（需家居上下文）=====
HOME_HIGH_FREQ = {'美的', '老板', '海尔', '格力', '石头'}
HOME_CONTEXT = r'家电|家居|厨卫|卫浴|清洁|净化|净水|空调|冰箱|洗衣机|热水器|油烟机|燃气灶|扫地|洗地|智能锁|马桶|浴霸|烘干机|洗碗机|蒸烤箱|集成灶|智能家居|全屋智能|KBC|AWE|家博会'

# ===== 新闻聚合源（极客早知道等多条合一，desc含无关话题）=====
ROUNDUP_SOURCES = {'geekpark', '36Kr', '36kr', 'ifanr', '爱范儿'}

def is_noise(title):
    t = title.lower()
    return any(p.lower() in t for p in NOISE_WORDS)

def is_blacklisted(text, keyword):
    kw_lower = keyword.lower()
    for bl_key in BLACKLIST:
        if bl_key.lower() == kw_lower:
            for pat in BLACKLIST[bl_key]:
                if pat.lower() in text.lower():
                    return True
    return False

def classify_cross_brand(text, brand):
    if brand not in CROSS_BRANDS:
        return None
    rules = CROSS_BRANDS[brand]
    for cat in ['auto', 'ai', '3c', 'home']:
        if cat in rules and re.search(rules[cat], text):
            return cat
    return None  # 无法归类 → 丢弃

def classify(title, desc, source):
    # 新闻聚合源只用标题匹配，避免desc中的无关话题干扰
    ROUNDUP_PLUS = ROUNDUP_SOURCES | {'Wired', 'ArsTechnica', 'MIT-TR', 'TechCrunch', 'TheVerge'}
    if source in ROUNDUP_PLUS:
        text = title
    else:
        text = title + ' ' + desc
    if is_noise(title):
        return None, [], []

    # 噪音平台硬排除（仅允许核心AI大新闻，且必须是新闻而非教程）
    if source in NOISE_PLATFORMS:
        core_ai = r'OpenAI|Anthropic|Claude|GPT-5|DeepSeek|Gemini'
        core_ai_events = r'发布|融资|IPO|开源|禁令|监管|收购|估值|launch|announce|release|raise|funding|ban|acquire'
        if not (re.search(core_ai, text) and re.search(core_ai_events, text, re.I)):
            return None, [], []

    # 跨品类品牌分流（优先于单品类匹配）
    for brand in CROSS_BRANDS:
        if brand in text:
            cat = classify_cross_brand(text, brand)
            if cat:
                return cat, [brand], ['分流']

    # 黑名单全局检查（大小写不敏感）
    text_lower = text.lower()
    for kw in BLACKLIST:
        if kw.lower() in text_lower and is_blacklisted(text, kw):
            return None, [], []

    # 汽车（品牌+事件或人物）
    auto_brands = r'比亚迪|蔚来|理想|问界|特斯拉|零跑|小鹏|极氪|领克|吉利|深蓝|阿维塔|宝马|奔驰|奥迪|沃尔沃|仰望|岚图|长安|大众|丰田|鸿蒙智行|昊铂|腾势|方程豹|埃安|启源|哈弗|坦克|长城|哪吒|飞凡|智己|保时捷|法拉利|劳斯莱斯|宾利|兰博基尼|日产|本田|马自达|别克|凯迪拉克|路虎|捷豹|红旗|捷途|星途|银河|极越|奕境|极石'
    auto_people = r'雷军|李斌|何小鹏|李想|王传福|余承东|魏建军|尹同跃'
    auto_events = r'新车上市|新车型|正式上市|车型上市|交付|降价|涨价|事故|维权|销量|裁员|出海|智驾|FSD|续航|电池|换电|增程|纯电|自动驾驶|预售|大定|工信部|申报图|谍照|路试|官图|试驾|碰撞测试|召回|补贴|购置税|SUV|MPV|轿车|越野|混动|插混|底盘|悬架|充电桩|车机|OTA|城市领航|高速领航|泊车|新能源|电动车|造车|车企|汽车市场|越野车|硬派'
    ab = re.search(auto_brands, text)
    ae = re.search(auto_events, text)
    ap = re.search(auto_people, text)
    if ab and (ae or ap):
        # 负面事件降级（自燃/起火/召回/事故 → 仍归类但降低排序优先级）
        negative_auto = r'自燃|起火|召回|追尾|撞车|失控|刹车失灵|断轴'
        neg = re.search(negative_auto, title)
        return 'auto', [ab.group()], [ae.group() if ae else ap.group()]

    # AI（品牌+事件双命中）
    ai_brands = r'Claude|GPT|OpenAI|Anthropic|DeepSeek|豆包|宇树|Meta AI|Google AI|文心|通义|MiniMax|Kimi|月之暗面|百川|智谱|零一万物|阶跃星辰|面壁|科大讯飞|讯飞星火|Gemini|Llama|Mistral|Cohere|Stability AI|Midjourney|Sora|Runway|Pika|Luma|Figure|Boston Dynamics|波士顿动力|Optimus|优必选|达闼|傅利叶|智元|银河通用|Cursor|Copilot|Windsurf|Devin|Manus|Codex|o1|o3|o4|Grok|Qwen'
    ai_events = r'大模型|融资|估值|IPO|开源|蒸馏|AI安全|AGI|人形机器人|具身智能|多模态|推理|训练|agent|智能体|文生图|文生视频|算力|GPU|TPU|RAG|RLHF|微调|benchmark|跑分|闭源|API|宕机|争议|版权|监管|禁令|发布新模型|模型发布|参数|token|上下文|长文本|思维链|reasoning|代码生成|自主编程|MCP|工具调用|视觉模型|语音模型|图像生成|视频生成|世界模型|强化学习|成本|能耗|效率|数据安全|隐私|数据中心|outsourc|失业|就业|审查|equity|stake|launch|announce|release|unveil|raise|funding|valuation|acquire|partnership|deploy|rollout|security|regulation|ban|pricing|revenue|billion|million|readying|comply|hack|attack|warn|urge|call.for|impact|replace|automat'
    aib = re.search(ai_brands, text)
    aie = re.search(ai_events, text)
    if aib and aie:
        # AI黑名单检查
        if any(re.search(p, title, re.I) for p in AI_BLACKLIST):
            return None, [], []
        # OpenAI博客：只保留新闻，过滤营销/case study
        if source == 'openai' and re.search(r'How.*redesign|How.*build|case study|customer story|is using|leveraging', title, re.I):
            return None, [], []
        return 'ai', [aib.group()], [aie.group()]

    # 家居（品牌或品类命中，高频词需上下文）
    home_brands = r'追觅|石头|云鲸|科沃斯|米家|Aqara|绿米|松下|九牧|徕芬|添可|惠达|海尔|美的|格力|飞利浦|西门子|博世|方太|华帝|万和|林内|能率|摩恩|TOTO|科勒|箭牌|恒洁|安华|Dreame|Roborock|Ecovacs|Narwal|Dyson|Tineco|SwitchBot|Aqara|Xiaomi.*vacuum|Xiaomi.*robot|Nanoleaf|Philips Hue|Eufy|Shark|iRobot|Roomba|Tineco'
    home_products = r'扫地机器人|洗地机器人|智能门锁|智能马桶|升降桌|咖啡机|空气净化器|空气炸锅|净水器|智能家居|新风系统|洗碗机|蒸烤箱|集成灶|油烟机|燃气灶|热水器|浴霸|智能窗帘|智能灯|全屋智能|除螨仪|挂烫机|电动牙刷|剃须刀|美容仪|按摩椅|robot vacuum|robot mop|smart lock|smart thermostat|smart home|smart plug|smart light|smart bulb|smart curtain|air purifier|water purifier|dishwasher|range hood|induction|blender|coffee maker|air fryer|smart display|video doorbell|home assistant|matter|thread|homekit|zigbee'
    home_en_context = r'smart home|robot vacuum|robot mop|home kit|home assistant|matter|thread|zigbee|home automation|smart lock|smart thermostat|smart plug|smart light|air purifier|smart display|video doorbell|smart appliance|cleaning robot|vacuum cleaner|floor washer'
    hb = re.search(home_brands, text, re.I)
    hp = re.search(home_products, text, re.I)
    if hb or hp:
        brand = (hb or hp).group()
        if brand in HOME_HIGH_FREQ:
            if not re.search(HOME_CONTEXT, text):
                return None, [], []
        return 'home', [brand], [brand]

    # 3C（品牌+产品/事件，必须有事件信号）
    tech_brands = r'苹果|iPhone|iPad|MacBook|AirPods|Apple Watch|大疆|DJI|影石|Insta360|OPPO|vivo|三星|索尼|追觅|石头|云鲸|科沃斯|徕芬|戴森|添可|红米|一加|iQOO|realme|真我|荣耀|魅族|锤子|坚果|诺基亚|联想|华硕|ROG|雷蛇|外星人|Bose|JBL|哈曼|Beats|韶音|Switch|PlayStation|Xbox|Steam Deck|Meta Quest|PICO|Nothing|Pixel|Surface|ThinkPad|拯救者|小新|Galaxy|Anker|绿联'
    tech_products = r'折叠屏|降噪耳机|运动相机|无人机|扫地机|洗地机|吸尘器|吹风机|智能手表|手环|充电宝|显卡|折叠手机|翻盖手机|游戏机|VR|AR|头显|投影仪|显示器|键盘|鼠标|路由器|NAS|固态硬盘|SSD|手机|耳机|平板|笔记本|相机|镜头|云台'
    tech_events = r'发布|降价|开售|首发|预约|现货|断货|涨价|评测|拆解|对比|国补|补贴|618|双11|新品|上市|曝光'
    tb = re.search(tech_brands, text)
    tp = re.search(tech_products, text)
    te = re.search(tech_events, text)
    if (tb or tp) and te:
        # 3C黑名单检查
        if any(re.search(p, title, re.I) for p in C3_BLACKLIST):
            return None, [], []
        return '3c', [(tb or tp).group()], [te.group()]

    # 趋势/行业品类（无品牌但有行业趋势信号，仅限高信号关键词，必须在标题中命中）
    trend_auto = r'新能源车涨价|新能源车降价|造车新势力|车市|汽车市场格局|车企淘汰|智驾普及|充电桩涨价|电池涨价|动力电池|固态电池|二手车.*崩盘|油车.*崩盘'
    trend_ai = r'AI监考|AI搜题|AI就业|AI失业|AI教育|AI医疗|AI成本|AI能耗|AI监管|AI审查|算力中心|数据中心|AI产业|大模型降价|大模型免费|AI替代|人工智能产业|AI芯片禁令|芯片股|太空算力'
    if re.search(trend_auto, title):
        return 'auto', ['趋势'], ['行业趋势']
    if re.search(trend_ai, title, re.I):
        return 'ai', ['趋势'], ['行业趋势']

    return None, [], []


def parse_rss_time(s):
    if not s: return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s)
    except: pass
    try: return datetime.fromisoformat(s.replace('Z', '+00:00'))
    except: return None


# ===== 加载数据 =====
with open(domestic_file) as f:
    dom_raw = json.load(f)
dom = []
now_ms = datetime.now(timezone.utc).timestamp() * 1000
dom_cutoff_ms = now_ms - 72 * 3600 * 1000  # 72h window (relaxed from 48h)
dom_skipped_old = 0
dom_skipped_bad_ts = 0
for p in dom_raw.get('data', []):
    src = p.get('name', '?')
    for it in p.get('data', []):
        ts = it.get('timestamp', 0)
        # 48h时间窗口过滤：热榜数据75%超过48h
        if ts:
            if ts < 0 or ts > now_ms + 3600000:
                dom_skipped_bad_ts += 1
                continue  # 跳过时间戳异常的平台(toutiao等)
            if ts < dom_cutoff_ms:
                dom_skipped_old += 1
                continue
        dom.append({'title': it.get('title',''), 'desc': it.get('desc',''), 'source': src})
if dom_skipped_old or dom_skipped_bad_ts:
    print(f"[INFO] 国内数据48h过滤: 保留{len(dom)}条, 跳过老旧{dom_skipped_old}条+异常时间戳{dom_skipped_bad_ts}条", file=sys.stderr)

# 国际RSS（48h窗口）
intl = []
if intl_file:
    try:
        with open(intl_file) as f:
            raw = json.load(f)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=48)
        for it in raw:
            dt = parse_rss_time(it.get('pubDate', ''))
            if dt and dt < cutoff: continue
            intl.append({'title': it.get('title',''), 'desc': it.get('desc','')[:300], 'source': it.get('source','RSS')})
    except Exception as e:
        print(f"[WARN] 国际RSS: {e}", file=sys.stderr)

# 家居RSS（72h窗口）
home_rss = []
if home_file:
    try:
        with open(home_file) as f:
            raw = json.load(f)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=72)
        for it in raw:
            dt = parse_rss_time(it.get('pubDate', ''))
            if dt and dt < cutoff: continue
            home_rss.append({'title': it.get('title',''), 'desc': it.get('desc','')[:300], 'source': it.get('source','RSS-家居')})
    except Exception as e:
        print(f"[WARN] 家居RSS: {e}", file=sys.stderr)


# ===== 运行 =====
seen = set()
cat = {'auto': [], '3c': [], 'ai': [], 'home': []}
unclassified = []  # 通过噪音过滤但未归入任何品类的条目

for src_list in [dom, intl, home_rss]:
    for it in src_list:
        c, brands, signals = classify(it['title'], it.get('desc',''), it['source'])
        if c and it['title'] not in seen:
            seen.add(it['title'])
            cat[c].append({**it, 'cat': c, 'brands': brands, 'signals': signals})
        elif not c:
            # 未归类但通过了噪音过滤 → 保留用于溢出检测
            unclassified.append(it)

# ===== 去重（标题高度重叠的条目只保留第一条）=====
def title_words(t):
    return set(re.sub(r'[，：、。！？\s]+', ' ', t).split())

for c in cat:
    unique = []
    seen_words = []
    for item in cat[c]:
        words = title_words(item['title'])
        is_dup = False
        for sw in seen_words:
            common = words & sw
            if len(common) >= 3 and len(common) / max(len(words), len(sw)) > 0.3:
                is_dup = True
                break
        if not is_dup:
            unique.append(item)
            seen_words.append(words)
    cat[c] = unique

# ===== 溢出热点检测（跨3+平台的未归类超级热点）=====
def extract_keywords(s, min_len=2, max_len=4):
    """提取中文关键词（2-4字连续中文片段）用于话题聚类"""
    # 提取连续中文字符片段
    segments = re.findall(r'[\u4e00-\u9fff]{%d,%d}' % (min_len, max_len), s)
    # 也提取中英混合的关键实体（如"SpaceX""iPhone18"）
    segments += re.findall(r'[A-Za-z][A-Za-z0-9]+', s)
    return set(segments)

def topic_cluster(items, threshold=0.15):
    """将标题相似的条目聚类为同一话题（用关键词匹配，适配中文）"""
    clusters = []
    for item in items:
        kws = extract_keywords(item['title'])
        matched = False
        for cluster in clusters:
            rep_kws = cluster[0]['_kws']
            common = kws & rep_kws
            # 至少共享1个关键词且重叠率>阈值
            if len(common) >= 1 and len(common) / max(len(kws), len(rep_kws)) > threshold:
                cluster.append({**item, '_kws': kws})
                matched = True
                break
        if not matched:
            clusters.append([{**item, '_kws': kws}])
    return clusters

# 对未归类条目做跨平台聚类
overflow_topics = []
if unclassified:
    # 为每条目预计算字符n-gram
    for it in unclassified:
        it['_kws'] = extract_keywords(it['title'])
    clusters = topic_cluster(unclassified)
    for cluster in clusters:
        platforms = set(it['source'] for it in cluster)
        if len(platforms) >= 3:
            # 取最短标题作为代表
            rep = min(cluster, key=lambda x: len(x['title']))
            overflow_topics.append({
                'title': rep['title'],
                'platform_count': len(platforms),
                'platforms': sorted(platforms),
                'count': len(cluster),
            })
    overflow_topics.sort(key=lambda x: x['platform_count'], reverse=True)

# ===== 输出 =====
total = sum(len(v) for v in cat.values())
print(f"## 筛选结果（国内{'+' + str(len(intl)) + '国际' if intl else ''}{'+' + str(len(home_rss)) + '家居RSS' if home_rss else ''}）")
print(f"  汽车:{len(cat['auto'])} | 3C:{len(cat['3c'])} | AI:{len(cat['ai'])} | 家居:{len(cat['home'])} | 总计:{total}")

print(f"\n--- 我关注的热点 ---")
for c, label in [('auto','🚗 汽车'), ('3c','📱 3C数码'), ('ai','🤖 AI'), ('home','🏠 家居')]:
    print(f"\n### {label} ({len(cat[c])}条)")
    for i, r in enumerate(cat[c][:15], 1):
        print(f"  {i}. [{r['source']}] {r['title'][:80]}")
        print(f"     → {'+'.join(r['brands'])} {'+'.join(r['signals'])}")

# 全网热点输出
if overflow_topics:
    print(f"\n### 🔥 全网热点（不在我的关注范围内，但热度很高）({len(overflow_topics)}条)")
    for i, t in enumerate(overflow_topics[:10], 1):
        print(f"  {i}. [{t['platform_count']}个平台] {t['title'][:80]}")
        print(f"     → 平台: {', '.join(t['platforms'][:5])}")

# 保存JSON
with open('/tmp/filtered_daily.json', 'w') as f:
    json.dump({**cat, 'overflow': overflow_topics}, f, ensure_ascii=False, indent=2)
print(f"\n✅ 已保存到 /tmp/filtered_daily.json")
