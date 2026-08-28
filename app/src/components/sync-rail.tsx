import { Bot, Check, FileCode2, Library, TriangleAlert } from "lucide-react"

import { StatusPill, type SemanticStatus } from "@/components/status-pill"
import { Skeleton } from "@/components/ui/skeleton"
import type { SelectionPayload, StatusPayload } from "@/types/api"

interface SyncNode {
  id: string
  label: string
  meta: string
  status: SemanticStatus
  stateLabel: string
  icon: typeof FileCode2
}

export function SyncRail({
  status,
  selection,
  loading,
}: {
  status?: StatusPayload
  selection?: SelectionPayload
  loading: boolean
}) {
  if (loading || !status) {
    return (
      <div className="space-y-4 p-4">
        <Skeleton className="h-5 w-28" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  const catalogFresh = status.catalog_state.fresh
  const hasConflicts = status.catalog.conflict_groups > 0
  const codexCount = selection?.resolved.codex.effective.length || 0
  const claudeCount = selection?.resolved.claude.effective.length || 0
  const luxCount = selection?.resolved.lux.effective.length || 0
  const nodes: SyncNode[] = [
    {
      id: "files",
      label: "本地文件",
      meta: `${status.catalog_state.personal_skills} 个个人 Skills`,
      status: catalogFresh ? "safe" : "warning",
      stateLabel: catalogFresh ? "已读取" : "有新变化",
      icon: FileCode2,
    },
    {
      id: "catalog",
      label: "Catalog",
      meta: `${status.catalog.skills} 个 Skills`,
      status: hasConflicts ? "warning" : "safe",
      stateLabel: hasConflicts
        ? `${status.catalog.conflict_groups} 组冲突`
        : "可用",
      icon: Library,
    },
    {
      id: "codex",
      label: "Codex",
      meta: `${codexCount} 个应启用`,
      status: "safe",
      stateLabel: "已选择",
      icon: Bot,
    },
    {
      id: "claude",
      label: "Claude Code",
      meta: `${claudeCount} 个应启用`,
      status: "safe",
      stateLabel: "已选择",
      icon: Bot,
    },
    {
      id: "lux",
      label: "Lux Neo",
      meta: `${luxCount} 个应启用`,
      status: "safe",
      stateLabel: "已选择",
      icon: Bot,
    },
  ]

  return (
    <section className="p-4" aria-labelledby="sync-rail-title">
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <p className="eyebrow">REPOSITORY SIGNAL</p>
          <h2 id="sync-rail-title" className="mt-1 font-label text-lg">
            同步轨
          </h2>
        </div>
        <span className="font-data text-[10px] text-muted-foreground">
          {status.generated_at ? "CATALOG ONLINE" : "NO CATALOG"}
        </span>
      </div>

      <div className="sync-track">
        {nodes.map((node, index) => {
          const Icon = node.icon
          const isBranch = index >= 2
          return (
            <div
              className={`sync-node sync-node-${node.id} ${isBranch ? "sync-node-branch" : ""}`}
              key={node.id}
            >
              <div className="sync-node-icon">
                <Icon className="size-4" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">{node.label}</span>
                  <StatusPill status={node.status}>{node.stateLabel}</StatusPill>
                </div>
                <p className="mt-1 truncate font-data text-[10px] text-muted-foreground">
                  {node.meta}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-5 border border-border bg-background/55 p-3">
        <div className="flex items-center gap-2 text-xs font-medium">
          {catalogFresh ? (
            <Check className="size-3.5 text-[var(--safe)]" />
          ) : (
            <TriangleAlert className="size-3.5 text-[var(--copper)]" />
          )}
          {catalogFresh ? "本地目录已进入 Catalog" : "先扫描，再同步平台"}
        </div>
        <p className="mt-2 text-[11px] leading-5 text-muted-foreground">
          已管理 {status.managed_links} 个平台链接。选择与实际安装分开保存，应用前会生成明确 Preview。
        </p>
      </div>
    </section>
  )
}
