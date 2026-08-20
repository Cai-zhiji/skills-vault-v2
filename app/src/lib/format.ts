export function shortHash(value: string | null | undefined): string {
  return value ? value.slice(0, 8) : "—"
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

export function truncate(value: string, length = 120): string {
  if (value.length <= length) return value
  return `${value.slice(0, length).trimEnd()}…`
}

export function operationLabel(operation: string): string {
  const labels: Record<string, string> = {
    "catalog.scan": "扫描 Catalog",
    install: "同步平台 Skills",
    update: "更新来源",
    "source.policy": "修改来源状态",
    "source.delete": "删除来源",
    "source.git.add": "添加 Git 来源",
    "source.skills-cli.add": "添加 Skills 来源",
    restore: "恢复备份",
    "selection.save": "保存选择",
    "profile.save": "保存 Profile",
    "skill.delete": "删除 Skill",
  }
  return labels[operation] || operation
}
