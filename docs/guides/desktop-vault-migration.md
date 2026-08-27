# Vault 初始化与迁移指南

## 1. 没有 Skills 仓库：如何开始

首次打开桌面应用时选择“创建新 Vault”，确认保存位置并先查看 Preview。应用会创建空的 Vault 结构、受管 Profile 和 Catalog，不要求电脑已经安装 Git。

进入工作台后，在 Skills 页面选择“创建 Skill”，填写小写英文、数字或连字符组成的名称，以及用途说明。系统先展示将创建的目录、`SKILL.md` 模板和冲突结果；确认后才写入 `my-skills/<name>/` 并记录事务。

Git 是可选能力。没有 Git 时，原创、编辑、扫描、部署和备份仍可使用；需要版本历史或远程同步时，可稍后从依赖中心安装 Git，再自行决定是否初始化本地仓库。

## 2. 已经有 Skills 仓库：如何迁移

先根据原仓库类型选择入口：

- 如果目录包含 `vault.json`、`registry.yaml`、`profiles/` 和 `my-skills/`，选择“打开已有 Vault”，原地继续使用，不复制数据。
- 如果它是普通 Git 仓库或文件夹，里面包含一个或多个 `SKILL.md`，选择“导入 Skills 文件夹”。系统只读扫描 Skill 数量、无效项、嵌套项和名称冲突，再创建新 Vault 并把已确认的 Skill 复制到 `my-skills/`。
- 如果希望保留第三方仓库身份和独立更新边界，可在进入 Vault 后从来源页把它添加为 `local-copy` 或 Git 来源；需要编辑时再派生到“我的 Skills”。

导入不会修改或删除原仓库。发生目标重名、无效 Skill 或写入失败时，操作会停止或回滚，不会用新内容覆盖已有文件。

## 3. 当前使用 Web v2：如何迁移

在首次启动页选择“迁移旧版 Web Vault”：

1. 选择当前 Web v2 项目目录作为读取位置。
2. 选择一个新的空目录作为桌面 Vault。
3. 查看 Preview 中的 Skill 数量、事实数据、来源和历史记录。
4. 确认后等待复制与 Catalog 重建完成。

迁移会复制 `registry.yaml`、`lock.yaml`、`profiles/`、`annotations/`、`my-skills/`、说明文档和 `sources/`，并把可解释的旧事务、备份和更新报告归档为 legacy history。活动 Catalog、端口/PID、日志、Preview token 和旧平台安装状态不会直接复制。

旧 Web 项目始终保持不变，可作为回滚副本。迁移完成后，需要在桌面应用中重新生成一次平台部署 Preview，再确认把 Codex / Claude Code / Lux Desktop 的受管目标指向新 Vault。

## 失败与恢复

- Preview 阶段不写文件，可随时返回修改路径。
- 新建或导入失败时，新目标会清理到操作前状态；原始目录保持不变。
- 如果“上次使用的 Vault”被移动，应用会回到首次启动页，请用“打开已有 Vault”重新选择。
- 外部 Git、Node 或 Skills CLI 缺失时，应用仍能启动；相关来源操作会明确提示受影响能力和安装方式。
