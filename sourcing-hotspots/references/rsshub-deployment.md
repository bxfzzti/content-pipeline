# RSSHub 部署与配置

## 部署（Docker，端口1200）
```bash
docker run -d --name rsshub -p 1200:1200 --restart unless-stopped diygod/rsshub:latest
```

## 已验证可用路由（无需cookie）
| 路由 | 状态 | 内容 |
|------|------|------|
| /sspai/matrix | ✅ 200 | 少数派矩阵文章（20条，含家居+科技） |
| /36kr/newsflashes | ✅ 200 | 36氪快讯 |
| /36kr/information/web_news | ✅ 200 | 36氪新闻 |

## 需要cookie的路由
| 路由 | 需要 | 说明 |
|------|------|------|
| /smzdm/keyword/:keyword | SMZDM_COOKIE | 什么值得买关键词订阅 |
| /smzdm/ranking/:type/:id/:hour | SMZDM_COOKIE | 品类排行榜 |
| /smzdm/haowen | SMZDM_COOKIE | 好文推荐 |
| /smzdm/baoliao | SMZDM_COOKIE | 爆料 |
| /sspai/featured | 配置 | 少数派精选 |
| /ithome/ranking | 配置 | IT之家排行 |

## SMZDM cookie获取
1. 浏览器登录 smzdm.com
2. F12 → Application → Cookies
3. 复制 smzdm_cookie 和 sess 值
4. 设置环境变量：docker run -e SMZDM_COOKIE=xxx

## 直接可用的RSS（不需要RSSHub）
- 少数派: https://sspai.com/feed (200 ✅)
- IT之家: https://www.ithome.com/rss/ (200 ✅)
- 爱范儿: https://www.ifanr.com/feed (200 ✅)
- 36氪: https://36kr.com/feed (200 ✅)

## 已知限制
- rsshub.app 公共实例已限流(403)，必须自建
- DDG/Google/Bing 均屏蔽服务器IP，搜索引擎不可用
- Docker首次拉镜像约1-2分钟
