# 状态 — Skills Vault v2

## 目标

重构现有 Skills Vault，让 React 网站成为浏览、管理、同步与维护 Agent Skills 的主要入口，同时保留本地优先、安全事务和可恢复性。

## 当前进度

- [x] 完成 Wayfinder 决策地图，闭合首发范围、运行时、数据、安全、信息架构、API、测试与交付决定。
- [x] 建立 React 19 + TypeScript + Vite 8 + shadcn/ui + Tailwind CSS 4 前端。
- [x] 实现 Skills、来源、记录三个一级入口与全局命令面板。
- [x] 实现同步轨、操作轨、详情 Sheet、Preview / Apply Dialog 和响应式布局。
- [x] 建立 Python 本地 API / 静态服务，并保留可配置 Vault 根目录用于测试和诊断。
- [x] 实现个人 Skills Catalog 新鲜度检测和扫描重建。
- [x] 补齐 Skill 删除入口：支持 Preview、影响摘要、个人归档恢复与上游隐藏。
- [x] 补齐同名 Skill 比较入口：列表和详情均可查看来源元数据与 `SKILL.md` unified diff。
- [x] 增加 `skills` 后台服务管理命令，支持启动、停止、重启、状态检查和日志查看。
- [x] 增加 Skills 批量管理：当前筛选结果多选、批量设置启用范围，以及批量删除 / 移出预览。
- [x] 为原创 / 派生 Skill 增加标准 8 节说明文档编辑器，并将保存动作记入事务。
- [x] 修正来源更新边界：脏来源被单独阻塞，安全来源可继续更新。
- [x] 修正详情 Sheet：长简介限制在标题区，正文独立滚动，底部操作栏不再遮挡内容。
- [x] 补齐前端单测、类型检查、Lint、生产构建和后端单元测试。
- [x] 在真实浏览器完成桌面端、390px 窄屏、键盘入口和控制台验收。
- [x] 提供一键启动脚本与项目使用说明。
- [x] 将 v1 的持久数据迁入 v2，并让项目根目录成为唯一活动数据工作区。
- [x] 支持在不重置平台目录的前提下，将旧 Vault 已纳管链接安全改指向新根目录。

## 下一步

1. 日常直接运行 `./scripts/vault-ui` 使用网站；来源更新、扫描和说明维护都写入 v2 内部数据。
2. 在来源页审阅 `mattpocock` 从 `9c9f36cc` 到当前远端版本的更新 Preview，再决定是否应用。
3. 在隔离的数据副本上扩展删除 Skill、批量管理与冲突比较的浏览器自动化覆盖，避免验收操作真实平台链接。
4. 在隔离数据副本上补充“创建 Skill → 保存说明文档”的完整写入式浏览器测试。
5. 如果需要分发给其他设备，再增加 macOS 应用壳、后台启动或安装包；这些不属于当前本地首发范围。

## 关键约束 / 约定

- 项目目录：`/Users/zivenjasek/Desktop/Projects/skills-vault-v2`。
- 网站是主入口；CLI 仅承担启动、诊断、自动化和应急维护。
- 前端使用 React 19、Vite 8、React Router、TanStack Query、shadcn/ui 与 Tailwind CSS 4。
- 后端使用 Python 标准库 HTTP 服务与现有 Skills Vault 领域服务，无额外运行时依赖。
- 默认 Vault 根目录就是 `/Users/zivenjasek/Desktop/Projects/skills-vault-v2`，可在测试或诊断时通过 `--vault-root` 或 `SKILLS_VAULT_ROOT` 替换。
- 原创 Skills、配置、Profiles、注解和说明文档由 v2 主 Git 跟踪；来源仓库独立版本化，Catalog 与 `.vault` 为同仓非跟踪数据。
- 旧项目 `/Users/zivenjasek/Desktop/Projects/skills-vault` 只保留作回滚副本，不参与运行或双向同步。
- 个人说明文档保存于 Vault 根目录的 `docs/skill-guides/`，仅限 `my` 来源的 Skill 编辑。
- 保留 `preview → apply → transaction → recovery` 安全模型。
- 不自动删除、暂存、提交或覆盖来源仓库中的用户改动。
- 本地 Git only，永不自动 push。
