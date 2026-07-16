# Linkly 本地检索前置条件校准

## 背景

实际验证表明，Linkly AI Desktop 的“文件夹”和“知识库”是两个不同层级：

- “文件夹”负责监听并索引本地目录，是 HTTP MCP 本地检索的必要条件。
- “知识库”用于按主题组织或共享资料，是可选能力。
- `list_libraries` 只反映知识库，不反映所有已监听文件夹。因此它返回空列表时，本地 `search` 仍可能正常命中文档。

现有 README 和 Skill 把“已添加知识库”写成必需条件，会把可用的本地检索误判为不可用。

## 目标

统一仓库和 Hermes 本地运行规则，使 Linkly 可用性判断与实际产品行为一致：

1. 前置条件改为 Linkly AI Desktop 正在运行，并在“设置 -> 文件夹”中添加至少一个监听目录。
2. 知识库改为可选的主题组织层，不作为本地搜索前置条件。
3. 不用 `list_libraries` 是否为空判断本地检索可用性。
4. 通过一次真实 `search` 判断本地索引是否可检索；结果为空时按“未命中”降级，不把它误报为 MCP 故障。

## 修改范围

- `README.md`：修正用户侧接入说明和空结果说明。
- `article-pipeline/SKILL.md`：修正 Agent 的检查顺序、失败分类和降级规则。
- `CHANGELOG.md`：新增本次校准记录，并纠正 v0.6.7 的前置条件描述。
- `~/.hermes/skills/pipeline-article/SKILL.md`：同步本机 Hermes 运行规则。

`article-pipeline/references/data-flow.md` 不需要修改，因为 Linkly 在流程中的职责和产物位置没有变化。

## 验证

1. Linkly Desktop 运行，HTTP MCP 往返检查成功。
2. 监听目录包含 `/Users/xxqq/content-pipeline`。
3. `list_libraries` 即使为空，MCP `search` 仍能命中仓库文档。
4. 对长文档按 `search -> outline -> read` 完成读取。
5. 仓库 Skill 和 Hermes 本地 Skill 不再把“没有知识库”当作故障。

## 回滚

仓库修改通过独立提交和版本标签回滚；Hermes 本地 Skill 修改前单独备份。
