# 2026-08-23 macOS 实体构建与验收

## 做了什么
- 安装 Rust/Cargo 1.98.0，补齐应用图标和 Cargo 锁文件，修复 Tauri 壳首次真实编译暴露的 sidecar 句柄问题。
- 通过统一打包入口生成 Skills Vault 2.1.0 的 Apple Silicon `.app` 与 `.dmg`，并输出版本化目录、构建元数据和 SHA-256 校验和。
- 验证应用包和 DMG 内应用的 arm64 架构、ad-hoc 签名、资源封装与校验和；实际启动桌面主进程和内置 sidecar，并确认退出后无残留进程。
- 让打包输出目录在复制新产物前安全清理，避免旧 bundle 混入新的校验文件。

## 为什么
- 只有真实编译、封装和启动才能暴露 Rust API、图标资源、签名以及 Python 运行时之间的问题。
- Apple Silicon 需要至少 ad-hoc 签名；当前内部测试包关闭 Hardened Runtime，以兼容 PyInstaller one-file sidecar 解压的 Python 动态库。
- 对外发布的 Developer ID 签名与公证需要单独验证，不能把内部可运行配置误称为公开发布就绪。

## 卡在哪 / 未决
- macOS 尚未完成创建 Vault、Web v2 迁移、平台部署、恢复与卸载后数据保留的完整安装烟测。
- Hardened Runtime 下的正式 sidecar 打包与 entitlement 方案尚未决定，已登记 Wayfinder 票据 110。
- Windows NSIS 与 Ubuntu AppImage 仍需在对应原生系统构建和验收。

## 下一步
- 在隔离目录完成 macOS DMG 的完整业务安装烟测，并记录用户数据保留结果。
- 评估并确定 Developer ID + Hardened Runtime 下的 sidecar 封装方案，再进行签名与公证。
- 在 Windows 与 Ubuntu 原生环境运行统一打包和验收矩阵。

## CONTEXT.md
- 本次新增/澄清词汇：无。
