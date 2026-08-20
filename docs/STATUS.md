# 状态 — Skills Vault v2

## 目标

重构现有 Skills Vault，让 React 网站成为浏览、管理、同步与维护 Agent Skills 的主要入口，同时保留本地优先、安全事务和可恢复性。

## 当前进度

- [x] 确认新项目目录可安全创建。
- [x] 读取旧项目功能、Web 规格和生产接口现状。
- [x] 选定 Wayfinder，并建立本地 Markdown 决策地图。
- [x] 确认 React + shadcn/ui + Tailwind CSS 的前端方向。
- [x] 建立第一版领域词汇、产品规格和视觉方向。
- [x] 建立按功能域组织的项目骨架。
- [ ] 逐张解决 Wayfinder 前沿决策票。
- [ ] 确认运行时边界与旧数据迁移策略。
- [ ] 在决策闭合后生成前后端脚手架。

## 下一步

1. 解决“定义 v2 首发产品边界”，锁定网页主流程与首发功能。
2. 解决“选择运行时与进程边界”，决定 React 构建方式及本地服务形态。
3. 解决“制定旧项目数据迁移方案”，明确复制、复用和重新生成的对象。
4. 根据已闭合决定更新产品规格，再开始 `app/` 与 `server/` 脚手架。

## 关键约束 / 约定

- 项目目录：`/Users/zivenjasek/Desktop/Projects/skills-vault-v2`。
- 网站是主入口；CLI 是辅助入口。
- 前端使用 React、shadcn/ui 与 Tailwind CSS；具体框架和构建器待决策。
- 本地优先，不引入云端账户或远程数据库作为基础依赖。
- 保留 preview → apply → transaction → recovery 的安全模型。
- 不自动删除、暂存、提交或覆盖来源仓库中的用户改动。
- `app/` 与 `server/` 在框架决策前保持为空。
- 仅初始化本地 Git，永不自动 push。
