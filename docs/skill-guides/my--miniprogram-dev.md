# miniprogram-dev

> 微信小程序从开发到上线的完整工作流：小程序端预览/上传走开发者工具 `cli`，云开发上传与操作走 CloudBase MCP，编码规范回指 `cloudbase` 技能。

## 1. 一句话理解

`miniprogram-dev` 是一份**"工具分工"约定**：它把微信小程序开发里最容易混淆的两条通道——小程序端（开发者工具 CLI）和云开发（CloudBase MCP）——划清边界，并规定"每个命令的真实参数以 `-h` 自查为准"。

## 2. 它解决什么问题

小程序开发有两个独立的执行通道，用错就会撞墙：

- 小程序端的真机预览、体验版上传，只能走开发者工具 `cli`。
- 云函数/数据库/存储/网关，只能走 CloudBase MCP——因为 `cli cloud functions deploy` 在部分工具版本会触发 `EISDIR` 打包 bug（实测踩过），所以云函数上传**一律走 MCP，不用 cli**。

如果没这个 skill，agent 很可能去试 `cli cloud functions deploy` 然后卡在打包错误上，或者反过来试图用 MCP 做小程序预览。它的价值就是把这些"哪条路能走"事先钉死。

## 3. 核心心智模型

**CLI 是自描述的，`-h` 是唯一可信源。** 这贯穿整个 skill：不记命令参数，运行前一律 `cli <verb> -h` 自查（中文用 `cli <verb> --lang zh -h`）。

其次是一条**不可跨越的边界**：

| 环节 | 通道 |
| --- | --- |
| 小程序端预览 / 上传体验版 | 开发者工具 `cli` |
| 云函数上传 / 部署 / 配置 | CloudBase MCP（`manageFunctions` 等）|
| 云开发编码规范 | `cloudbase` 技能 |

登录也有明确分工：**登录由用户自己在开发者工具里扫码完成，agent 只 `cli islogin` 检查状态、等待，不在终端代为登录**。

## 4. 一次典型运转

一次"改完代码、上传体验版、顺带更新云函数"：

1. **定位 + 自查**：`cli -h` 确认命令；`cli islogin` 确认登录态（未登录等用户扫码）。
2. **小程序端上传**：`cli upload --project <含 project.config.json 的目录> -v 版本号 -d 备注`（`-v`、`-d` 必填），到公众平台「版本管理」核对。
3. **云函数上传**：`manageFunctions(action="updateFunctionCode", functionName=..., functionRootPath=...)`——`functionRootPath` 是直接含函数文件夹的目录，不是项目根、不是函数子目录。
4. **部署门禁自查**：TCP 连库必须配真实 VPC；公网暴露检查安全规则；核对 runtime/timeout/memory 没被意外覆盖。
5. **验证**：远端 `Active/Available`、`ModTime` 已更新；日志走 CLS `queryLogs`。

## 5. 何时用 / 何时不用

**用**：用户提到微信小程序开发、小程序命令行、`cli preview/upload`、云函数部署、云开发、CloudBase、微信云开发、CloudBase MCP API Key、不打开网站上传等。

**不用**：非小程序、非 CloudBase 的任务。云开发的**编码规范**（怎么写云函数/数据库/存储代码）不在本 skill，而在 `cloudbase` 技能——本 skill 只负责"通道"，`cloudbase` 负责"规范"。

## 6. 依赖与网络位置

- **依赖 `cloudbase`**：云开发编码规范回指它。
- 关联 `references/cloudbase-api-key-function-deploy.md`：API Key 无网页授权部署的降级路径。
- 与 `cloudbase` 是兄弟分工，不冲突。

## 7. 易错点与坑

- **`functionRootPath` 传错层级**：必须是 `.../cloudfunctions`（直接含函数文件夹），不是项目根、也不是 `.../cloudfunctions/hello`。
- **`cli cloud functions deploy` 会 `EISDIR`**：云函数上传别走 cli，走 MCP。
- **`--project` 与 `--appid` 互斥**：给了 `--project`，`--appid` 被忽略。
- **API Key 泄露**：API Key 不许写进仓库/配置/命令输出/最终回复；曾明文出现就提醒轮换。
- **`scf:GetTempCosInfo` 权限不足**：临时 COS 上传失败时，保持 API Key 认证，改走 `callCloudApi(service="scf", action="UpdateFunctionCode")` 提交 Base64 ZIP，别擅自切网页授权。
- **登录别代劳**：agent 只检查 `islogin`，扫码由用户自己做。

## 8. 出处

- 原始路径：`my-skills/miniprogram-dev/SKILL.md`
- 附属：`references/cloudbase-api-key-function-deploy.md`
- 官方参考：`https://developers.weixin.qq.com/miniprogram/dev/devtools/cli.html`
- 平台兼容：codex、claude（both）
