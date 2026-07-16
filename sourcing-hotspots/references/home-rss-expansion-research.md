# 家居RSS源扩充调研（2026-06-04）

## 已验证可用的国际家居RSS源

| 源 | URL | 条数/天 | 内容 |
|---|---|---|---|
| TheVerge SmartHome | `https://www.theverge.com/rss/smart-home/index.xml` | ~3-10 | 智能家居产品/评测 |
| HomeKit News | `https://homekitnews.com/feed/` | ~2-10 | Matter/HomeKit生态 |
| Home Assistant Blog | `https://www.home-assistant.io/atom.xml` | ~1-20 | 智能家居平台/生态 |
| CNET Smart Home | `https://www.cnet.com/rss/smart-home/` | ~1-5 | 智能家居产品 |
| Wirecutter | `https://www.nytimes.com/wirecutter/feed/` | ~10-20 | 家居产品评测 |
| Dwell | `https://www.dwell.com/@dwell/rss` | ~20+ | 家居设计/装修 |
| Bob Vila | `https://www.bobvila.com/feed` | ~20+ | 家居装修/DIY |
| ZDNet Smart Home | `https://www.zdnet.com/topic/smart-home/rss.xml` | ~5 | 智能家居 |

## 测试失败的源

| 源 | 状态 | 原因 |
|---|---|---|
| Digital Trends Smart Home | 403 | 拒绝访问 |
| Consumer Reports | 403 | 拒绝访问 |
| Apartment Therapy | 403 | 拒绝访问 |
| Reddit 子版 | 403 | Reddit已屏蔽RSS |
| 好好住/住小帮/一条 | 无RSS | 中文家居媒体无RSS |
| 什么值得买 | 302 | 需登录，RSS被拦 |

## 中文家居内容源（需间接获取）

| 源 | 方案 | 预期 |
|---|---|---|
| 什么值得买 | RSSHub + cookie | +10-20条 |
| 少数派 Matrix | RSSHub `/sspai/matrix` | 4条/次 |
| 小红书 | 禁止个人登录态；仅用户主动提供材料 | 不计入自动抓取 |

## 过滤脚本关键词

英文品牌：Dreame/Roborock/Ecovacs/Narwal/Dyson/Tineco/SwitchBot/Nanoleaf/Eufy/iRobot/Roomba
英文品类：robot vacuum/robot mop/smart lock/smart thermostat/smart home/smart plug/smart light/air purifier/video doorbell/home assistant/matter/thread/homekit/zigbee
