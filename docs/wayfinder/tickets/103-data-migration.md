# 制定旧项目数据迁移方案

- 状态：待决定
- 类型：Research
- 阻塞：无
- 解锁：确定 API 与异步操作契约、确定本地交付与升级方式

## Decision question

旧项目中的哪些对象是用户数据、配置、可重建视图或运行时状态，v2 应分别复制、引用、导入还是重新生成？

## Known constraints

- `my-skills/`、来源仓库、Profile、annotations 和 Skill guides 包含用户成果。
- Catalog、更新报告和部分运行时状态可重建，但可能具有审计价值。
- 旧工作区包含未提交改动，迁移过程不得整理或覆盖它们。
- 新项目需要独立回退路径。

## Inventory to classify

- 原创与派生 Skills。
- Git / skills-cli 来源及锁定信息。
- Profile 与平台选择。
- annotations 与说明文档。
- Catalog 与冲突报告。
- 事务、备份、预览 token 和安装状态。
- launchd 配置与日志。

## Resolution

待研究票据完成；任何迁移工具必须先提供只读预检。
