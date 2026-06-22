# RSS源可靠性实测数据

> 每次热点抓取后更新此文件，记录各数据源的实际返回情况。

## 2026-06-04 实测（验证跑 17:18 CST）

### 国际RSS源（48h窗口）

| 源 | 状态 | 条数 | 备注 |
|---|---|---|---|
| TechCrunch | ✅ | 20 | 稳定 |
| TheVerge | ✅ | 10 | 稳定 |
| TheVerge-Gadgets | ✅ | 10 | 稳定 |
| TheVerge-Transport | ⚠️ | 0 | 持续低迷 |
| Wired | ✅ | 50 | 稳定 |
| ArsTechnica | ✅ | 20 | 稳定 |
| HN-AI | ❌ | 0 | **再次502**，极不稳定 |
| ProductHunt | ✅ | 50 | 稳定 |
| 9to5Mac | ✅ | 44 | 稳定 |
| GoogleAI | ⚠️ | 1 | 极少 |
| 36Kr | ✅ | 30 | 稳定 |
| Engadget | ✅ | 20 | 稳定 |
| GSMArena | ✅ | 20 | 稳定 |
| cnBeta | ✅ | 118 | 稳定，最大RSS源 |

### 家居补充RSS源（72h窗口）（扩充后首次验证）

| 源 | 状态 | 条数 | 备注 |
|---|---|---|---|
| IT之家 | ✅ | 60 | 稳定 |
| 爱范儿 | ✅ | 12 | 稳定 |
| TheVerge SmartHome | ✅ | 3 | 新增源，稳定 |
| HomeKit-News | ✅ | 2 | 新增源，稳定 |
| HomeAssistant | ✅ | 1 | 新增源，稳定（Atom格式） |

### 四品类过滤结果

汽车:12 | 3C:30 | AI:28 | **家居:6** | 总计:76

**家居品类突破：** 从1→6条，新源贡献5/6条（TheVerge-SmartHome + HomeKit-News）。家居品类不再是空白。

### HN-AI 可靠性总结

| 日期 | 状态 | 条数 |
|---|---|---|
| 6/1 凌晨 | ❌ SSL超时 | 0 |
| 6/3 晚间 | ✅ | 28 |
| 6/4 凌晨 | ✅ | 25 |
| 6/4 晚间 | ❌ 502 | 0 |
| 6/4 验证跑 | ❌ 502 | 0 |

**结论：HN-AI 不可靠，降级为bonus源而非主力。**

### 国际RSS源（48h窗口）

| 源 | 状态 | 条数 | 备注 |
|---|---|---|---|
| TechCrunch | ✅ | 20 | 稳定 |
| TheVerge | ✅ | 10 | 稳定 |
| TheVerge-Gadgets | ✅ | 10 | 恢复（凌晨6条） |
| TheVerge-Transport | ⚠️ | 0 | 零条，汽车RSS几乎无产出 |
| ProductHunt | ✅ | 50 | 比凌晨(20)多，时段差异大 |
| HN-AI | ❌ | 0 | **502 Bad Gateway**，凌晨还正常 |
| 9to5Mac | ✅ | 45 | 稳定 |
| Wired | ✅ | 50 | 稳定 |
| ArsTechnica | ✅ | 20 | 稳定 |
| MIT-TR | ✅ | 4 | 少量 |
| GoogleAI | ⚠️ | 1 | 极少 |
| 36Kr | ✅ | 30 | 稳定 |
| Engadget | ✅ | 20 | 新增源，首次验证 |
| GSMArena | ✅ | 20 | 新增源，首次验证 |
| cnBeta | ✅ | 120 | 新增源，大量数据 |

### 家居补充RSS源（72h窗口）（2026-06-04扩充）

| 源 | 状态 | 条数 | 备注 |
|---|---|---|---|
| IT之家 | ✅ | 60 | 连续3天稳定 |
| 爱范儿 | ✅ | 13 | 连续3天稳定 |
| TheVerge SmartHome | ✅ | 3 | 新增源，首次验证 |
| HomeKit News | ✅ | 2 | 新增源，首次验证，含追觅/石头等产品评测 |
| Home Assistant Blog | ✅ | 1 | 新增源，首次验证 |

### 公众号辅助源（搜狗搜索）

| 源 | 状态 | 备注 |
|---|---|---|
| wechat_downloader search | ⚠️ | headless Chrome被搜狗反爬拦截，需非headless环境 |
| wechat_downloader read | ✅ | 直接读mp.weixin.qq.com，不依赖搜狗 |

### 数据覆盖

- **总计原始数据：** hot-aggregator 69平台(~1.6MB, 2905条) + 国际RSS 473条 + 家居RSS 225条
- **四品类过滤后（含48h时间窗口）：** AUTO=38 + 3C=28 + AI=47 + HOME=1 + UNCATEGORIZED=1105
- **AI品类大幅改善(47条)**：品牌+事件双命中+噪音平台排除后，从数百条降到47条
- **家居品类仍极低(1条)**：仅小米米家手持风扇，结构性稀缺持续

### 关键发现

