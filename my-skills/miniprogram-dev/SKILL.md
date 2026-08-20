---
name: miniprogram-dev
description: 微信小程序开发综合技能 — 覆盖小程序端（真机预览、体验版上传）与云开发（云函数、数据库、存储）全流程。Use when the user mentions 微信小程序开发 / 小程序命令行 / cli preview / cli upload / 云函数部署 / 云开发 / CloudBase / 微信云开发 / CloudBase MCP API Key / 不打开网站上传。小程序端操作走开发者工具 `cli`（自查：以 `cli -h` 为准）；云开发上传走 CloudBase MCP（manageFunctions 等）；云开发编码规范参照 `cloudbase` 技能。
---

# miniprogram-dev — 微信小程序开发综合技能

覆盖微信小程序从开发到上线的完整工作流：小程序端预览/上传（开发者工具 `cli`）+ 云开发（CloudBase MCP 上传 + `cloudbase` 技能规范）。

## 工具分工（核心）

| 环节 | 通道 |
|---|---|
| 小程序端真机预览 / 上传体验版 | 开发者工具 `cli` |
| 云函数上传 / 部署 / 配置 | **CloudBase MCP**（`manageFunctions` / `queryFunctions`）|
| 云开发数据库 / 存储 / 网关 / 环境 | CloudBase MCP（`queryXxx` 读 / `manageXxx` 写）|
| 云开发编码规范 | `cloudbase` 技能（`~/.claude/skills/cloudbase`）|

**为什么**：`cli cloud functions deploy` 在部分工具版本会触发 `EISDIR` 打包 bug（本会话实测），云函数上传一律走 MCP，不用 cli。

## 小程序端 — 预览与上传（cli）

核心原则**自查**：cli 自描述，每个命令与参数的唯一可信来源是 `-h` 输出，运行前一律先自查。

前置：开发者工具已装（macOS 二进制 `/Applications/wechatwebdevtools.app/Contents/MacOS/cli`）；登录由用户在自己打开的开发者工具中完成，agent 只检查状态。

1. **定位 cli**：`cli -h` 能打印命令列表
2. **确认登录**：`cli islogin` 返回 `{"login":true}`；未登录时**由用户自己在开发者工具扫码登录**，agent 只检查等待，不在终端代为登录
3. **自查命令**：`cli <verb> -h`（中文 `cli <verb> --lang zh -h`）读取本次准确参数
4. **执行**：`--project <路径>` 指向含 `project.config.json` 的目录
5. **验证**：预览确认二维码可扫码；上传到公众平台「版本管理」核对

命令地图（自查用，非最终参数）：

| 任务 | 起点 |
|---|---|
| 全部命令 / 中文帮助 | `cli -h` / `cli --lang zh -h` |
| 登录态检查 | `cli islogin` |
| 真机预览 | `cli preview`（`-f` 二维码格式、`-o` 输出、`-i` 信息 json）|
| 自动预览 | `cli auto-preview` |
| 上传体验版 | `cli upload`（`-v` 版本号、`-d` 备注均必填）|
| 构建 npm | `cli build-npm` |
| 打开 / 关闭项目 | `cli open` / `cli open-other` / `cli close` / `cli quit` |
| 云开发（只读查询）| `cli cloud env list` / `cli cloud functions list` |

## 云开发 — 上传与操作（CloudBase MCP）

云函数、数据库、存储、网关一律走 CloudBase MCP：

- 云函数上传：`manageFunctions(action="updateFunctionCode", functionName=..., functionRootPath=...)`——`functionRootPath` 为直接含函数文件夹的目录（如 `.../cloudfunctions`），不是项目根、不是函数子目录
- 云函数创建：`manageFunctions(action="createFunction")`；配置更新（timeout/memory/env）：`updateFunctionConfig`
- 函数详情 / 日志：`queryFunctions(action="getFunctionDetail" | "listFunctionLogs", functionName=...)`
- 数据库 / 存储 / 网关 / 环境：按场景用 `queryXxx`（读）与 `manageXxx`（写）；`queryEnv(action="info", envId=...)` 看 `RuntimeBackends` 决定后端选型
- 环境登录与绑定：`mcp__cloudbase__auth` 检查/绑定环境

### API Key 无网页授权部署

当用户明确要求使用 CloudBase MCP API Key 且不打开网站时，禁止启动 device/web OAuth，也不要把 API Key 写入仓库、配置文件、命令输出或最终回复。先确认 MCP 返回 `auth_mode=api_key`、`auth_status=READY`、目标完整 `EnvId` 已绑定，再部署。

优先使用 `manageFunctions(action="updateFunctionCode", functionName=..., functionRootPath=...)`。若因 `scf:GetTempCosInfo` 权限不足导致临时 COS 上传失败，仍保持 API Key 认证，按 [API Key 云函数部署参考](references/cloudbase-api-key-function-deploy.md) 改走 MCP `callCloudApi(service="scf", action="UpdateFunctionCode")` 直接提交 Base64 ZIP；不要擅自切换网页授权。

部署成功必须核对远端 `Active / Available`、`ModTime` 已更新、runtime/handler/timeout/memory 未意外变化。函数日志优先走 CLS `queryLogs(action="searchLogs")`；若 API Key 没有 `scf:InvokeFunction`，只报告远端冒烟测试缺口，不要把 CAM 调用失败误判为上传失败。

部署前检查（部署门禁）：
- **TCP 连库**（DATABASE_URL / MYSQL_HOST / MYSQL_* 等）→ 必须配真实 VPC + subnet，禁止编造 ID；原生 `app.database()` / `app.rdb()` 不需要 VPC
- **公网暴露** → 检查函数安全规则；匿名访问默认关闭
- **配置一致**：runtime / timeout / memorySize 与远程核对，避免覆盖远程配置
- **密钥安全**：API Key 若曾在聊天或日志中明文出现，交付时提醒轮换；任何示例只写占位符

## 云开发 — 编码规范（cloudbase 技能）

编写云函数 / 数据库 / 存储代码前，加载 `cloudbase` 技能按其规范执行：Event 函数 `exports.main(event, context)`、HTTP 函数监听 9000 并带 `scf_bootstrap`、原生 SDK 优先于 TCP、文档集合先建后用等。

## 边界

- 登录由用户自己完成，agent 只检查 `cli islogin`，不在终端代为登录
- `cli cloud functions deploy` 有 `EISDIR` 打包 bug → 云函数上传走 MCP
- API Key 无网页授权部署及权限降级路径见 [references/cloudbase-api-key-function-deploy.md](references/cloudbase-api-key-function-deploy.md)
- 运行 `cli` 会启动或连接开发者工具 IDE 服务（未打开时自启，`--port` 指定）
- `--project` 与 `--appid` 互斥：提供 `--project` 时 `--appid` 被忽略
- 官方文档：https://developers.weixin.qq.com/miniprogram/dev/devtools/cli.html
