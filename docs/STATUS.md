# 状态 — Skills Vault v2

## 目标

把 Skills Vault 交付为 Windows、macOS、Linux 可安装的本地优先 Tauri 桌面应用，同时保留 React 工作台、Python 领域服务、安全事务和浏览器诊断入口。

## 当前进度

- [x] 完成 React 工作台、Python 本地 API、Catalog、来源、Profile、批量管理、说明文档、事务和恢复等 Web v2 基础能力。
- [x] 完成跨平台路径与平台适配层，覆盖 macOS、Windows、Linux 的应用目录和 Agent Skills 目标目录。
- [x] 完成 symlink / managed-copy 部署器和安装状态 schema v2；Windows 默认受管复制，用户修改目标时阻止覆盖或删除。
- [x] 完成空 Vault 初始化、候选目录识别、普通 Skills 文件夹导入和 Web v2 复制迁移，写操作均使用 Preview / Apply。
- [x] 完成原创 Skill 创建预览，并把前端创建流程切换到一次性 Preview token。
- [x] 完成 Git、Node/npm/npx 与 Skills CLI 可选依赖检测、受控安装计划和依赖中心界面。
- [x] 完成首次启动向导：创建、打开、导入、迁移四个入口；桌面配置与用户 Vault 已分离。
- [x] 建立 Tauri v2 壳、单实例、原生文件夹选择、Python sidecar 生命周期和前端运行配置。
- [x] sidecar 已实现随机回环端口、进程内会话令牌、严格 Origin、父进程监测和优雅关闭；源码模式和 PyInstaller 冻结模式均通过烟测。
- [x] 建立根目录 `npm run dev`、`dev:web`、`test:all`、`package:diagnose` 与 `package` 跨平台入口。
- [x] PyInstaller 6.22.2 已在当前 Apple Silicon Mac 成功生成并启动 sidecar。
- [x] 当前全量验证通过：前端类型、Lint、2 项单测与生产构建；后端 57 项测试通过，其中 8 项真实数据集成测试按约定跳过。
- [ ] Tauri Rust 壳尚未在当前机器编译；当前系统缺少 Rust/Cargo。
- [ ] macOS `.app/.dmg`、Windows NSIS 与 Ubuntu AppImage 尚未完成实体安装验收。

## 下一步

1. 在当前 Mac 安装 Rust 1.77.2+（推荐 rustup），先运行 `cargo test --manifest-path src-tauri/Cargo.toml`，处理任何 Rust API/编译问题。
2. 运行 `npm run dev` 验证 Tauri 窗口、原生目录选择、首次启动和退出时 sidecar 回收。
3. 运行 `npm run package` 生成未签名 macOS `.app/.dmg`，完成创建 Vault、Web v2 迁移、平台部署和卸载后数据保留烟测。
4. 分别在 Windows 与 Ubuntu 原生环境执行相同打包流程，完成中文/空格路径、非管理员安装、managed-copy 和 AppImage 验收。
5. 对外分发前补齐 macOS Developer ID/公证与 Windows 代码签名；在此之前构建元数据必须保持 `internal/testing`。

## 关键约束 / 约定

- 项目目录：`/Users/zivenjasek/Desktop/Projects/skills-vault-v2`。
- Tauri 桌面应用是正式入口；`npm run dev:web` 和旧 Bash 脚本只用于开发、诊断和兼容。
- 最终用户不需要 Node、Rust 或 Python；Python 领域服务由平台专属 PyInstaller sidecar 内置。
- Git 与外部 Skills CLI 是可选增强依赖；缺失时应用仍可启动、创建和管理原创 Skills。
- 用户 Vault 与应用资源、桌面配置分离；升级或卸载应用不得触碰 Vault。
- macOS/Linux 默认部署 symlink，Windows 默认 managed-copy，并使用指纹保护用户在目标目录中的修改。
- 所有重要写操作保留 `preview → apply → transaction → recovery`。
- PyInstaller 不跨操作系统编译；三个平台必须分别构建和验收。
- 当前 Mac 有 Node 22、npm 10、Python 3.9、Xcode Command Line Tools 和可用的项目本地 PyInstaller；缺少 Rust/Cargo 与完整 Xcode。
- 本地 Git only，永不自动 push。
