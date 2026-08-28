# 用 Lux Neo 替换 Lux 平台目标

- 状态：已决定
- 类型：Product / Architecture
- 阻塞：确定跨平台桌面交付方式
- 解锁：Lux Neo 选择、预览、部署、迁移、恢复与状态展示

## Decision question

Skills Vault 如何在不改变现有 Codex / Claude Code 选择语义的前提下，把原 `lux` 平台直接迁移为个人使用的 Lux Neo？

## Resolution

- 逻辑平台键继续使用 `lux`，但产品与部署语义直接替换为 Lux Neo；不保留 Lux Desktop 目标，也不新增 `lux-neo` 平台键。
- 保留旧值 `both` 的原义：只表示 Codex + Claude Code。
- Lux Neo 只提供 `lux`（仅 Lux Neo）模式；删除 `all`、`codex-lux`、`claude-lux`，不提供 Lux Neo 与其他平台的组合。
- Lux Neo 使用 `$LUX_HOME/skills/`，默认根目录为 `~/.lux_neo`：`SKILL.md` 映射为 `<name>.md`，Skill 目录映射为同名资源目录；可选 `SKILL.json` 或 `<name>.json` 映射为同名 watcher 配置。
- macOS/Linux 使用受管 symlink，Windows 使用受管复制；文件与目录分别记录来源和目标指纹，目标被用户修改时继续阻止覆盖或删除。
- 迁移时只临时识别 install-state 中由 Skills Vault 纳管的 `~/.lux/skills` 旧路径，用于备份和精确移除；新 install-state 只记录 Lux Neo 路径，不重新暴露旧目标。
- 旧 Profile 在缺少平台声明时仍只对 Codex / Claude Code 生效；Lux Neo 必须显式声明 `platform: lux`，重新保存 UI 选择后写入 `ui-lux` Profile。

## Specification

- [Skills Vault v2 产品规格](../../specs/skills-vault-v2.md)
- [跨平台桌面化需求](../../specs/cross-platform-desktop/requirements.md)
- [跨平台桌面化技术设计](../../specs/cross-platform-desktop/design.md)
