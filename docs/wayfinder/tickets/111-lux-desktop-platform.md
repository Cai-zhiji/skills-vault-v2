# 增加 Lux Desktop 平台目标

- 状态：已决定
- 类型：Product / Architecture
- 阻塞：确定跨平台桌面交付方式
- 解锁：Lux Desktop 选择、预览、部署、恢复与状态展示

## Decision question

Skills Vault 如何在不改变现有 Codex / Claude Code 选择语义的前提下，把 Agent Skill 安全部署到 Lux Desktop？

## Resolution

- 把 Lux Desktop 加入正式平台集合；Catalog、Profile、选择状态、同步轨、详情和安装状态均展示 Lux。
- 保留旧值 `both` 的原义：只表示 Codex + Claude Code，不因新增平台而静默扩大部署范围。
- 新增 `all`、`lux`、`codex-lux`、`claude-lux`，从而表达三个平台的全部非空组合。
- Lux 使用规范用户目录 `~/.lux/skills/`：`SKILL.md` 映射为 `<name>.md`，Skill 目录映射为同名资源目录；可选 `SKILL.json` 或 `<name>.json` 映射为同名 watcher 配置。
- macOS/Linux 使用受管 symlink，Windows 使用受管复制；文件与目录分别记录来源和目标指纹，目标被用户修改时继续阻止覆盖或删除。
- 旧 Profile 在缺少平台声明时仍只对 Codex / Claude Code 生效；要覆盖 Lux 必须显式声明 `platform: lux` 或 `platforms`，重新保存 UI 选择后新增 `ui-lux` Profile。

## Specification

- [Skills Vault v2 产品规格](../../specs/skills-vault-v2.md)
- [跨平台桌面化需求](../../specs/cross-platform-desktop/requirements.md)
- [跨平台桌面化技术设计](../../specs/cross-platform-desktop/design.md)
