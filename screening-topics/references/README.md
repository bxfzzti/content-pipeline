# 筛选Agent Prompt 位置说明

筛选Agent的完整prompt已迁移到：`references/screening-agent-prompt.md`

该prompt包含：
- 三线并行评分体系（热点观点/消费决策/经验沉淀分别按权重计分）
- 两层筛选逻辑（先全网热点再关注领域）
- 用户插入选题分流逻辑
- 反面理由排序（信息不足>热度衰减>争议太大>角度写烂>定位不符）
- JSON 输出契约

## 执行方式

```python
delegate_task(
    goal="热点筛选分析",
    context="热点数据+内容定位+筛选Agent prompt内容",
    toolsets=["web", "file"]
)
```

主Agent加载本SKILL.md了解筛选规则和流程，需要执行筛选时加载references/screening-agent-prompt.md作为子Agent的指令。
