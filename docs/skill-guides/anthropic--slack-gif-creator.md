# slack-gif-creator

> 制作面向 Slack 优化的动图 GIF：尺寸/帧率/颜色约束、校验工具、动画概念。

## 1. 一句话理解

`slack-gif-creator` 提供**做 Slack GIF 的知识 + 工具**：Slack 的尺寸/帧率/颜色/时长约束，一个 `GIFBuilder` 生成器，以及动画概念。

## 2. 它解决什么问题

Slack 对 GIF 有体积和尺寸约束（emoji GIF 128×128、消息 GIF 480×480、帧率 10–30、颜色 48–128、emoji GIF 3 秒内）。做出来的 GIF 要能塞进 Slack 且不超限。本 skill 把约束和优化工具封装好。

## 3. 核心心智模型

**约束 + 生成器。** Slack 要求：emoji GIF 128×128、消息 GIF 480×480；FPS 10–30（越低越小）、颜色 48–128（越少越小）、emoji GIF 时长 <3 秒。

核心流程：`GIFBuilder(width, height, fps)` 建 builder → 用 PIL 逐帧画 → `add_frame` → 带优化保存。

## 4. 一次典型运转

建 builder → 生成帧（PIL 画圆/多边形/线）→ add_frame → 优化保存。

## 5. 何时用 / 何时不用

**用**：用户要"给 Slack 做个 X 做 Y 的 GIF"。

**不用**：非 Slack 用途的 GIF。

## 6. 依赖与网络位置

- 依赖 PIL + `core/gif_builder.py`。
- 是 `anthropic` 来源的工具技能。

## 7. 易错点与坑

- **尺寸/帧率/颜色超限**：Slack 有硬约束，别做 1080p 高帧 GIF。
- **emoji GIF 太长**：3 秒内。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/slack-gif-creator/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
