# Wayfinder 地图 — Skills Vault v2

## Destination

交付一个以网站为主要入口的 Skills Vault v2：用户能在一个本地 React 工作台中理解并管理 Skills、来源、平台同步与恢复状态；核心写操作安全、可预览、可追踪、可恢复；旧项目中的用户数据和成熟领域能力有明确迁移路径。

到达标志：没有会阻止脚手架和首个纵向切片的遗留决定，产品规格能够拆成实现任务而无需开发者猜测。

## Notes

- 地图采用本地 Markdown，替代当前不可用的 Wayfinder tracker 集成。
- 地图只保存决定摘要和链接；完整理由只存在于对应票据。
- 票据按标题引用，不依赖编号。
- 当前处于“画图”阶段，不在 `app/` 或 `server/` 中实现功能。
- 参考旧项目事实，但不默认复制旧的信息架构或技术债务。

## Decisions so far

- 网站成为主要入口；CLI 退居辅助角色。见[确定网站主入口](tickets/001-web-primary-entry.md)。
- 前端基础确定为 React + shadcn/ui + Tailwind CSS。见[确定前端组件基础](tickets/002-frontend-foundation.md)。
- 视觉采用“本地仓库工作台”，以同步轨作为签名元素。见[确定视觉基线](tickets/003-visual-baseline.md)。
- v2 使用独立新目录，本轮只建立文档化骨架与本地 Git。见[确定新项目边界](tickets/004-new-project-boundary.md)。

## Decision frontier

以下票据可以从前沿开始解决：

1. [定义 v2 首发产品边界](tickets/101-product-scope.md)
2. [选择运行时与进程边界](tickets/102-runtime-boundary.md)
3. [制定旧项目数据迁移方案](tickets/103-data-migration.md)
4. [确定安全事务与权限边界](tickets/104-safety-boundary.md)

在前沿决定后再处理：

5. [确认信息架构与页面模型](tickets/105-information-architecture.md)
6. [确定 API 与异步操作契约](tickets/106-api-contract.md)
7. [确定测试接缝与验收矩阵](tickets/107-testing-seams.md)
8. [确定本地交付与升级方式](tickets/108-delivery-model.md)

## Not yet specified

- 是否在首发支持 Codex / Claude Code 之外的平台。
- 是否需要在 v2 内置 Skill 编辑器或仅提供外部编辑入口。
- Skill 说明文档由独立阅读页、详情侧栏还是双模式承载。
- 是否需要插件化后端或平台适配器市场。
- 是否需要跨设备同步；当前默认不属于首发。
- 项目名称、图标和对外品牌是否沿用 Skills Vault。

这些问题目前仍处于战争迷雾中；只有在前置决定完成后能精确陈述时才升级为票据。

## Out of scope

- 本地图阶段不编写生产 React 或服务端代码。
- 不修改、整理或提交旧项目工作区中的现有未提交改动。
- 不自动迁移 `sources/`、`my-skills/`、Profile、说明文档或运行时状态。
- 不发布到远端 Git，不配置云端 CI/CD。
- 不直接复制参考站点的品牌外观、素材或专有字体。
