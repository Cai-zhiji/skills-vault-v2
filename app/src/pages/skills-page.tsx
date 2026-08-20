import { useEffect, useMemo, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowRight,
  Boxes,
  FilePlus2,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react"
import { useSearchParams } from "react-router-dom"

import { SkillDetailSheet } from "@/components/skill-detail-sheet"
import { StatusPill } from "@/components/status-pill"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import { truncate } from "@/lib/format"
import { useOperation } from "@/lib/operation-context"
import { selectionKey } from "@/lib/selection"
import { cn } from "@/lib/utils"
import type {
  ApplyResponse,
  CreateOriginalResponse,
  InstallPreview,
  ScanResult,
  SelectionMode,
  SelectionPayload,
  SkillsPayload,
  StatusPayload,
} from "@/types/api"

const modeLabels: Record<SelectionMode, string> = {
  off: "关闭",
  both: "两端启用",
  codex: "仅 Codex",
  claude: "仅 Claude",
}

export function SkillsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState("")
  const [source, setSource] = useState("all")
  const [classification, setClassification] = useState("all")
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null)
  const [draft, setDraft] = useState<Record<string, SelectionMode>>({})
  const [installPreview, setInstallPreview] = useState<InstallPreview | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState("")
  const [newDescription, setNewDescription] = useState("")
  const initializedSelection = useRef(false)
  const handledAction = useRef(false)
  const queryClient = useQueryClient()
  const { runOperation, operation } = useOperation()

  const skillsQuery = useQuery({
    queryKey: ["skills"],
    queryFn: () => api.get<SkillsPayload>("/api/skills"),
  })
  const selectionQuery = useQuery({
    queryKey: ["selection"],
    queryFn: () => api.get<SelectionPayload>("/api/selection"),
  })
  const statusQuery = useQuery({
    queryKey: ["status"],
    queryFn: () => api.get<StatusPayload>("/api/status"),
  })

  useEffect(() => {
    if (selectionQuery.data && !initializedSelection.current) {
      setDraft(selectionQuery.data.selections)
      initializedSelection.current = true
    }
  }, [selectionQuery.data])

  const refreshAll = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["skills"] }),
      queryClient.invalidateQueries({ queryKey: ["selection"] }),
      queryClient.invalidateQueries({ queryKey: ["status"] }),
      queryClient.invalidateQueries({ queryKey: ["transactions"] }),
    ])
  }

  const scan = async () => {
    const result = await runOperation(
      "catalog.scan",
      "扫描本地 Skills",
      "读取来源与个人 Skills，重建 Catalog",
      () => api.post<ScanResult>("/api/catalog/scan"),
      (value) =>
        `扫描完成：新增 ${value.added.length}、变化 ${value.changed.length}、移除 ${value.removed.length}`,
    )
    if (result) await refreshAll()
  }

  useEffect(() => {
    if (searchParams.get("action") === "scan" && !handledAction.current) {
      handledAction.current = true
      setSearchParams({}, { replace: true })
      void scan()
    }
  })

  const filteredSkills = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return (skillsQuery.data?.skills || []).filter((skill) => {
      if (source !== "all" && skill.source_id !== source) return false
      if (classification !== "all" && skill.classification !== classification)
        return false
      if (!needle) return true
      return [
        skill.id,
        skill.name,
        skill.description,
        skill.summary_zh || "",
        skill.source_id,
      ]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    })
  }, [classification, search, skillsQuery.data?.skills, source])

  const sources = useMemo(
    () =>
      Array.from(
        new Set((skillsQuery.data?.skills || []).map((skill) => skill.source_id)),
      ).sort(),
    [skillsQuery.data?.skills],
  )
  const classifications = useMemo(
    () =>
      Array.from(
        new Set(
          (skillsQuery.data?.skills || []).map((skill) => skill.classification),
        ),
      ).sort(),
    [skillsQuery.data?.skills],
  )

  const savedSelection = useMemo(
    () => selectionQuery.data?.selections || {},
    [selectionQuery.data?.selections],
  )
  const hasDraftChanges = selectionKey(draft) !== selectionKey(savedSelection)
  const changedCount = useMemo(() => {
    const ids = new Set([...Object.keys(draft), ...Object.keys(savedSelection)])
    return Array.from(ids).filter(
      (id) => (draft[id] || "off") !== (savedSelection[id] || "off"),
    ).length
  }, [draft, savedSelection])

  const updateMode = (skillId: string, mode: SelectionMode) => {
    setDraft((current) => ({ ...current, [skillId]: mode }))
  }

  const saveSelection = async () => {
    const result = await runOperation(
      "selection.save",
      "保存启用选择",
      "校验平台兼容与同名冲突",
      () =>
        api.post<SelectionPayload>("/api/selection", {
          selections: draft,
        }),
      () => `已保存 ${changedCount} 项选择变化；尚未修改平台链接`,
    )
    if (result) {
      initializedSelection.current = false
      await refreshAll()
    }
  }

  const previewInstall = async () => {
    const result = await runOperation(
      "install.preview",
      "生成安装 Preview",
      "比较选择与 Codex / Claude Code 的实际链接",
      () =>
        api.post<InstallPreview>("/api/install/preview", {
          profiles: selectionQuery.data?.active_profiles || [],
        }),
      (value) =>
        `Preview：新增 ${value.changes.added.length}、移除 ${value.changes.removed.length}、替换 ${value.changes.changed.length}`,
    )
    if (result) setInstallPreview(result)
  }

  const applyInstall = async () => {
    if (!installPreview) return
    const result = await runOperation(
      "install.apply",
      "同步平台 Skills",
      "备份现有状态并应用 Preview",
      () =>
        api.post<ApplyResponse>("/api/install/apply", {
          preview_token: installPreview.preview_token,
          reset: false,
        }),
      (value) => `平台同步完成；事务 ${value.transaction_id}`,
    )
    if (result) {
      setInstallPreview(null)
      await refreshAll()
    }
  }

  const createOriginal = async () => {
    if (!newName.trim()) return
    const result = await runOperation(
      "skill.original",
      "创建原创 Skill",
      "创建目录与 SKILL.md，并重建 Catalog",
      () =>
        api.post<CreateOriginalResponse>("/api/skills/original", {
          name: newName.trim(),
          description: newDescription.trim(),
        }),
      () => `已创建 my/${newName.trim()}`,
    )
    if (result) {
      setCreateOpen(false)
      setNewName("")
      setNewDescription("")
      await refreshAll()
      setSelectedSkillId(result.skill_id)
    }
  }

  const catalogState = statusQuery.data?.catalog_state
  const scanning = operation.key === "catalog.scan" && operation.state === "running"

  return (
    <div className="page-stack">
      {catalogState && !catalogState.fresh && (
        <section className="attention-strip">
          <div className="flex min-w-0 items-start gap-3">
            <RefreshCw className="mt-0.5 size-4 shrink-0 text-[var(--copper)]" />
            <div>
              <p className="text-sm font-medium">Catalog 落后于本地文件</p>
              <p className="mt-1 text-xs text-muted-foreground">
                新增 {catalogState.added.length}、变化 {catalogState.changed.length}、缺失 {catalogState.missing.length}。扫描只重建索引，不修改 Skill 内容。
              </p>
            </div>
          </div>
          <Button onClick={() => void scan()} disabled={scanning}>
            <RefreshCw className={cn(scanning && "animate-spin")} />
            扫描本地 Skills
          </Button>
        </section>
      )}

      <section className="toolbar-panel">
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="搜索 Skills"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="搜索名称、说明或来源"
            className="pl-9"
          />
        </div>
        <Select value={source} onValueChange={(value) => setSource(value || "all")}>
          <SelectTrigger className="w-[150px]">
            <Filter />
            <SelectValue placeholder="全部来源" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部来源</SelectItem>
            {sources.map((item) => (
              <SelectItem key={item} value={item}>
                {item}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={classification}
          onValueChange={(value) => setClassification(value || "all")}
        >
          <SelectTrigger className="w-[150px]">
            <SlidersHorizontal />
            <SelectValue placeholder="全部分类" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部分类</SelectItem>
            {classifications.map((item) => (
              <SelectItem key={item} value={item}>
                {item}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={() => setCreateOpen(true)}>
          <FilePlus2 /> 创建 Skill
        </Button>
        <Button variant="outline" onClick={() => void scan()} disabled={scanning}>
          <RefreshCw className={cn(scanning && "animate-spin")} /> 扫描
        </Button>
      </section>

      <section className="catalog-panel" aria-label="Skills 目录">
        <div className="catalog-header">
          <div>
            <p className="eyebrow">CATALOG ENTRIES</p>
            <p className="mt-1 text-xs text-muted-foreground">
              显示 {filteredSkills.length} / {skillsQuery.data?.total || 0}
            </p>
          </div>
          <div className="hidden items-center gap-6 text-[10px] text-muted-foreground md:flex">
            <span>来源 / 分类</span>
            <span>启用范围</span>
          </div>
        </div>

        {skillsQuery.isLoading ? (
          <div className="space-y-px bg-border">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="bg-surface p-4">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="mt-2 h-3 w-3/4" />
              </div>
            ))}
          </div>
        ) : filteredSkills.length ? (
          <div className="skill-list">
            {filteredSkills.map((skill) => {
              const mode = draft[skill.id] || "off"
              const platforms = new Set(skill.compatibility.platforms)
              const hasConflict = Boolean(
                selectionQuery.data?.conflicts[skill.name.toLowerCase()],
              )
              return (
                <article className="skill-row" key={skill.id}>
                  <button
                    type="button"
                    className="skill-row-main"
                    onClick={() => setSelectedSkillId(skill.id)}
                  >
                    <div className="skill-glyph" aria-hidden="true">
                      {skill.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="font-medium text-foreground">{skill.name}</h2>
                        {skill.source_id === "my" && (
                          <StatusPill status="safe">个人</StatusPill>
                        )}
                        {hasConflict && <StatusPill status="warning">同名冲突</StatusPill>}
                        {skill.risk_signals.length > 0 && (
                          <StatusPill status="muted">
                            {skill.risk_signals.length} risk
                          </StatusPill>
                        )}
                      </div>
                      <p className="mt-1.5 text-xs leading-5 text-muted-foreground">
                        {truncate(skill.summary_zh || skill.description || "暂无说明")}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-3 font-data text-[10px] text-muted-foreground">
                        <span>{skill.source_id}</span>
                        <span>{skill.classification}</span>
                        <span>{skill.invocation.codex}</span>
                      </div>
                    </div>
                  </button>
                  <div className="skill-row-control">
                    <Select
                      value={mode}
                      onValueChange={(value) =>
                        updateMode(skill.id, (value || "off") as SelectionMode)
                      }
                    >
                      <SelectTrigger
                        className={cn(
                          "w-[132px]",
                          mode !== "off" && "selection-active",
                        )}
                        aria-label={`设置 ${skill.name} 启用范围`}
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="off">{modeLabels.off}</SelectItem>
                        {platforms.has("codex") && platforms.has("claude") && (
                          <SelectItem value="both">{modeLabels.both}</SelectItem>
                        )}
                        {platforms.has("codex") && (
                          <SelectItem value="codex">{modeLabels.codex}</SelectItem>
                        )}
                        {platforms.has("claude") && (
                          <SelectItem value="claude">{modeLabels.claude}</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`查看 ${skill.name} 详情`}
                      onClick={() => setSelectedSkillId(skill.id)}
                    >
                      <ArrowRight />
                    </Button>
                  </div>
                </article>
              )
            })}
          </div>
        ) : (
          <div className="empty-state">
            <Boxes />
            <h2>没有匹配的 Skills</h2>
            <p>调整搜索或筛选；如果刚加入本地目录，请先扫描。</p>
            <Button variant="outline" onClick={() => void scan()}>
              <RefreshCw /> 扫描本地 Skills
            </Button>
          </div>
        )}
      </section>

      <div className={cn("selection-dock", hasDraftChanges && "selection-dock-visible")}>
        <div>
          <p className="text-sm font-medium">{changedCount} 项选择尚未保存</p>
          <p className="mt-1 text-[11px] text-muted-foreground">
            保存只更新配置；随后生成安装 Preview 才会修改平台链接。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            onClick={() => setDraft(selectionQuery.data?.selections || {})}
          >
            放弃变化
          </Button>
          <Button onClick={() => void saveSelection()}>
            <ShieldCheck /> 保存选择
          </Button>
        </div>
      </div>

      {!hasDraftChanges && selectionQuery.data && (
        <div className="install-corner-action">
          <Button variant="outline" onClick={() => void previewInstall()}>
            <Sparkles /> 预览平台同步
          </Button>
        </div>
      )}

      <SkillDetailSheet
        skillId={selectedSkillId}
        onOpenChange={(open) => !open && setSelectedSkillId(null)}
      />

      <AlertDialog
        open={Boolean(installPreview)}
        onOpenChange={(open) => !open && setInstallPreview(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-label text-2xl">
              应用平台同步
            </AlertDialogTitle>
            <AlertDialogDescription>
              应用前会创建备份。只管理由 Skills Vault 记录的链接，不清理 `.system`、plugins、hooks 或 settings。
            </AlertDialogDescription>
          </AlertDialogHeader>
          {installPreview && (
            <div className="preview-grid">
              <div><strong>{installPreview.changes.added.length}</strong><span>新增</span></div>
              <div><strong>{installPreview.changes.removed.length}</strong><span>移除</span></div>
              <div><strong>{installPreview.changes.changed.length}</strong><span>替换</span></div>
              <div><strong>{installPreview.changes.kept.length}</strong><span>保留</span></div>
            </div>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={() => void applyInstall()}>
              应用同步
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-label text-2xl">创建原创 Skill</DialogTitle>
            <DialogDescription>
              在当前 Vault 的 `my-skills` 中创建最小 SKILL.md，并立即加入 Catalog。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="new-skill-name" className="text-xs font-medium">
                名称
              </label>
              <Input
                id="new-skill-name"
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder="my-new-skill"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="new-skill-description" className="text-xs font-medium">
                一句话说明
              </label>
              <Textarea
                id="new-skill-description"
                value={newDescription}
                onChange={(event) => setNewDescription(event.target.value)}
                placeholder="这个 Skill 解决什么问题…"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              取消
            </Button>
            <Button onClick={() => void createOriginal()} disabled={!newName.trim()}>
              <FilePlus2 /> 创建并扫描
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
