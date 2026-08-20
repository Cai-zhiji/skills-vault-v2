# 确认信息架构与页面模型

- 状态：被阻塞
- 类型：Prototype
- 阻塞：定义 v2 首发产品边界
- 解锁：首个 UI 纵向切片

## Decision question

Skills、来源、记录、设置和说明文档应如何分布在页面、详情侧栏、Dialog 与命令入口中？

## Starting hypothesis

- 一级区域：Skills、来源、记录。
- 单对象详情：右侧 Sheet。
- 危险或批量确认：Dialog。
- 长耗时操作：持续 Operation Rail。
- 常用导航与安全动作：全局 Command。

## Prototype questions

- 同步轨应常驻右侧、主内容顶部还是按上下文变化？
- Skill 选择适合表格内联、批量模式还是详情动作？
- 窄屏时如何保持操作状态可见但不挤压列表？

## Resolution

待产品边界确定后，通过低保真交互原型解决。
