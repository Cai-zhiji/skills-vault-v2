# 确定前端组件基础

- 状态：已决定
- 类型：Task

## Decision question

新网站使用什么前端基础？

## Resolution

使用 React 构建界面，shadcn/ui 提供可访问组件基础，Tailwind CSS 承载设计令牌、布局与状态样式。具体 React 构建方式由“选择运行时与进程边界”决定。

## Rationale

这是用户明确指定的技术方向。将组件原语与项目视觉令牌分离，既能复用 Dialog、Sheet、Command、Table 等交互，也避免页面停留在默认 shadcn 外观。
