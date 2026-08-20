# wayfinder

> 把一份超出单个 agent 会话的大工作，规划成 issue tracker 上的一张共享"决策地图"，逐个解决决策 ticket，直到去往目的地的路清晰。

## 1. 一句话理解

`wayfinder` 处理的是**"大而模糊"**的工作：目的地看得见但路看不清，且一个会话装不下。它把这段路画成一张共享地图（一个 map issue + 一串决策 ticket），然后一次解决一个决策，直到"没有遗留的决定"——此时才交接给别人去做。

## 2. 它解决什么问题

超大会话的经典失败是**过早冲去做**——路线还没看清就动手，做一半发现方向错。`wayfinder` 反其道而行：默认**只规划、不执行**，把"做"的冲动当作"已经走到地图边缘、该交接了"的信号。

## 3. 核心心智模型

**地图 = 索引，不是仓库。** map 是单个 issue（标 `wayfinder:map`），列出已做决定（gist + 链接到持有细节的 ticket），每个决定只存在一个地方（它的 ticket）。map 结构五段：Destination / Notes / Decisions so far / Not yet specified / Out of scope。

**ticket 是"决策问题"，不是"构建切片"。** 每张 ticket 回答一个决策或调查，有四种类型：

- **Research**（AFK）：查文档/API，由 `research` 子 agent 解决。
- **Prototype**（HITL）：做个粗糙实物来反应。
- **Grilling**（HITL，默认）：`grilling` + `domain-modeling` 对话。
- **Task**（HITL/AFK）：决策前必须先完成的手工活（签约服务、搬数据），唯一"做"而非"决定"的类型，靠解锁决策来挣位置。

**战争迷雾（fog of war）**：地图故意不完整。看不清、挂在前置问题上的东西记在 `Not yet specified`，不硬拆成 ticket。**"迷雾还是 ticket"的判据**：你现在能精确陈述这个问题吗——能就建 ticket（哪怕被阻塞），不能就留在迷雾里。

**凭名引用，不凭编号。** 人读到的一切都用 ticket 的标题名，不用裸 `#42`。

**一个会话只解决一个 ticket**（research ticket 除外）。认领 = 先 assign 给自己，防止并发会话重复做。

## 4. 一次典型运转

**画图（一次会话）**：拷问定目的地 → 广度优先拷问前沿 → 建 map → 建能明确的 ticket（第二遍再接线阻塞边）→ 并行发 research 子 agent → 停。

**走图（每次一个 ticket）**：载入低清 map → 选下一个前沿 ticket（未阻塞、未认领）→ 认领 → 用 `## Notes` 指定的 skill 解决 → 记 resolution、关 ticket、在 Decisions so far 追加指针 → 把新可明确的迷雾升级成 ticket、把越过目的地的 ticket 判 out-of-scope。

## 5. 何时用 / 何时不用

**用**：工作量大到超过一个会话、且路径不清。

**不用**：一次会话能装下、路径已清晰（那不需要地图，直接做）。

## 6. 依赖与网络位置

- 依赖 `setup-matt-pocock-skills`（tracker 的 wayfinding 操作）。
- 内部用 `grilling`/`domain-modeling`/`research`/`prototype`。
- 终点交接给 `to-spec` → `to-tickets` → `implement`。

## 7. 易错点与坑

- **默认就去做**：wayfinder 默认只规划，产出"决定"而非"交付物"。
- **一次会话解决多个 ticket**：除 research 外，一次只一个。
- **把迷雾预切成 ticket 大小**：迷雾比 ticket 粗，一次升级可能变成多张或零张。
- **决策重复写在 map 和 ticket 两处**：决定只住一个地方（ticket），map 只 gist + link。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/wayfinder/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
