# skill-onboarding

## 1. 一句话理解

这是 v2 项目的 Skill 入库流水线：把新 Skill 的完整材料审阅、中文短说明、8 节深度说明、注释登记、Catalog 重建和网站验收连成一次可追踪交付。

## 2. 它解决什么问题

引入 Skill 如果只把目录放进仓库，机器能找到它，用户却仍会看到英文长 description、缺少中文上下文，网站也可能没有说明文档；只读 `SKILL.md` 还会漏掉脚本参数、参考资料、模板、资源和 UI 元数据。若说明、注释和索引分别手工处理，又容易漏掉 commit、文件映射或 API 刷新。这个 skill 解决的是“新 Skill 已存在，但还没有成为 v2 中可理解、可浏览、可验证的完整条目”的问题。

## 3. 核心心智模型

**入库不是复制文件，而是建立三条对齐链：** 原始 Skill 负责真实能力，`annotations/skills.yaml` 负责面向人的中文短说明，`docs/skill-guides/` 负责可阅读的深度理解；Catalog 把三者与 `id`、来源 commit 和平台信息连接起来，网站 API 则是最终可见性验收点。

其中 `source/name` 是唯一主键。只要主键一致，短说明、深度文档和扫描后的 Catalog 就能落到同一个网站条目；任何一步绕过主键或直接编辑生成 JSON，都可能造成“文件在，但页面找不到”的假成功。

## 4. 一次典型运转

用户把新的第三方 Skill 接入 `sources/`，或在 `my-skills/` 创建个人 Skill 后，先确认目录、`SKILL.md`、frontmatter 和来源注册都完整，再扫描 v2 Catalog，取得准确的 ID、路径、commit 和兼容平台。列出 Skill 文件夹下的全部材料并逐个审阅：完整阅读 `SKILL.md`，读完 `references/` 和模板，读脚本源码与参数，核对 `agents/` 元数据，并检查图片、压缩包等资源的类型和用途。从全部材料中提炼触发边界、核心概念、典型流程、依赖和坑。

随后在 `annotations/skills.yaml` 为同一个 ID 写一条 25–80 字符左右的中文 `summary_zh`，再把整体材料重述成 `docs/skill-guides/<source>--<name>.md` 的固定 8 节说明。完成后通过 v2 服务的 `POST /api/catalog/scan`，或本地 CLI 扫描重建索引；最后分别请求 Skill API 和 guide API，确认短说明已不再回退到英文、guide 存在、commit 一致、文件数量和 ID 映射完整。

第三方 Skill 的本地说明只写入 annotations 和 docs，不改上游 `SKILL.md`；个人 Skill 也不把 guide 放进 Skill 目录。已有说明默认保留，只有用户明确要求刷新或上游变化时才重写。

## 5. 何时用 / 何时不用

**适合用：** v2 引入新的上游或个人 Skill；为已有 Skill 补中文短说明、8 节 guide；上游更新后需要核对 commit 并刷新 Catalog；网站显示英文或“尚未创建”时排查入库链路。

**不要用：** 只想修改某个 Skill 的执行规则或脚本实现；只想重写一篇已有 guide 而不涉及入库登记；只做 Catalog 查询而不改变 Skill 的可见性。前者应直接维护对应 Skill，后者可使用 `skill-guide-writer` 或普通文档编辑流程。

## 6. 依赖与网络位置

- 依赖 v2 的 `registry.yaml`、`annotations/skills.yaml`、`catalog/catalog.json`、`docs/skill-guides/` 和源 Skill 的 `SKILL.md`。
- 通过 `POST /api/catalog/scan` 或 `PYTHONPATH=server python3 -m skills_vault.cli scan` 重建 Catalog；网站实际读取 `/api/skills/<id>` 和 `/api/skills/<id>/guide`。
- 与 `skill-guide-writer` 分工互补：后者专注说明文档内容，本 skill 负责把说明、中文注释和索引一起接入 v2。
- 本项目中的路径是 `my-skills/skill-onboarding`，通过 `agents/openai.yaml` 提供 UI 名称和 `$skill-onboarding` 默认调用提示；兼容 Codex、Claude。

## 7. 易错点与坑

- 只把新目录放进 `sources/`，忘记注册来源或扫描 Catalog，导致网站看不到 Skill。
- 只读 `SKILL.md`，跳过 `scripts/`、`references/`、`agents/` 或资源文件，导致说明漏掉真实流程、依赖、输出或风险。
- 只写 guide，不写 `summary_zh`，弹窗仍会回退到原始英文 description。
- 手工改 `catalog/catalog.json` 试图修复页面；生成索引应从 annotations 和源文件重新扫描。
- 用文件名猜 ID，尤其在同名冲突场景下漏掉 source 前缀；必须以 Catalog 的完整 `id` 为准。
- 说明文档只读 description，不读完整材料，结果会遗漏边界、依赖和风险；说明应吸收材料的实际影响，但不照搬文件清单。
- 把中文注释写进第三方上游文件，造成来源仓库脏改动；本地中文维护内容应留在 v2。
- API 服务未运行却声称网站已更新；没有服务时只能报告文件和本地扫描结果，不能伪造可见性验证。

## 8. 出处

- 原始路径：`my-skills/skill-onboarding/SKILL.md`
- 上游 commit：`51f963c`
- 平台兼容：Codex、Claude（含 `agents/openai.yaml` UI 元数据）
