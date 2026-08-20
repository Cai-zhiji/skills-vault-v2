# 2026-08-20 后台服务管理命令

## 做了什么
- 增加 `skills start`、`stop`、`restart`、`status`、`logs` 命令，支持后台运行 Skills Vault Web 服务。
- 增加 PID、日志和健康检查管理；命令安装到当前可用的 Homebrew bin 目录后可直接调用。
- 用隔离端口验证启动、状态、日志、重启和停止流程。

## 为什么
- 原先只能在前台终端运行并通过 `Ctrl+C` 停止，日常使用不便，也不利于查看历史运行日志。
- 运行状态放在 `.vault/run/`，日志放在 `.vault/logs/`，遵守运行数据不进入主 Git 的边界。

## 卡在哪 / 未决
- 无。系统级 `/usr/local/bin` 在当前机器不可写，因此命令安装到了 PATH 中可写的 `/opt/homebrew/bin`。

## 下一步
- 如需更完整的长期运行能力，可再增加 macOS launchd 开机启动；当前命令已满足手动后台管理。

## CONTEXT.md
- 本次新增/澄清词汇：无
