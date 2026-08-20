# CloudBase MCP API Key 云函数部署

用于用户明确要求“使用 MCP API Key 上传、不打开网站”的场景。只通过 CloudBase MCP 操作，不启动浏览器、设备码或网页 OAuth。

## 1. 安全与认证门禁

1. 不在仓库、MCP 配置、脚本、shell 历史、日志或回复中保存/复述 API Key。
2. 通过 CloudBase MCP `auth(action="login_by_api_key", apiKey=..., apiKeyEnvId=...)` 登录；优先让工具安全输入通道接收密钥。
3. 调用 `auth(action="status")`，必须确认：
   - `auth_mode` 为 `api_key`
   - `auth_status` 与环境状态为 `READY`
   - `current_env_id` 是目标完整 EnvId
4. 用户要求不打开网站时，禁止调用 `start_auth`，也不得因上传失败自行切换 device/web 登录。
5. 若 API Key 已在聊天或日志中明文出现，完成任务后提醒用户轮换；不要在提醒中复述密钥。

## 2. 上传前检查

1. 用 `queryEnv(action="info", envId=...)` 确认环境正常与地域。
2. 用 `queryFunctions(action="getFunctionDetail", functionName=...)` 记录远端：
   - `Namespace`、`Runtime`、`Handler`
   - `Timeout`、`MemorySize`
   - `Status`、`AvailableStatus`、`ModTime`
3. 完成本地测试、语法检查和 CloudBase code review。
4. 仅更新代码时不要传配置更新字段，避免覆盖远端配置。

## 3. 首选上传路径

调用：

```text
manageFunctions(
  action="updateFunctionCode",
  functionName="<function-name>",
  functionRootPath="/absolute/path/to/cloudfunctions"
)
```

`functionRootPath` 必须是直接包含各函数文件夹的父目录，不能是项目根目录，也不能指向具体函数子目录。

## 4. 临时 COS 权限不足时直传 ZIP

若首选路径返回缺少 `scf:GetTempCosInfo`，说明高层工具的临时 COS 打包通道无权使用，不等于 `UpdateFunctionCode` 本身无权执行。保持 API Key 认证，改用 CloudBase MCP 的通用云 API 通道。

### 4.1 生成代码包

- ZIP 根目录直接包含 `index.js`、`package.json`、业务目录等，不能再嵌套一层函数名目录。
- 排除无关文件；若远端 `InstallDependency=TRUE`，通常不打包 `node_modules`。
- 将 ZIP 内容编码为 Base64；直传大小须符合腾讯云当前限制，执行前核对官方文档。
- 不把 Base64 内容打印到输出；错误日志可能回显参数，限制工具输出长度。

### 4.2 MCP 直传

先检查 CloudBase MCP 的 `callCloudApi` schema，再调用：

```text
callCloudApi(
  service="scf",
  action="UpdateFunctionCode",
  params={
    FunctionName: "<function-name>",
    Namespace: "<function-namespace>",
    Handler: "<existing-handler>",
    ZipFile: "<base64-zip>",
    InstallDependency: "TRUE|FALSE",
    CodeSource: "ZipFile",
    Publish: "FALSE"
  }
)
```

关键约束：

- `Namespace` 使用函数详情返回的真实值。
- `Namespace` 与 `EnvId` 互斥，不能同时传入；已有函数优先使用详情中的 `Namespace`。
- 保持原 `Handler` 与 `InstallDependency` 设置。
- 仅代码更新使用 `Publish="FALSE"`，除非用户明确要求发布版本。
- 若 MCP 高层 `zipFile` 参数出现本地路径解析错误（如 `paths[0]` 未定义），不要继续重复同一路径，改用上述 `callCloudApi`。
- 官方参数以腾讯云 [UpdateFunctionCode](https://cloud.tencent.com/document/api/583/18581) 最新文档为准。

## 5. 部署后核验

1. 轮询 `queryFunctions(action="getFunctionDetail")`，确认：
   - `Status=Active`
   - `AvailableStatus=Available`
   - `ModTime` 晚于部署前
   - Runtime、Handler、Timeout、MemorySize 等配置未意外改变
2. 日志：优先用 `queryLogs(action="searchLogs", service="tcb", ...)` 查询部署后的时间范围。旧的 `listFunctionLogs` 若提示底层接口下线，不再重试。
3. 冒烟测试：权限允许时调用 `manageFunctions(action="invokeFunction", ...)`，优先测试公开只读接口。
4. 若返回 `Cam authentication failed`，检查是否缺少 `scf:InvokeFunction`。这表示远端验证权限不足，不代表代码上传失败；以 `UpdateFunctionCode` 请求成功和函数状态/更新时间为上传依据。
5. 删除本地临时代码包，不删除或覆盖用户项目文件。

## 6. 权限诊断与停止条件

常见权限按需检查：

- 高层临时 COS 上传：`scf:GetTempCosInfo`
- 代码更新：`scf:UpdateFunctionCode`
- 详情查询：`scf:GetFunction`
- 远端调用：`scf:InvokeFunction`
- 日志验证：对应 CLS 查询权限

同一路径失败 2–3 次后停止重复尝试，依据明确错误切换到权限模型、API 通道或报告阻塞。不得用网页授权规避用户明确指定的 API Key 流程。
