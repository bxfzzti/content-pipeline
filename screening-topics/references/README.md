# 筛选Agent Prompt 位置说明

筛选Agent的完整prompt已迁移到：`references/screening-agent-prompt.md`

该prompt包含：
- 50分制评分体系（全网热度×2 + 时效性×2 + 讨论热度×2 + 情绪强度×2 + 内容关联度×2）
- 两层筛选逻辑（先全网热点再关注领域）
- 切入方向类型标注（故事/分析/预判/站队/类比）
- 反面理由排序（信息不足>热度衰减>争议太大>角度写烂>定位不符）
- 输出格式模板

## 执行方式

```python
delegate_task(
    goal="热点筛选分析",
    context="热点数据+内容定位+筛选Agent prompt内容",
    toolsets=["web", "file"]
)
```

主Agent加载本SKILL.md了解筛选规则和流程，需要执行筛选时加载references/screening-agent-prompt.md作为子Agent的指令。
