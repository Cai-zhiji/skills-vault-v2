# Skills Vault v2

以网站为主要入口的本地优先 Agent Skills 管理工作台。

## 先读

- `CONTEXT.md` — 领域词汇表
- `docs/STATUS.md` — 当前状态、进度、下一步
- `docs/wayfinder/map.md` — 决策地图与待澄清边界
- `docs/specs/skills-vault-v2.md` — 当前产品规格

## 规则

- 本地 git only，**永不 push**。
- 每个功能完成即 commit，消息使用简短中文（`feat:` / `fix:` / `chore:`）。
- 未解决的产品或架构问题先更新 Wayfinder 决策票，不在实现中静默猜测。
- 写操作必须保留预览、确认、执行、记录与恢复边界。
- 上游来源与用户原创 Skills 默认视为用户数据，不得静默覆盖或删除。
- 会话结束走 `/session-end`：更新 `docs/STATUS.md`、检查 `CONTEXT.md`、写 devlog、commit。
