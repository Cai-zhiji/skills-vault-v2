# 制定旧项目数据迁移方案

- 状态：已决定
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

最初首版采用外部挂载：旧项目继续作为唯一事实源，v2 只承载应用代码。该决定已被 2026-08-20 的迁移决定取代。

当前决定是让 v2 项目根目录成为唯一活动 Vault，并按数据所有权分层：

- `registry.yaml`、`lock.yaml`、`my-skills/`、`profiles/`、`annotations/` 与 `docs/skill-guides/` 随 v2 主 Git 版本化。
- `sources/` 与项目同目录，但 Git 来源保留各自历史，避免被父仓库压成不可维护的嵌套仓库记录。
- `catalog/` 是可重建索引；`.vault/` 保存本机安装状态、事务、备份和回收站，两者同仓但不进入 v2 主 Git。
- 迁移复制持久数据、审计记录、备份与回收站；过期 Preview token 和旧服务日志不迁移。
- 网站完成来源更新后直接写入 v2 的 `sources/`、`lock.yaml` 和 `catalog/`，不再与旧仓库双向同步。

启动器默认使用 v2 项目根目录。显式 `--vault-root` 优先于 `SKILLS_VAULT_ROOT`，二者只用于测试、诊断或打开其他 Vault。旧项目保持原状，作为迁移回滚副本。
