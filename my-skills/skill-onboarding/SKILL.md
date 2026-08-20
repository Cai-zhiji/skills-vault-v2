---
name: skill-onboarding
description: 在 Skills Vault v2 中登记或引入新 Skill，并一次完成 Skill 文件夹全部材料审阅、中文短说明、8 节中文说明文档、annotations/skills.yaml 注释、Catalog 扫描和结果校验。Use when a new upstream or personal Skill is added to the v2 project, when a Skill is missing its guide or Chinese summary, or when the Skill catalog needs to be refreshed after onboarding. Read every relevant file under the Skill folder, including SKILL.md, references, scripts, assets, and agents metadata. Do not use for editing an existing Skill's implementation rules only.
---

# Skill 入库与说明

将新 Skill 接入 v2 时，把“能被发现”与“人能看懂”作为同一个交付单元完成：先确认来源和 Catalog 身份，再审阅 Skill 文件夹中的全部材料，随后写短说明、深度说明和中文注释，最后重建索引并验证网站实际 API。

## 工作边界

- 只在用户明确要引入、登记、补齐说明或中文注释时执行。
- 不修改第三方 `sources/` 中的上游 `SKILL.md`，也不把中文说明塞进原始 Skill。
- 不手工编辑 `catalog/catalog.json` 或 `catalog/skills.md`；它们由 Catalog 扫描生成。
- 不覆盖已有说明或注释，除非用户明确要求重写；先报告已有内容和将要更新的字段。
- 个人 Skill 放在 `my-skills/<name>/`，第三方 Skill 必须已经存在于 `sources/` 并被 `registry.yaml` 纳入扫描。
- 不把“只读 `SKILL.md`”当作完成；Skill 文件夹内的脚本、参考资料、模板、资源和 Agent 元数据都会影响说明、依赖和风险判断。

## 标准工作流

### 1. 确认来源和入口

确认新 Skill 是第三方来源还是 `my-skills` 个人 Skill，并确认其目录、`SKILL.md` 和 frontmatter 存在。若第三方来源尚未注册，不要猜测 Catalog 条目；先完成来源接入或向用户报告缺少的来源信息。

运行一次 v2 Catalog 扫描，取得准确的 `id`、`name`、`path`、`source_commit`、平台兼容性和当前的 `summary_zh`。Skill ID 是后续所有文件映射的唯一依据：`source/name` 对应 `docs/skill-guides/source--name.md`。

### 2. 完整审阅 Skill 文件夹

先列出 Skill 文件夹下的全部文件，包含隐藏文件和嵌套目录：

```bash
rg --files <skill path> -uu | sort
```

然后按文件类型完整审阅：

- `SKILL.md`：读取 frontmatter 和正文，确认触发条件、流程、边界、依赖、平台限制、危险操作和相邻 Skill 路由。
- `references/`、模板和 Markdown/纯文本：逐个读完；不要只读目录名或引用文件的开头。
- `scripts/`：逐个读源码、命令行参数、输入输出、依赖和副作用；不要因为“说明文档不审计实现”而跳过脚本。除非用户要求执行，否则不运行有副作用的脚本。
- `agents/`、配置和元数据：读取并核对触发方式、UI 名称、平台声明、工具依赖与 `SKILL.md` 是否一致。
- `assets/` 和其他二进制材料：先列出文件和类型；图片用视觉工具检查，压缩包或不可直接阅读的文件检查目录/元数据，并在说明中记录其用途或无法审阅的限制。

审阅完成后，建立一份内部材料清单：每个文件如何支持 Skill、是否改变依赖/风险/输出判断、是否需要在 guide 中提及。任何无法读取的材料都要在最终回报中明确说明。

说明文档理解的是 Skill 的整体能力，而不是只翻译 `SKILL.md`；但不要把材料清单、函数扫描或文件夹地图原样塞进 guide。把材料带来的实际行为、工作流变化、依赖和坑重述到对应章节。

### 3. 生成中文短说明

