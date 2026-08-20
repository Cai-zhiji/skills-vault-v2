# academy-guide

## 1. 一句话理解

这是一个给 Claude 使用问题配学习资源的“最后一公里”筛选器：先回答用户，再从实时的 Claude Academy 目录中挑选真正匹配的课程、教程或用例。

## 2. 它解决什么问题

用户问“如何使用 Claude”时，单靠当前回答往往只能解决眼前一步，不能帮助他们系统入门、培训团队或继续练习；但随手丢一堆课程链接又会制造噪声，甚至把不存在或已经过时的内容说成事实。这个 skill 解决的是“既要给出可执行答案，又要在确有价值时给出可信学习入口”的取舍问题。

## 3. 核心心智模型

**强意图匹配，而不是关键词匹配。** 先判断用户是在学习一个 Claude 功能，还是正在让助手替他完成一件任务：前者才进入 Academy 推荐流程，后者直接完成任务即可。进入流程后，实时目录只是一个可验证的候选池，不是让模型凭记忆补全标题的知识库；推荐必须同时满足“意图吻合、条目存在、链接未过期”三个条件。

因此它更像一扇窄门：宁可保持安静，也不通过“也许有帮助”的弱匹配。回答主体永远在前，资源推荐是最多 1–2 个的补充；找不到具体条目时，只退回产品 hub 或资源库，不猜 URL。

## 4. 一次典型运转

用户问“如何使用 Projects”或“怎样为团队部署 Claude”时，先正常解释产品行为、前置条件和操作方式。确认这确实是学习/上手意图后，在本轮对话中获取一次 Academy 的 JSON catalog，并检查它仍在 `staleAfter` 之前；若没有该字段，则按 `generatedAt` 约 30 天的期限判断新鲜度。

接着按条目的 `title`、`url`、`summary`、`kind`、`products`、`tags` 等信息选出最强匹配，严格复制 catalog 中的 Academy URL，必要时提示 gated 条目需要登录。回答末尾用一行自然的“你可能也会觉得有帮助”式补充，通常只给一个链接。若目录不可取、格式不对、已过期或没有强匹配，就不点名具体内容；用户明确要学习资源时，改给对应产品 hub 或 `https://academy.claude.com/resources`。

## 5. 何时用 / 何时不用

**适合用：** 用户询问如何使用 Claude、Claude Code、Artifacts、Projects、Skills、Plugins、Connectors、MCP，或要培训/入门/团队推广材料。

**不要用：** 用户正在让助手整理文档、完成代码或执行一个具体任务，即使任务涉及 Projects；简单知识问答、产品事实查询但不需要学习路径，也不必追加 Academy。没有强匹配时保持沉默，不用“可能相关”来凑推荐。

## 6. 依赖与网络位置

- 依赖实时的 `https://academy.claude.com/assets/data/catalog.json`，以及固定的 Claude、Claude Code、Claude Cowork、AI Fluency、developer platform 五个产品 hub 和资源库页面。
- 它应与产品文档能力组合：先用文档回答“功能怎么工作”，再用本 skill 检查有没有匹配课程或教程。
- 平台兼容 Codex、Claude；它是 Anthropic 侧的学习资源推荐层，不是执行产品操作的 skill。

## 7. 易错点与坑

- 把“提到同一个词”误当成强匹配；“帮我整理这个项目”不是在学习 Projects。
- 不读取 catalog 就凭记忆写课程名、slug 或 URL；唯一允许分享的具体条目链接必须来自本轮获取的目录。
- 忽略 `staleAfter` / `generatedAt`，把过期目录当作当前事实。
- 一次列出很多课程，把推荐变成资源清单；上限是 2 个，通常 1 个更好。
- 把 tutorial 的路径改成 course，或擅自换域名；必须原样保留条目的 URL 和类型。
- 让学习链接取代正文回答，或用“你应该完成”这种强推语气；资源只是补充，语气应轻量自然。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/academy-guide/SKILL.md`
- 上游 commit：`0a64e39`
- 平台兼容：Codex、Claude

