# 2026-08-23 跨平台桌面交付基础

## 做了什么
- 完成跨平台路径、平台部署、Vault 生命周期与迁移、可选依赖中心、首次启动向导和原创 Skill 创建预览。
- 建立 Tauri v2 桌面壳与 Python sidecar 安全会话，接入原生目录选择、单实例和优雅退出。
- 建立统一开发、测试与打包入口；当前 Mac 已成功构建并启动 Apple Silicon PyInstaller sidecar。
- 补充三类用户的 Vault 初始化/迁移指南，并把桌面入口和数据所有权写入 README 与领域词汇表。

## 为什么
- 采用 Tauri + React + Python sidecar，保留成熟领域服务，同时让最终用户不依赖 Python、Node 或 Rust。
- 把桌面配置与 Vault 分开，确保应用升级、卸载和运行缓存不会成为用户 Skills 数据的所有者。
- 将 Git 和 Skills CLI 设计为可选能力，避免外部环境缺失阻塞首次启动与原创 Skill 管理。

## 卡在哪 / 未决
- 当前 Mac 缺少 Rust/Cargo，因此 Tauri Rust 壳尚未编译，macOS `.app/.dmg` 尚未生成。
- Windows NSIS 与 Ubuntu AppImage 必须在对应原生系统构建和验收。
- 对外分发所需的 macOS 公证和 Windows 代码签名凭证尚未配置。

## 下一步
- 安装 Rust 后先执行 Cargo 测试与 `npm run dev`，修正可能的 Tauri Rust API 编译差异。
- 再运行 `npm run package`，完成 macOS 安装包及真实首次启动、迁移、部署和数据保留验收。
- 最后转到 Windows 与 Ubuntu 原生环境完成对应安装包验收。

## CONTEXT.md
- 本次新增/澄清词汇：Vault 根目录、桌面配置、受管复制、sidecar。