在 `annotations/skills.yaml` 的 `skills` 下增加或更新对应 ID：

```yaml
"source/name": {
  "summary_zh": "一句话说清这个 Skill 解决什么问题，以及主要产出什么。"
}
```

短说明用于 v2 网站列表和详情弹窗，建议 25–80 个中文字符，优先写“动作 + 对象 + 结果”，不要翻译整段触发规则。例如：`在回答 Claude 使用问题后，匹配 Claude Academy 中真正相关的课程、教程或用例。`

### 4. 生成 8 节说明文档

写入 `docs/skill-guides/<source>--<name>.md`，严格使用下面 8 个二级标题，顺序固定、不多不少：

```text
## 1. 一句话理解
## 2. 它解决什么问题
## 3. 核心心智模型
## 4. 一次典型运转
## 5. 何时用 / 何时不用
## 6. 依赖与网络位置
## 7. 易错点与坑
## 8. 出处
```

中文优先，英文术语、命令、代码和 URL 保留原文。说明必须是重述而不是逐段翻译：第 3 节提炼一个能统摄全篇的关键比喻，第 4 节讲一遍端到端场景，第 5 节写清相邻 Skill 的边界。脚本、参考资料、资源或 Agent 元数据带来的关键行为要写入流程、依赖或坑，而不是单独堆成文件清单。没有实际依赖时，第 6 节可以简短说明“无额外依赖”。

第 8 节必须包含：

- 原始路径：`<catalog skill.path>/SKILL.md`
- 上游 commit：`<source_commit 前 7 位>`
- 平台兼容：从 Catalog 或 frontmatter 准确填写

### 5. 重建 Catalog

优先调用正在运行的 v2 服务：

```bash
curl -X POST http://127.0.0.1:8765/api/catalog/scan
```

没有服务时，在 v2 项目根目录执行等价的本地扫描命令：

```bash
PYTHONPATH=server python3 -m skills_vault.cli scan
```

扫描后确认 `catalog/catalog.json` 已包含新的 `summary_zh`、正确的 Skill ID 和更新后的 guide 计数。生成文件不要手工改写。

### 6. 验证网站可见性

至少检查以下两条 API：

```bash
curl http://127.0.0.1:8765/api/skills
curl http://127.0.0.1:8765/api/skills/<url-encoded-id>/guide
```

验收标准：

- Skill API 的 `summary_zh` 是中文短说明，且不再回退到英文 description。
- Guide API 返回 `exists: true`，路径是 `docs/skill-guides/<source>--<name>.md`。
- Guide 正文恰好包含 8 个规定的 `##` 标题。
- 第 8 节的 commit 前 7 位与 Catalog 一致。
- `catalog` 的 Skill 数量、说明文档数量和实际文件映射没有缺失或多余。

## 特殊情况

- **新建个人 Skill：** 先在 `my-skills/<name>/SKILL.md` 写好 frontmatter 和正文，再登记 `summary_zh`，扫描会把它加入 Catalog；不要把说明文档写进 Skill 目录。
- **第三方 Skill：** 先完整审阅来源 Skill 文件夹中的全部材料，再只在 v2 的 `annotations/skills.yaml` 和 `docs/skill-guides/` 添加本地维护内容；上游更新后重新检查全部材料、commit 和说明是否过期。
- **已有英文短说明：** 不改原始 `description`，补上 `summary_zh`，因为网站弹窗按 `summary_zh || description` 显示。
- **已有 guide：** 默认保留并先报告；只有用户要求刷新或上游内容变化时才重写，并同步更新出处 commit。
- **Catalog 落后：** 以本地文件和 annotations 为事实，重新扫描；不要用手工改 JSON 的方式掩盖落后状态。

## 完成回报

完成后简洁报告：新增/更新的 Skill ID、中文短说明、说明文档路径、扫描结果和验证结果。若网站服务未运行，说明文件已写入但 API 验证尚未执行，不要声称网页已经更新。
