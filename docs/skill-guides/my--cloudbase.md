# cloudbase

> 腾讯云开发（CloudBase / TCB）的全栈开发总入口：把 Web、小程序、App 对接数据库、云函数、云托管、云存储、认证、内置大模型这一整套能力，用一套路由规则组织起来。

## 1. 一句话理解

`cloudbase` 不是"教你怎么写某一段代码"，而是一个**带强制路由的工程规范**。它先判断你的场景（登录？小程序？数据库？云函数？大模型？），再指定"该先读哪个子技能、绝不该先读哪个"，然后逼你在写前端代码之前先用 MCP 把后端资源（认证、表、存储、安全规则）备好。它真正的产物是"纪律"，不是代码片段。

## 2. 它解决什么问题

CloudBase 的能力面极宽：三种数据库（NoSQL 文档库、MySQL、PostgreSQL）、云函数、云托管、云存储、认证、内置大模型、巡检、Spec 流程…… 一个人（或 agent）面对一个需求时，最贵的不是不会写，而是**走错路**：

- 用 Web SDK 的思维去写小程序（`wx.cloud` 不是 Web auth）
- 该用 `app.rdb()`/PostgreSQL 时退回 MySQL 或 NoSQL
- 大模型调用报错，改了半天代码，其实是没买 Token Credits / 成长计划
- 登录失败，补了一堆前端代码，其实是 provider 没启用

`cloudbase` 用一个稳定的 `activation-map`（激活地图）把"场景 → 该读什么"固化成一张表，让这些系统性错误在动手前就被拦住。

## 3. 核心心智模型

**路由表（activation map）是唯一事实源。** 整个 skill 的逻辑是一条链：

```
识别场景 → 读对应子技能（先读谁、别先读谁）→ 资源准备（MCP 先于代码）→ 写代码 → 自查 → 收尾
```

几个反复出现的底层约定：

- **资源先于代码（Engineering Constitution）**：后端资源通过 MCP 备好之后才允许写前端。这是硬约束，不是建议。
- **稳定 skill id 路由**：路由用 `auth-web-cloudbase`、`ai-model-web` 这种稳定 id，而不是自然语言。这样生成产物、安装、跨来源都能对得上号。
- **`EnvId` 必须显式**：不许依赖 CLI 隐式选中的环境；别名/昵称要先 `envQuery(aliasExact=true)` 解析成完整 `EnvId` 再传。
- **2–3 次失败即换路**：同一条路径失败 2–3 次，停下重新路由（平台 / runtime / auth 域 / 权限模型 / SDK 边界），而不是继续硬试。
- **能力边界清晰**：`ai.createModel()` 的 `GroupName` 只能是 `"cloudbase"` / `"hunyuan-exp"` / `"custom-<name>"`，模型 id 放进 `generateText` 的 `model` 字段——这是最高频的调用错误点。

## 4. 一次典型运转

以"做一个带登录的 Web 应用 + 文档数据库 + 大模型对话"为例，它不会让你直接开写：

1. **路由**：登录场景 → 先读 `auth-tool-cloudbase`（不是 `cloud-functions`）；数据库 → `cloudbase-document-database-web-sdk`；大模型 → 先跑"资格检查"（`DescribeActivityInfo` 成长计划 + `DescribeEnvPostpayPackage` Token Credits）。
2. **备资源**：用 MCP 启用登录 provider、拿到 publishable key、建好集合、配好安全规则、确认存储域名。
3. **写代码**：前端接 `@cloudbase/js-sdk`，用 `auth.getSession()`（不是废弃的 `getLoginState()`）做登录态判断。
4. **自查**：`tsc`/lint/build 静态过一遍，再用 agent-browser 走用户可见流程；没跑通的层要明说。
5. **收尾**：跑 `cloudbase-code-review`，修错，声明完成。

## 5. 何时用 / 何时不用

**用**：任何 CloudBase 项目的开发、设计、构建、部署、调试、迁移、排障——Web、小程序、uni-app、原生 App（iOS/Android/Flutter/RN）、云函数、云托管、内置/第三方大模型、巡检、Spec。

**不用**：
- 非 CloudBase 项目
- 纯前端、不接 CloudBase 的页面
- 自托管后端（没有 CloudBase）

`miniprogram-dev` 是它的兄弟技能：小程序端"预览/上传"走开发者工具 `cli` 的那部分在 `miniprogram-dev`，云开发的**编码规范**又回指到 `cloudbase`。

## 6. 依赖与网络位置

- 被 `miniprogram-dev` 依赖（云开发编码规范）。
- 自身是"总入口"，把大量子技能作为 `references/` 挂在下面：`auth-web-cloudbase`、`auth-wechat-miniprogram`、`cloud-functions`、`ai-model-web/nodejs/wechat`、`postgresql-development-cloudbase`、`relational-database-mcp-cloudbase`、`ui-design`、`ops-inspector`、`spec-workflow`、`cloudrun-development`、`cloudbase-agent` 等。
- 硬依赖 CloudBase MCP（管理/部署必需，`npx plugins add TencentCloudBase/cloudbase-plugin`）。
- 与 `miniprogram-dev` 分工，不冲突；与 `academic`/`anthropic`/`mattpocock` 无直接关系。

## 7. 易错点与坑

- **`GroupName` 传错**：`ai.createModel("deepseek")` 是错的，模型 id 要放 `generateText({ model })`，`GroupName` 填 `"cloudbase"` 等三选一。
- **把对象直接写进文件**：MCP 返回是对象，写文件要 `JSON.stringify(result, null, 2)`，别拿原始对象重试。
- **别名当 EnvId 传**：昵称/别名不能直接喂给 `auth.set_env` 或 SDK init，必须先解析。
- **`manageHosting` vs `manageApps`**：首次前端部署必须 `manageApps(action="createApp")`，`manageHosting` 只用于老项目增量更新。
- **大模型报错先查配额**：Token Credits / 成长计划没配好时，改代码是白费。

## 8. 出处

- 原始路径：`my-skills/cloudbase/SKILL.md`（版本 `2.25.6`）
- 附属：`references/activation-map.yaml`（路由契约源头）、`mcp-setup.md`、`deployment-workflow.md`、`console-links.md`、`scenarios.md` 及一批 `references/<skill-id>/SKILL.md`
- 平台兼容：codex、claude（both）
