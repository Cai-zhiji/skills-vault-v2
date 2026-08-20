# 确定新项目边界

- 状态：已决定
- 类型：Task

## Decision question

v2 应在旧仓库中原地改造，还是建立独立项目？

## Resolution

在 `/Users/zivenjasek/Desktop/Projects/skills-vault-v2` 建立独立项目。旧仓库作为功能事实、数据格式和迁移来源，不在初始化过程中修改或提交其未完成工作。

## Rationale

用户已经指定新的项目地址；旧仓库当前也包含大量未提交变化。独立初始化能保持回退路径，并把“迁移什么”变成显式决定。
