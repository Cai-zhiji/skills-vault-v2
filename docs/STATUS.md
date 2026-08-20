# 状态 — Skills Vault v2

## 目标

重构现有 Skills Vault，让 React 网站成为浏览、管理、同步与维护 Agent Skills 的主要入口，同时保留本地优先、安全事务和可恢复性。

## 当前进度

- [x] 完成 Wayfinder 决策地图，闭合首发范围、运行时、数据、安全、信息架构、API、测试与交付决定。
- [x] 建立 React 19 + TypeScript + Vite 8 + shadcn/ui + Tailwind CSS 4 前端。
- [x] 实现 Skills、来源、记录三个一级入口与全局命令面板。
- [x] 实现同步轨、操作轨、详情 Sheet、Preview / Apply Dialog 和响应式布局。
- [x] 建立 Python 本地 API / 静态服务，并通过可配置路径复用 v1 数据工作区。
- [x] 实现个人 Skills Catalog 新鲜度检测和扫描重建。
- [x] 为原创 / 派生 Skill 增加标准 8 节说明文档编辑器，并将保存动作记入事务。
- [x] 修正来源更新边界：脏来源被单独阻塞，安全来源可继续更新。
- [x] 修正详情 Sheet：长简介限制在标题区，正文独立滚动，底部操作栏不再遮挡内容。
- [x] 补齐前端单测、类型检查、Lint、生产构建和后端单元测试。
- [x] 在真实浏览器完成桌面端、390px 窄屏、键盘入口和控制台验收。
- [x] 提供一键启动脚本与项目使用说明。

## 下一步

1. 日常直接运行 `./scripts/vault-ui` 使用网站。
2. 在隔离的数据副本上扩展 Preview / Apply 的浏览器自动化覆盖，避免验收操作真实平台链接。
3. 在隔离数据副本上补充“创建 Skill → 保存说明文档”的完整写入式浏览器测试。
4. 如果需要分发给其他设备，再增加 macOS 应用壳、后台启动或安装包；这些不属于当前本地首发范围。

## 关键约束 / 约定

- 项目目录：`/Users/zivenjasek/Desktop/Projects/skills-vault-v2`。
- 网站是主入口；CLI 仅承担启动、诊断、自动化和应急维护。
- 前端使用 React 19、Vite 8、React Router、TanStack Query、shadcn/ui 与 Tailwind CSS 4。
- 后端使用 Python 标准库 HTTP 服务与现有 Skills Vault 领域服务，无额外运行时依赖。
- 默认数据工作区为相邻的 `/Users/zivenjasek/Desktop/Projects/skills-vault`，可通过 `--vault-root` 或 `SKILLS_VAULT_ROOT` 替换。
- v2 不复制用户数据；Catalog 和运行记录继续由被挂载的数据工作区管理。
- 个人说明文档保存于数据工作区的 `docs/skill-guides/`，仅限 `my` 来源的 Skill 编辑。
- 保留 `preview → apply → transaction → recovery` 安全模型。
- 不自动删除、暂存、提交或覆盖来源仓库中的用户改动。
- 本地 Git only，永不自动 push。
