# session-end

## 1. 一句话理解

这是一个把一次 agent 会话的现实状态、领域词汇、历史日志和代码变更一起封存成可交接提交的项目收尾仪式。

## 2. 它解决什么问题

会话结束时，代码可能已经改变，但项目文档仍停在旧状态；下一位 agent 只能从零猜测做了什么、为什么这样做、接下来先做什么。若把历史写进状态文件，状态又会越来越混乱。`session-end` 用一次固定收尾把“现在是什么”“这次发生了什么”“下次做什么”分开记录，并将文档与代码放进同一个本地 commit，形成渐进式增长的交接线索。

## 3. 核心心智模型

**STATUS 是现在，CONTEXT 是词汇，devlog 是历史。** 三者不是同一份日志的不同名字：`docs/STATUS.md` 应始终描述当前现实；`CONTEXT.md` 只吸收本次新出现或被澄清的领域概念；`docs/devlog/` 则一篇篇追加，记录这次会话发生过什么。把时间维度分开，下一位 agent 才能先读现状，再按需追溯历史，而不会被旧任务污染。

会话是 devlog 的单位，commit 仍可以在会话中途多次产生；本 skill 的 commit 是最后的收口，而不是把整个 git 历史误压成一次提交。

## 4. 一次典型运转

会话结束时先打开 `docs/STATUS.md`，把已完成工作移入 done，标明仍在进行的内容，重写下一步，并补充新学到的栈、环境或决策约束。然后检查 `CONTEXT.md`：只有出现新领域词汇或概念澄清才增补，不能趁机塞进实现细节。

接着按 `templates/devlog.md` 新建一篇 `docs/devlog/YYYY-MM-DD-<slug>.md`，五个小节全部填充；确实没有内容的小节写“无”。历史文件只增不改。最后把代码与文档一起提交，默认消息为 `chore: 会话结束，更新文档与日志`（或能概括主题的同类消息），确认 `git log` 可见，且不向任何远程仓库 push。

## 5. 何时用 / 何时不用

**适合用：** 一个连续 agent 会话完成、暂停或准备交接时；尤其是代码、文档、决策或状态发生变化，需要让下一个 agent 冷启动即可继续时。

**不要用：** 会话仍在进行、只完成了一次小改动但还没有收尾、或用户只要求查看状态/写一条临时日志时。中途独立功能仍可正常单独 commit；不要把每次 commit 都当成一次 session-end。若只是项目首次建立骨架，应使用 `new-project`。

## 6. 依赖与网络位置

- 依赖现有的 `docs/STATUS.md`、`CONTEXT.md`、`docs/devlog/` 目录和 `templates/devlog.md`；依赖本地 git，不依赖网络。
- 与 `new-project` 是互补生命周期 skill：前者创建入口、词汇和初始状态，后者持续维护并记录每次会话。
- 该 skill 必须显式调用（Codex `$session-end`、Claude Code `/session-end`），兼容 Codex、Claude。

## 7. 易错点与坑

- 把历史塞回 STATUS，导致它不再反映“当前现实”；旧事件应进入 devlog。
- 修改旧 devlog 来“纠正”过去；devlog 只增不改，新的理解应写入新的条目或当前 STATUS。
- 没有新术语也改写 CONTEXT，或把实现细节写进 glossary；无变化就不动。
- 忘记给 devlog 的五个小节填内容，空白处应明确写“无”。
- 只提交文档不提交代码，或反过来提交代码不提交文档；收尾 commit 应让两者成为同一个可追溯单元。
- 把 commit 当成远程同步，执行 push；本 skill 的边界是本地 git only、永不 push。

## 8. 出处

- 原始路径：`my-skills/session-end/SKILL.md`
- 上游 commit：`51f963c`
- 平台兼容：Codex、Claude（Claude Code 支持 `disable-model-invocation` 扩展）

