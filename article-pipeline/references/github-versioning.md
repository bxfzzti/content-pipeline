# GitHub 版本管理流程

## 仓库

https://github.com/bxfzzti/content-pipeline

本地 clone：`/Users/xxqq/content-pipeline/`

## 自动发布脚本（推荐）

```bash
~/.hermes/scripts/publish-pipeline.sh "变更说明"          # patch (v0.4.1 → v0.4.2)
~/.hermes/scripts/publish-pipeline.sh "变更说明" minor    # minor (v0.4 → v0.5)
~/.hermes/scripts/publish-pipeline.sh "变更说明" major    # major (v0 → v1)
~/.hermes/scripts/publish-pipeline.sh --dry-run           # 仅预览，不提交
```

脚本自动完成：
1. rsync 同步 7 个模块（article-pipeline / sourcing-hotspots / screening-topics / angle-selection / title-craft / xhs-adapter / zvec）
2. 检测变更（无变更则跳过）
3. 自动版本号递增
4. 更新 CHANGELOG.md（插入新版本条目 + 变更文件列表）
5. git commit + tag + push to GitHub

## 手动发布流程（备用）

如果脚本不可用，手动步骤：

### 1. 同步文件

```bash
cd /Users/xxqq/content-pipeline

# 7个模块的源路径
rsync -av --delete ~/.hermes/skills/content-engine/article-pipeline/ article-pipeline/
rsync -av --delete ~/.hermes/skills/sourcing-hotspots/ sourcing-hotspots/
rsync -av --delete ~/.hermes/skills/screening-topics/ screening-topics/
rsync -av --delete ~/.hermes/skills/writing/angle-selection/ angle-selection/
rsync -av --delete ~/.hermes/skills/writing/title-craft/ title-craft/
rsync -av --delete ~/.hermes/skills/content-engine/xhs-adapter/ xhs-adapter/
cp ~/.hermes/zvec-content-poc.py zvec/zvec_kb.py
```

### 2. 更新 CHANGELOG

在 CHANGELOG.md 顶部（第一个 `---` 之后）添加新版本记录。

### 3. 提交 + 推送

```bash
git add -A
git commit -m "vX.Y.Z: 版本标题"
git tag vX.Y.Z
git push origin main --tags
```

## 版本命名规则

- **主版本.次版本.补丁版本**（如 v0.4.0）
- 主版本：架构级变更（如从单 Agent 到多 Agent）
- 次版本：功能新增（如新增 zvec 知识库）
- 补丁版本：prompt 修复、bug 修复、文档更新

## ⚠️ Pitfalls

- **macOS bash 3.x 不支持 `declare -A`**：脚本用函数封装 `rsync` 代替关联数组，确保兼容性
- **模块路径可能变化**：如果 skill 目录结构调整，需同步更新脚本中的路径映射
- **必须先 `cd` 到仓库目录**：git 操作依赖 cwd 在 repo 内
