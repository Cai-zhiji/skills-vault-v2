# 状态 — Skills Vault v2

## 目标

把 Skills Vault 交付为 Windows、macOS、Linux 可安装的本地优先 Tauri 桌面应用，同时保留 React 工作台、Python 领域服务、安全事务和浏览器诊断入口。

## 当前进度

- [x] 完成 React 工作台、Python 本地 API、Catalog、来源、Profile、批量管理、说明文档、事务和恢复等 Web v2 基础能力。
- [x] 完成跨平台路径与平台适配层，覆盖 macOS、Windows、Linux 的应用目录和 Agent Skills 目标目录。
- [x] 完成 symlink / managed-copy 部署器和安装状态 schema v2；Windows 默认受管复制，用户修改目标时阻止覆盖或删除。
- [x] 平台目标为 Codex、Claude Code 与 Lux Neo；Lux Neo 的 Markdown 入口、资源目录和可选 watcher 配置部署到 `$LUX_HOME/skills`，仅支持独立启用，并保持旧 `both` 只代表 Codex + Claude Code。
- [x] 完成空 Vault 初始化、候选目录识别、普通 Skills 文件夹导入和 Web v2 复制迁移，写操作均使用 Preview / Apply。
- [x] 完成原创 Skill 创建预览，并把前端创建流程切换到一次性 Preview token。
- [x] 完成 Git、Node/npm/npx 与 Skills CLI 可选依赖检测、受控安装计划和依赖中心界面。
- [x] 完成首次启动向导：创建、打开、导入、迁移四个入口；桌面配置与用户 Vault 已分离。
- [x] 建立 Tauri v2 壳、单实例、原生文件夹选择、Python sidecar 生命周期和前端运行配置。
- [x] sidecar 已实现随机回环端口、进程内会话令牌、严格 Origin、父进程监测和优雅关闭；源码模式和 PyInstaller 冻结模式均通过烟测。
- [x] 建立根目录 `npm run dev`、`dev:web`、`test:all`、`package:diagnose` 与 `package` 跨平台入口。
- [x] PyInstaller 6.22.2 已在当前 Apple Silicon Mac 成功生成并启动 sidecar。
- [x] 当前全量验证通过：前端类型、Lint、2 项单测与生产构建；后端 73 项测试通过，其中 8 项真实数据集成测试按约定跳过；Tauri Rust 1 项测试通过。
- [x] 当前 Apple Silicon Mac 已安装 Rust/Cargo 1.98.0，Tauri Rust 壳编译与 1 项 Rust 单测通过。
- [x] 已生成 macOS arm64 `.app/.dmg`，完成应用与 DMG 内签名结构、架构、SHA-256、实际启动及退出回收验收。
- [ ] macOS 完整业务安装验收、Windows NSIS 与 Ubuntu AppImage 实体验收尚未完成。

## 下一步

1. 从 macOS DMG 安装到隔离位置，完成创建 Vault、Web v2 迁移、平台部署、恢复和卸载后数据保留烟测。
2. 决定 macOS Developer ID 签名下的 Python sidecar 方案；当前内部测试包使用 ad-hoc 签名并关闭 Hardened Runtime。
3. 分别在 Windows 与 Ubuntu 原生环境执行相同打包流程，完成中文/空格路径、非管理员安装、managed-copy 和 AppImage 验收。
4. 对外分发前补齐 macOS Developer ID/公证与 Windows 代码签名；在此之前构建元数据必须保持 `internal/testing`。

## 关键约束 / 约定

- 项目目录：`/Users/zivenjasek/Desktop/Projects/skills-vault-v2`。
- Tauri 桌面应用是正式入口；`npm run dev:web` 和旧 Bash 脚本只用于开发、诊断和兼容。
- 最终用户不需要 Node、Rust 或 Python；Python 领域服务由平台专属 PyInstaller sidecar 内置。
- Git 与外部 Skills CLI 是可选增强依赖；缺失时应用仍可启动、创建和管理原创 Skills。
- 用户 Vault 与应用资源、桌面配置分离；升级或卸载应用不得触碰 Vault。
- macOS/Linux 默认部署 symlink，Windows 默认 managed-copy，并使用指纹保护用户在目标目录中的修改。
- 所有重要写操作保留 `preview → apply → transaction → recovery`。
- PyInstaller 不跨操作系统编译；三个平台必须分别构建和验收。
- 当前 Mac 有 Node 22、npm 10、Python 3.9、Rust/Cargo 1.98.0、Xcode Command Line Tools 和项目本地 PyInstaller；无需完整 Xcode 即可生成当前内部测试 DMG。
- 当前 macOS 内部测试包使用 ad-hoc 签名；为兼容 PyInstaller one-file 解压运行，关闭 Hardened Runtime。该设置不代表公开分发方案。
- 当前 macOS arm64 产物位于 `dist/packages/2.1.0/macos-arm64/`，DMG SHA-256 为 `85b5968e543d6ca8043c3882d0c8daa555d3ec78f4ee3fa59a798224027a2d08`。
- 本地 Git only，永不自动 push。
