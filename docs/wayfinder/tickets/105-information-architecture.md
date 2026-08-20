# 确认信息架构与页面模型

- 状态：已决定
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

- 一级路由固定为 Skills、来源、记录，桌面使用左侧导航，窄屏使用顶部切换。
- Skill、来源和事务详情使用右侧 Sheet；危险或批量应用使用 AlertDialog/Dialog。
- 同步轨在桌面常驻右栏，窄屏折叠到内容顶部；点击节点只切换上下文，不直接执行写操作。
- Skills 使用紧凑语义列表与内联启用范围控件；选择变更集中在底部保存条。
- 全局 Command 提供页面导航、Skill 搜索和安全动作入口。
- 长操作使用 Operation Rail 持续显示；toast 只报告无需处理的短成功。
