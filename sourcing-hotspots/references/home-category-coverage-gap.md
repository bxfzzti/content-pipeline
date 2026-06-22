# 家居品类数据源覆盖分析（2026-06-04 更新）

## 现状
扩充3个国际家居RSS源 + 英文关键词后，家居品类从 **2条→6条**（实测均值）。

## 数据源矩阵

| 源 | 类型 | 状态 | 日产量 | 家居内容占比 |
|---|---|---|---|---|
| IT之家 | 中文RSS | ✅ | ~60条 | <5%（家电新闻偶现） |
| 爱范儿 | 中文RSS | ✅ | ~15条 | <5%（智能家居新品偶现） |
| TheVerge SmartHome | 英文RSS | ✅ | ~3条 | >90%（纯智能家居） |
| HomeKit News | 英文RSS | ✅ | ~2条 | >90%（Matter/HomeKit生态） |
| Home Assistant Blog | 英文RSS | ✅ | ~1条 | >90%（智能家居平台） |
| cnBeta | 中文RSS | ✅ | ~150条 | <1%（几乎无家居） |
| SMZDM | cookie | ⚠️ | 未知 | 需cookie+RSSHub路由 |
| 小红书 | cookie/MCP | ⚠️ | 5-10条 | UGC内容，需搜索关键词 |

## 中文家居媒体RSS调研结果

| 媒体 | RSS状态 | 替代方案 |
|---|---|---|
| 好好住 | ❌ 无RSS | 小红书搜索 |
| 住小帮 | ❌ 无RSS | 小红书搜索 |
| 一条 | ❌ 无RSS | 不可用 |
| 良仓 | ❌ 无RSS | 不可用 |
| 少数派 | ✅ RSS可用 | 内容偏数码，家居<10% |
| 什么值得买 | ❌ RSS被拦 | RSSHub + cookie方案 |

**结论：** 中文家居媒体几乎全军覆没（无RSS），家居品类数据源只能靠：
1. 国际智能家居RSS（TheVerge系 + HomeKit News + Home Assistant）— 英文，需英文关键词
2. IT之家/爱范儿少量中文家居内容 — 中文关键词
3. SMZDM + 小红书作为备选 — 需cookie/MCP

## 过滤脚本修复记录

| 问题 | 修复 |
|---|---|
| 英文RSS全被丢弃 | brand/products正则加英文词 + re.I |
| Ring/Nest/Shark误匹配 | 从品牌列表移除，改用产品关键词 |
| 格力/石头误匹配 | 加入HOME_HIGH_FREQ需上下文 |
| 飞利浦显示器误匹配 | 加入黑名单 |
| 黑名单大小写敏感 | 全局检查+is_blacklisted改为case-insensitive |

## 进一步扩充方向

1. **SMZDM cookie方案**：配好cookie后 `/smzdm/ranking/pinlei/11` 可用，预期+10-20条好价
2. **小红书搜索**：`xhs_search` 搜"扫地机评测""智能家居"，预期+5-10条UGC
3. **RSSHub扩展**：`/huxiu/channel/21`（虎嗅车与出行）虽是汽车但偶有智能家居内容
