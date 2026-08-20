# 选择运行时与进程边界

- 状态：已决定
- 类型：Research
- 阻塞：无
- 解锁：确定 API 与异步操作契约、确定本地交付与升级方式

## Decision question

React 前端、文件系统/Git 领域能力与本地 HTTP 服务应如何分进程、构建和启动？

## Known constraints

- 应用需要访问本地文件系统、Git、Codex 与 Claude Code 的用户级目录。
- 旧项目已有 Python 领域服务与本地 HTTP API。
- 首发保持本地优先，网站需要易于启动。
- React + shadcn/ui + Tailwind CSS 已确认。

## Options to examine

- Vite SPA + 继续复用/重构 Python 本地服务。
- React Router framework 的静态客户端 + Python 本地服务。
- 单一 JavaScript/TypeScript 本地服务重写领域适配层。
- 桌面壳仅作为后续交付层，不改变核心 HTTP 边界。

## Evidence required

- 对旧 Python 服务可复用程度做接口级盘点。
- 比较开发体验、打包复杂度、流式进度、文件权限和测试接缝。
- 明确 Node 是否仅为构建依赖，还是生产运行依赖。

## Resolution

使用 Vite + React + TypeScript 构建 SPA，React Router 承担页面路由。Node.js 只用于开发与构建，不作为生产领域运行时。

后端继续使用 Python 标准库本地 HTTP 服务，并迁入 v2 独立维护；生产模式由同一进程提供 `/api/*` 与 `app/dist` 静态文件。开发模式由 Vite 把 `/api` 代理到 Python 服务。

后续数据归属决定将默认 seam 收拢到 v2 项目根目录：服务代码和活动数据同仓放置，调用方无需配置路径。`--vault-root` 或 `SKILLS_VAULT_ROOT` 继续作为测试、诊断和打开其他 Vault 的显式适配入口。
