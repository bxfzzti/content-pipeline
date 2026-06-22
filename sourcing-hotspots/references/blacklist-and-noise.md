# 完整噪音表和黑名单（2026-05-31 验证版）

## 噪音表（标题命中即丢弃）

### 体育
欧冠, 进球, 破门, 比赛, 联赛, 决赛, 阿森纳, 巴黎圣日耳曼, NBA, 马刺, 雷霆, 姆巴佩, 哈弗茨

### 娱乐
王菲, 谢霆锋, 鹿晗, 综艺, 选秀, 偶像, 桃花坞, 演唱会, 明星

### 政治/社会
印度, 高温, 投弃权票, 选举, 国会, 核电站, 俄罗斯, 乌克兰, 古巴, 特朗普, 中南海

### 健康/生活
牙齿, 早睡, 减肥, 养生, 创作主场, 仅退款, 榴莲, 杨梅, 荔枝, 塌陷, 排泄

### 促销
天猫618, 京东618, 优惠券, 发新券, 红包, 秒杀

### 开发者/学术
喜加一, Epic免费, Steam免费, 源码, arxiv, GPIC, npm supply, TanStack

### 事故/社会新闻
月嫂, ICU, 虐猫, 虐童, 戒网瘾, 学术造假, 院长, 追尾货车, 撞向路人, 保时捷为躲避

### 国际噪音
pizza oven, steroid, Arduboy, Steam Controller, Backrooms, Night Vale, art TVs, borked, time killer, YouTubers directed, Lamine Yamal, Beats headphones teased

### 3C噪音
CarPlay, 怎么连, 求教, Raskin, Visionary Behind, 母亲节文案, 问责通告

### AI噪音（非新闻）
AI terms and nodded, What happens when companies, so-called, Coders are refusing

## 黑名单（关键词命中但实际无关）

| 关键词 | 排除模式 | 原因 |
|--------|---------|------|
| 三星 | 三星堆, 三星海力士杠杆 | 三星堆文物≠三星电子, 杠杆ETF≠产品 |
| 眼镜 | 眼镜王蛇, 眼镜蛇 | 蛇≠眼镜产品 |
| 充电 | 充电后自燃, 充电起火 | 安全事故≠充电产品 |
| 发布 | 停售通知, 红色预警, 主题曲, 问责通告, 律师函, 虐猫影像 | 非产品发布 |
| 稳定器 | 尼克尔 | 镜头≠稳定器 |
| 无人机 | 袭击, 残骸, 军事, 美军人形 | 消费无人机≠军事无人机 |

## 搜索引擎限制

DDG/Google/Bing均屏蔽服务器IP（返回首页或验证码），热点搜索只能依赖RSS+hot-aggregator。

## 华为分流规则

华为同时命中多个品类时的优先级：
1. 有汽车事件词（问界/智驾/SUV等）→ 汽车
2. 有芯片/韬定律/麒麟/昇腾/半导体 → AI
3. 有手机/Mate X/Mate 80/降价/激活量 → 3C数码
