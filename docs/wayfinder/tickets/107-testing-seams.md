# 确定测试接缝与验收矩阵

- 状态：已决定
- 类型：Research
- 阻塞：确定安全事务与权限边界、选择运行时与进程边界
- 解锁：实现任务拆分与完成定义

## Decision question

哪个最小稳定接缝能够同时验证文件/Git 安全、API 契约和用户主流程？

## Candidate seams

- 领域应用服务：使用临时 Vault 目录与真实 Git fixture。
- HTTP API：验证资源、preview/apply 与错误契约。
- 浏览器：只验证用户可见编排、焦点和防重复提交。

## Required matrix

- 正常、空、运行中、成功、阻塞、失败和过期状态。
- 桌面、窄屏、键盘、减少动态效果。
- 用户数据保持、原子回滚和恢复预览。

## Resolution

使用三个接缝：

1. Python 领域/API：临时 Vault fixture 验证 Catalog 状态、扫描、更新分类、token 与路径安全。
2. TypeScript：Vitest + Testing Library 验证状态映射、筛选、选择草稿和错误呈现。
3. 浏览器：Playwright 或真实浏览器烟测三条一级路由、详情、筛选、异步反馈与响应式布局。

领域安全由 Python 测试负责，浏览器测试不复制文件/Git 断言。
