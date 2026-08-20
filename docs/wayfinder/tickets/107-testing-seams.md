# 确定测试接缝与验收矩阵

- 状态：被阻塞
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

待前置票据完成后研究。
