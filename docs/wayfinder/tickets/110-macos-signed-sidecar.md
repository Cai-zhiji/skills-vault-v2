# 确定 macOS 正式签名下的 sidecar 打包方式

- 状态：待决定
- 类型：Architecture / Release
- 阻塞：macOS 对外分发与公证
- 解锁：Developer ID 签名、公证和公开下载

## Decision question

Skills Vault 如何在启用 macOS Hardened Runtime、Developer ID 签名和公证时，可靠运行包含 Python 运行时的 sidecar？

## Current evidence

- PyInstaller one-file sidecar 可在源码构建和未启用 Hardened Runtime 的 ad-hoc 签名包中正常运行。
- Tauri 默认启用 Hardened Runtime 后，sidecar 解压出的系统 Python 动态库因 Team ID 不同被 library validation 拒绝，桌面应用无法完成启动握手。
- 当前 `internal/testing` 包明确关闭 Hardened Runtime，并已通过 `.app/.dmg` 启动与退出回收烟测；这不是公开分发方案。

## Options to evaluate

- 改用 PyInstaller onedir，把 Python 运行时作为嵌套代码随应用签名。
- 保留 one-file，但为正式签名配置最小、可审计的 library-validation entitlement。
- 使用面向 macOS 分发的独立 Python 运行时或其他 sidecar 封装方式。

## Acceptance boundary

- 必须使用 Developer ID Application 身份签名，并通过 `codesign --verify --deep --strict`。
- 必须在 Hardened Runtime 下实际启动 sidecar、完成 API 握手和优雅退出。
- 必须完成 Apple 公证与 stapling 验证；签名凭证不得进入仓库或构建日志。
- 不得以关闭安全机制的内部测试配置冒充公开发布就绪。
