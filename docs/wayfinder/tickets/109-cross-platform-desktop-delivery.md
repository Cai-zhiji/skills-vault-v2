# 确定跨平台桌面交付方式

- 状态：已决定
- 类型：Product / Architecture
- 阻塞：选择运行时与进程边界、确定本地交付与升级方式
- 解锁：跨平台适配、桌面壳、sidecar、打包与三平台验收

## Decision question

Skills Vault 如何从 macOS/Linux 本地网站演进为 Windows、macOS、Linux 都能开发、安装和一键启动的桌面应用，同时保留现有 Python 领域能力和本地安全模型？

## Resolution

- 接受 Tauri v2 桌面应用作为正式日常入口，浏览器模式保留作开发、诊断和应急入口。
- 继续使用 React SPA 与 Python 领域服务；Python 在生产包中作为平台专属 sidecar，由 Tauri 管理生命周期。
- Node.js 仍只用于开发和构建，不作为桌面应用核心运行时。
- Git 与外部 Skills CLI 是可选增强依赖；缺失时应用仍可启动，并通过依赖中心提供影响说明、安装引导、受控安装计划和重新检测。
- 应用安装资源与用户 Vault 分离；首次启动创建或选择 Vault，旧 Vault 的 schema 变化继续使用 Preview、备份、Apply、事务与恢复。
- macOS/Linux 默认使用受管 symlink；Windows 首版默认使用受管复制，并通过指纹阻止覆盖用户在目标目录中的修改。
- 使用统一 `npm run dev` 与 `npm run package`；打包在目标操作系统分别执行，不假设 PyInstaller 可跨操作系统编译。
- 首批交付 macOS `.app/.dmg`、Windows 安装包和 Ubuntu AppImage；未签名产物只作为内部测试版本。

## Supersedes and preserves

- 扩展 `108-delivery-model` 中“首版 macOS/Linux 本地前台启动”的阶段性范围；Tauri 成为新的正式交付层。
- 保留 `102-runtime-boundary` 确定的 React + Python HTTP 边界，不进行领域服务重写。
- 保留 `104-safety-boundary` 的预览、确认、事务和恢复规则，并将其扩展到 Vault 迁移、受管复制和依赖安装。

## Specification

- [跨平台桌面化需求](../../specs/cross-platform-desktop/requirements.md)
- [跨平台桌面化技术设计](../../specs/cross-platform-desktop/design.md)
