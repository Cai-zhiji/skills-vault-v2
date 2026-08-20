# 确定 API 与异步操作契约

- 状态：已决定
- 类型：Research
- 阻塞：定义 v2 首发产品边界、选择运行时与进程边界、制定旧项目数据迁移方案、确定安全事务与权限边界
- 解锁：前后端实现任务拆分

## Decision question

前端以什么稳定契约读取资源、启动操作、接收进度、处理过期预览和呈现可恢复错误？

## Topics

- 资源与命令式操作的 URL/类型边界。
- 统一错误对象和用户可执行建议。
- Operation ID、阶段进度、轮询或事件流。
- 请求取消、前端单例锁和服务端幂等性。
- Catalog 新鲜度与平台安装状态的组合查询。

## Resolution

保留旧版 JSON API 的兼容端点，并新增：

- `GET /api/catalog/state`：返回个人 Skill 的 `fresh / added / changed / missing`。
- `POST /api/catalog/scan`：返回扫描前后的新增、变化、移除与冲突摘要。
- `GET /api/health`：返回应用版本、数据目录与构建可用性。

错误统一为 `{ code, error, details }`。前端每种写操作使用 operation key 防重复；Preview 响应携带 token，Apply 只接受 token。更新预览额外返回 `actionable_source_ids` 与 `blocked_source_ids`，Apply 只消费可执行行。

首版操作耗时通过客户端 Operation Rail 的阶段模型表达；不增加事件流。若真实操作时间继续增长，再升级为 Operation ID + 轮询。
