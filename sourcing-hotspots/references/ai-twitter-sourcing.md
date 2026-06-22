# AI品类数据源：Twitter/X 行业大佬追踪

## 为什么不用关键词过滤

hot-aggregator 69平台 + 国际RSS 的关键词过滤，AI品类实测数据：
- v1（单品牌触发）：763条，绝大部分是"芯片""推理"泛匹配噪音
- v3（品牌+事件双命中+噪音平台排除+跨品类分流）：211条，质量提升但量仍大
- 根因：hot-aggregator 中大量科技新闻含"芯片""推理""训练"，无法区分AI大模型新闻和普通半导体新闻

**结论：AI品类关键词过滤有天花板，需切换数据源。**

## 方案：xurl 追踪 AI 行业核心声音

用 X/Twitter 官方 CLI（`xurl`）追踪 AI 行业大佬的推文，信号密度远高于关键词过滤。

### 核心追踪列表（15-20人）

| 人物 | 账号 | 身份 | 关注领域 |
|------|------|------|---------|
| Sam Altman | @sama | OpenAI CEO | GPT系列/AGI/OpenAI战略 |
| Dario Amodei | @DarioAmodei | Anthropic CEO | Claude/AI安全/政策 |
| Andrej Karpathy | @karpathy | ex-OpenAI/Tesla AI | 技术深度/教育/开源 |
| Jim Fan | @DrJimFan | NVIDIA AI研究 | 具身智能/机器人/模拟 |
| Yann LeCun | @ylecun | Meta AI首席 | 开源AI/学术/辩论 |
| Demis Hassabis | @demaboris | DeepMind CEO | 科学AI/AlphaFold/Gemini |
| Andrew Ng | @AndrewYNg | AI教育/创业 | AI应用/教育/落地 |
| Elon Musk | @elonmusk | xAI/Grok | Grok/xAI/争议 |
| Ilya Sutskever | @ilyasut | SSI联合创始人 | AI安全/超级智能 |
| Jeff Dean | @JeffDean | Google AI | Google AI/基础设施 |
| Emad Mostaque | @EMostaque | AI创业 | 开源AI/创业 |
| 李彦宏 | @robinli | 百度CEO | 文心/中国AI |
| Jason Wei | @_jasonwei | AI研究 | 推理/scaling |
| swyx | @swyx | AI社区 | AI工程/趋势分析 |

### 执行方式

```bash
# 搜索指定用户最近推文
xurl search "from:sama OR from:karpathy OR from:DarioAmodei" -n 20

# 搜索特定话题
xurl search "from:sama OR from:karpathy AI OR LLM OR model" -n 15

# 单用户推文
xurl search "from:DrJimFan" -n 10
```

### 定时任务集成

每天21:00定时任务中，AI品类改为：
1. 用 `xurl search "from:sama OR from:karpathy OR from:DarioAmodei OR from:DrJimFan OR from:ylecun OR from:demaboris OR from:ilyasut"` 拉24h内推文
2. 用 LLM 从推文中提取 AI 行业重大事件（新模型/融资/产品发布/争议）
3. 输出 3-5 条精选，附推文原文链接

### 前置条件

1. 用户在 https://developer.x.com/en/portal/dashboard 创建 App
2. 获取 Client ID + Client Secret
3. 终端执行：
   ```bash
   xurl auth apps add my-app --client-id YOUR_ID --client-secret YOUR_SECRET
   xurl auth oauth2 --app my-app
   xurl auth default my-app
   ```
4. 验证：`xurl auth status` 和 `xurl whoami`

### 状态

- [x] xurl 已安装（`~/.local/bin/xurl`）
- [ ] X API 凭证待用户配置
- [ ] 定时任务待集成