1. **HN-AI可靠性波动大**：凌晨25条正常→晚间502 Bad Gateway。该源不稳定，不能作为AI品类主力依赖。
2. **cnBeta数据量巨大(120条)**：科技综合类，家居含量极低但3C/AI补充效果好。
3. **ProductHunt时段差异大**：凌晨20条→晚间50条，可能与发布周期有关。
4. **TheVerge-Transport持续低迷**：0-1条，汽车RSS几乎无产出，不必重点抓取。
5. **cross-platform验证是关键**：Anthropic IPO仅在RSS中出现（cnBeta/爱范儿/9to5Mac），hot-aggregator中无对应条目。验证脚本必须同时搜索两个数据源。
6. **filter_all_categories.py输出改善**：AI从185条降到47条，品牌+事件双命中效果显著。但仍有误分类（威斯迪镜头被标为AUTO，华硕破晓被标为AUTO），原因是"上市"关键词匹配了非汽车上市语境。

### 可靠源排名（更新 2026-06-04 晚间扩充后）

1. hot-aggregator（国内69平台）-- 主力，每次必须重启
2. cnBeta(120条)+TheVerge系+ArsTechnica+Wired（国际科技，~210条）-- cnBeta新增后成为最大RSS源
3. 36Kr+TechCrunch+9to5Mac+Engadget+GSMArena（国际科技，~135条）-- 稳定
4. ProductHunt(50条) -- 时段差异大，晚间数据更多
5. **家居源扩充后（5源，78条）：** IT之家(60)+爱范儿(12)+TheVerge-SmartHome(3)+HomeKit-News(2)+HomeAssistant(1)
6. HN-AI -- **不可靠**，502错误，降级为备选
7. GoogleAI+MIT-TR -- 数据极少，低优先级

### 家居品类扩充效果（2026-06-04 实测）

| 指标 | 改前（2源） | 改后（5源） |
|------|------------|------------|
| RSS源数 | IT之家+爱范儿 | +TheVerge-SmartHome+HomeKit-News+HomeAssistant |
| 家居RSS总条数 | ~75条 | ~78条 |
| filter输出家居条数 | **1条** | **5条**（真·家居内容） |

**关键发现：英文源需要英文关键词。** 原始filter_all_categories.py只有中文关键词，英文RSS内容（SwitchBot/Dreame/Dyson等）被静默丢弃。添加英文品牌名+产品关键词后，家居品类从1→5条。详见下方pitfall。

---

## 2026-06-04 实测（凌晨抓取）

### 国际RSS源（48h窗口）

| 源 | 状态 | 条数 | 备注 |
|---|---|---|---|
| TechCrunch | ✅ | 20 | 稳定 |
| TheVerge | ✅ | 10 | 稳定 |
| TheVerge-Gadgets | ✅ | 6 | 略少于6/3(10) |
| TheVerge-Transport | ⚠️ | 1 | 极少，汽车专题活跃度低 |
| ProductHunt | ✅ | 20 | 少于6/3(50)，非高峰期 |
| HN-AI | ✅ | 25 | **恢复稳定**，6/1 SSL超时 |
| 9to5Mac | ✅ | 49 | **大幅恢复**，6/1为0 |
| Wired | ✅ | 50 | **首次测到大量数据**，之前未测/为0 |
| ArsTechnica | ✅ | 20 | 稳定 |
| MIT-TR | ✅ | 5 | 少量 |
| GoogleAI | ⚠️ | 1 | 极少 |
| 36Kr | ✅ | 30 | **恢复**，6/1为0 |

### 家居补充RSS源（72h窗口）

| 源 | 状态 | 条数 | 备注 |
|---|---|---|---|
| IT之家 | ✅ | 60 | 连续3天稳定 |
| 爱范儿 | ✅ | 15 | 连续3天稳定 |

### 数据覆盖

- **总计原始数据：** hot-aggregator 69平台(~1.6MB) + 国际RSS 237条 + 家居RSS 75条
- **四品类过滤后：** 汽车33 + 3C数码16 + AI 185 + 家居4 = 238条
- **AI品类仍偏大(185)：** 关键词过滤对半导体/芯片新闻误匹配严重，需人工筛选
- **家居品类偏小(4)：** hot-aggregator天然缺失家居内容，RSS补充后仍少

### 关键发现

1. **RSS源可用性持续波动**：Wired从"未测"到50条，36Kr从0到30，9to5Mac从0到49。永远不要假设某源不可用。
2. **家居RSS已稳定**：IT之家+爱范儿连续3天出数据，可作为家居品类的可靠补充。
3. **AI品类过滤天花板仍在**：185条AI结果中大量是华为/英伟达半导体新闻，与AI大模型无关。关键词过滤的固有局限。
4. **跨平台验证有效**：用Python搜索候选话题在hot-aggregator各平台的出现次数，能有效判断传播势能。3+平台的话题优先级应提升。
5. **filter_all_categories.py脚本稳定运行**：无报错，输出格式正确，可直接用于生产。

### 可靠源排名（更新）

1. hot-aggregator（国内69平台）-- 主力，每次必须重启
2. TheVerge系+ArsTechnica+Wired（国际科技，~80条）-- 国际补充主力
3. 36Kr+TechCrunch+9to5Mac（国际科技，~100条）-- 有时有大量数据
4. IT之家+爱范儿（家居，~75条）-- 家居补充
5. HN-AI+ProductHunt（AI+产品，~45条）-- 特定品类补充
