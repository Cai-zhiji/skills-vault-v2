# 确定网站主入口

- 状态：已决定
- 类型：Grilling

## Decision question

Skills Vault v2 的主要使用入口是什么？

## Resolution

网站是浏览、管理、同步和维护 Skills 的主要入口。CLI 保留启动本地服务、诊断、自动化和应急维护能力，但不要求日常用户记忆多组命令。

## Rationale

这是用户明确提出的重构目标，也能把现有分散在 CLI、静态网页与操作菜单中的主流程收敛到同一上下文。
