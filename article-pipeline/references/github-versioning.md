# GitHub 版本管理流程

## 仓库

https://github.com/bxfzzti/content-pipeline

## 发布流程

每次流水线有变更（prompt 修改、新增模块、接入新能力）后，执行以下步骤：

### 1. 同步文件

```bash
# 将最新文件复制到仓库
cp -r ~/.hermes/skills/content-engine/article-pipeline/* /tmp/content-pipeline-v1/article-pipeline/
cp -r ~/.hermes/skills/writing/angle-selection/* /tmp/content-pipeline-v1/angle-selection/
cp -r ~/.hermes/skills/screening-topics/* /tmp/content-pipeline-v1/screening-topics/
cp -r ~/.hermes/skills/sourcing-hotspots/* /tmp/content-pipeline-v1/sourcing-hotspots/
cp -r ~/.hermes/skills/writing/title-craft/* /tmp/content-pipeline-v1/title-craft/
cp -r ~/.hermes/skills/content-engine/xhs-adapter/* /tmp/content-pipeline-v1/xhs-adapter/
cp ~/.hermes/zvec-content-poc.py /tmp/content-pipeline-v1/zvec/zvec_kb.py
```

### 2. 更新 CHANGELOG

在 `/tmp/content-pipeline-v1/CHANGELOG.md` 顶部添加新版本记录：

```markdown
## vX.Y.Z — YYYY-MM-DD: 版本标题

**核心变更**：一句话描述

### 变更详情
- ...
```

### 3. 提交 + 打 tag + 推送

```bash
cd /tmp/content-pipeline-v1
git add -A
git commit -m "vX.Y.Z: 版本标题"
git tag -a vX.Y.Z -m "vX.Y.Z: 版本标题"
git push origin main
git push origin vX.Y.Z
```

## 版本命名规则

- **主版本.次版本.补丁版本**（如 v0.4.0）
- 主版本：架构级变更（如从单 Agent 到多 Agent）
- 次版本：功能新增（如新增 zvec 知识库）
- 补丁版本：prompt 修复、bug 修复、文档更新
