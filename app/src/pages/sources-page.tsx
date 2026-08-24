import { useEffect, useMemo, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleOff,
  GitBranch,
  GitPullRequestArrow,
  Link2,
  PackageCheck,
  Plus,
  RefreshCw,
  ShieldCheck,
} from "lucide-react"
import { useSearchParams } from "react-router-dom"

import { StatusPill } from "@/components/status-pill"
import { QueryErrorState } from "@/components/query-state"
import { QueryEmptyState } from "@/components/query-state"
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { api } from "@/lib/api"
import { formatDate, shortHash } from "@/lib/format"
import { useOperation } from "@/lib/operation-context"
import { cn } from "@/lib/utils"
import type {
  ApplyResponse,
  DependenciesPayload,
  DependencyInstallPreview,
  PreviewTokenResponse,
  SourceAddPreview,
  SourceRow,
  UpdatePreview,
  UpdateSourceRow,
} from "@/types/api"

interface SourcePolicyPreview extends PreviewTokenResponse {
  source_id: string
  action: string
  changed: boolean
  skill_count: number
  target_enabled: boolean
  notes: string[]
}

function updateStatus(row: UpdateSourceRow | undefined, source: SourceRow) {
  if (row) {
    if (row.status === "blocked-dirty")
      return { status: "fault" as const, label: "本地改动阻塞" }
    if (row.status === "fast-forward")
      return { status: "warning" as const, label: "可安全更新" }
    if (row.status === "self-managed")
      return { status: "warning" as const, label: "由 Skills CLI 更新" }
    if (["diverged", "missing", "missing-remote-ref"].includes(row.status))
      return { status: "fault" as const, label: row.status }
    return { status: "safe" as const, label: "已是最新" }
  }
  if (!source.exists) return { status: "fault" as const, label: "目录缺失" }
  if (source.dirty) return { status: "warning" as const, label: "有本地改动" }
  return { status: "safe" as const, label: "健康" }
}

export function SourcesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [updatePreview, setUpdatePreview] = useState<UpdatePreview | null>(null)
  const [selectedSource, setSelectedSource] = useState<SourceRow | null>(null)
  const [policyPreview, setPolicyPreview] = useState<SourcePolicyPreview | null>(null)
  const [addOpen, setAddOpen] = useState(false)
  const [addKind, setAddKind] = useState<"git" | "skills-cli">("git")
  const [sourceInput, setSourceInput] = useState("")
  const [branch, setBranch] = useState("main")
  const [addPreview, setAddPreview] = useState<SourceAddPreview | null>(null)
  const [dependenciesOpen, setDependenciesOpen] = useState(false)
  const [dependencyPreview, setDependencyPreview] = useState<DependencyInstallPreview | null>(null)
  const handledAction = useRef(false)
  const queryClient = useQueryClient()
  const { runOperation, operation } = useOperation()

  const sourcesQuery = useQuery({
    queryKey: ["sources"],
    queryFn: () => api.get<SourceRow[]>("/api/sources"),
  })
  const dependenciesQuery = useQuery({
    queryKey: ["dependencies"],
    queryFn: () => api.get<DependenciesPayload>("/api/dependencies"),
  })

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["sources"] }),
      queryClient.invalidateQueries({ queryKey: ["status"] }),
      queryClient.invalidateQueries({ queryKey: ["skills"] }),
      queryClient.invalidateQueries({ queryKey: ["selection"] }),
      queryClient.invalidateQueries({ queryKey: ["transactions"] }),
      queryClient.invalidateQueries({ queryKey: ["dependencies"] }),
    ])
  }

  const refreshDependencies = async () => {
    const result = await runOperation(
      "dependencies.refresh",
      "重新检测依赖",
      "离线检查 Git、Node、npm 与 npx",
      () => api.post<DependenciesPayload>("/api/dependencies/refresh"),
      (value) => `依赖检测完成：${value.platform} / ${value.architecture}`,
    )
    if (result) queryClient.setQueryData(["dependencies"], result)
  }

  const previewDependencyInstall = async (dependency: "git" | "node") => {
    const result = await runOperation(
      "dependency.install.preview",
      "预览依赖安装",
      "检查可信安装提供者、命令与权限影响",
      () =>
        api.post<DependencyInstallPreview>("/api/dependencies/install/preview", {
          dependency,
        }),
      (value) => `${value.label} 安装 Preview 已生成`,
    )
    if (result) setDependencyPreview(result)
  }

  const applyDependencyInstall = async () => {
    if (!dependencyPreview) return
    if (!dependencyPreview.can_execute) {
      window.open(dependencyPreview.official_url, "_blank", "noopener,noreferrer")
      setDependencyPreview(null)
      return
    }
    const result = await runOperation(
      "dependency.install.apply",
      `安装 ${dependencyPreview.label}`,
      `通过 ${dependencyPreview.provider} 执行已确认命令`,
      () =>
        api.post<ApplyResponse>("/api/dependencies/install/apply", {
          preview_token: dependencyPreview.preview_token,
        }),
      () => `${dependencyPreview.label} 安装命令已完成`,
    )
    if (result) {
      setDependencyPreview(null)
      await refreshDependencies()
    }
  }

  const checkUpdates = async () => {
    const result = await runOperation(
      "updates.check",
      "检查来源更新",
      "获取远端引用并分类安全与阻塞来源",
      () => api.post<UpdatePreview>("/api/updates/check"),
      (value) =>
        `检查完成：${value.actionable_source_ids.length} 个可应用，${value.blocked_source_ids.length} 个被阻塞`,
    )
    if (result) setUpdatePreview(result)
  }

  useEffect(() => {
    if (searchParams.get("action") === "updates" && !handledAction.current) {
      handledAction.current = true
      setSearchParams({}, { replace: true })
      void checkUpdates()
    }
  })

  const applyUpdates = async () => {
    if (!updatePreview) return
    const result = await runOperation(
      "updates.apply",
      "应用安全来源更新",
      "只更新 Preview 中可执行的来源，并在失败时回滚",
      () =>
        api.post<ApplyResponse>("/api/updates/apply", {
          preview_token: updatePreview.preview_token,
        }),
      (value) => `更新完成；事务 ${value.transaction_id}`,
    )
    if (result) {
      setUpdatePreview(null)
      await refresh()
    }
  }

  const previewPolicy = async (source: SourceRow) => {
    const result = await runOperation(
      "source.policy.preview",
      source.enabled ? "预览停用来源" : "预览启用来源",
      "计算受影响 Skills、平台选择与链接",
      () =>
        api.post<SourcePolicyPreview>("/api/sources/policy/preview", {
          source_id: source.id,
          enabled: !source.enabled,
        }),
      (value) => `Preview：${value.skill_count} 个 Skills 受影响`,
    )
    if (result) setPolicyPreview(result)
  }

  const applyPolicy = async () => {
    if (!policyPreview) return
    const result = await runOperation(
      "source.policy.apply",
      policyPreview.target_enabled ? "启用来源" : "停用来源",
      "先备份，再同步来源策略与平台链接",
      () =>
        api.post<ApplyResponse>("/api/sources/policy/apply", {
          preview_token: policyPreview.preview_token,
        }),
      () => `${policyPreview.source_id} 已${policyPreview.target_enabled ? "启用" : "停用"}`,
    )
    if (result) {
      setPolicyPreview(null)
      await refresh()
    }
  }

  const previewAdd = async () => {
    const endpoint =
      addKind === "git"
        ? "/api/sources/git/preview"
        : "/api/sources/skills-cli/preview"
    const result = await runOperation(
      "source.add.preview",
      "检查新来源",
      "验证地址并发现可用 Skills",
      () =>
        api.post<SourceAddPreview>(endpoint, {
          input: sourceInput.trim(),
          branch,
          full_depth: false,
        }),
      (value) => `已发现来源 ${value.source_id}`,
    )
    if (result) setAddPreview(result)
  }

  const applyAdd = async () => {
    if (!addPreview) return
    const endpoint =
      addKind === "git" ? "/api/sources/git/apply" : "/api/sources/skills-cli/apply"
    const result = await runOperation(
      "source.add.apply",
      "添加来源",
      "安装到 Vault 专用目录并重建 Catalog",
      () =>
        api.post<ApplyResponse>(endpoint, {
          preview_token: addPreview.preview_token,
        }),
      () => addPreview.action === "merge"
        ? `已向 ${addPreview.source_id} 追加 Skill`
        : addPreview.action === "unchanged"
          ? `${addPreview.source_id} 已是最新`
          : `来源 ${addPreview.source_id} 已添加`,
    )
    if (result) {
      setAddPreview(null)
      setAddOpen(false)
      setSourceInput("")
      await refresh()
    }
  }

  const updateBySource = useMemo(
    () =>
      new Map((updatePreview?.sources || []).map((row) => [row.source_id, row])),
    [updatePreview],
  )
  const checking = operation.key === "updates.check" && operation.state === "running"
  const dependencies = dependenciesQuery.data?.dependencies || []
  const dependencyById = new Map(dependencies.map((row) => [row.id, row]))
  const selectedDependency = addKind === "git" ? dependencyById.get("git") : dependencyById.get("npx")
  const sourceDependencyReady = selectedDependency?.status === "available" || selectedDependency?.status === "unverified"

  return (
    <div className="page-stack">
      {sourcesQuery.isError || dependenciesQuery.isError ? <QueryErrorState message="来源或依赖状态暂时无法读取" onRetry={() => { void queryClient.invalidateQueries({ queryKey: ["sources"] }); void queryClient.invalidateQueries({ queryKey: ["dependencies"] }) }} /> : null}
      <section className="source-summary-band">
        <div>
          <p className="eyebrow">SOURCE CONTROL</p>
          <h2 className="mt-2 font-label text-2xl tracking-wide">
            {sourcesQuery.data?.length || 0} 个受管来源
          </h2>
          <p className="mt-2 max-w-xl text-xs leading-5 text-muted-foreground">
            更新检查会保留脏来源并只应用安全集合；系统不会自动清理、stash、commit 或覆盖本地文件。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setDependenciesOpen(true)}>
            <PackageCheck /> 依赖中心
          </Button>
          <Button variant="outline" onClick={() => setAddOpen(true)}>
            <Plus /> 添加来源
          </Button>
          <Button onClick={() => void checkUpdates()} disabled={checking}>
            <RefreshCw className={cn(checking && "animate-spin")} /> 检查更新
          </Button>
        </div>
      </section>

      {updatePreview && (
        <section className="update-overview">
          <div>
            <p className="text-sm font-medium">更新检查已完成</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {updatePreview.actionable_source_ids.length} 个可执行；{updatePreview.blocked_source_ids.length} 个阻塞来源不会进入 Apply。
            </p>
          </div>
          <Button
            onClick={() => void applyUpdates()}
            disabled={!updatePreview.actionable_source_ids.length}
          >
            <GitPullRequestArrow /> 应用安全更新
          </Button>
        </section>
      )}

      <section className="sources-grid">
        {sourcesQuery.data?.length ? sourcesQuery.data.map((source) => {
          const updateRow = updateBySource.get(source.id)
          const health = updateStatus(updateRow, source)
          return (
            <article className="source-card" key={source.id}>
              <div className="source-card-topline" />
              <div className="flex items-start justify-between gap-4">
                <div className="source-icon">
                  {source.kind === "git" ? <GitBranch /> : <Link2 />}
                </div>
                <StatusPill status={health.status}>{health.label}</StatusPill>
              </div>
              <div className="mt-6">
                <div className="flex items-center gap-2">
                  <h2 className="font-label text-xl tracking-wide">{source.id}</h2>
                  {!source.enabled && <StatusPill status="muted">已停用</StatusPill>}
                </div>
                <p className="mt-1 truncate font-data text-[10px] text-muted-foreground">
                  {source.url}
                </p>
              </div>
              <dl className="source-metrics">
                <div><dt>Revision</dt><dd>{shortHash(source.commit)}</dd></div>
                <div><dt>Trust</dt><dd>{source.trust}</dd></div>
                <div><dt>Policy</dt><dd>{source.update_policy}</dd></div>
              </dl>
              {source.dirty_files.length > 0 && (
                <div className="source-warning">
                  <AlertTriangle />
                  <div>
                    <p>{source.dirty_files.length} 个本地变化</p>
                    <p>{source.dirty_files[0]}</p>
                  </div>
                </div>
              )}
              <div className="mt-auto flex items-center justify-between gap-2 pt-5">
                <Button variant="ghost" onClick={() => void previewPolicy(source)}>
                  {source.enabled ? <CircleOff /> : <CheckCircle2 />}
                  {source.enabled ? "停用" : "启用"}
                </Button>
                <Button variant="outline" onClick={() => setSelectedSource(source)}>
                  查看详情 <ArrowRight />
                </Button>
              </div>
            </article>
          )
        }) : <QueryEmptyState title="还没有受管来源" description="可以添加 Git、Skills CLI 或本地来源，然后重新扫描 Catalog。" action={<Button onClick={() => setAddOpen(true)}><Plus />添加来源</Button>} />}
      </section>

      <Sheet
        open={Boolean(selectedSource)}
        onOpenChange={(open) => !open && setSelectedSource(null)}
      >
        <SheetContent className="w-full p-0 sm:max-w-[520px]">
          {selectedSource && (
            <>
              <SheetHeader className="detail-sheet-header">
                <StatusPill status={selectedSource.dirty ? "warning" : "safe"}>
                  {selectedSource.dirty ? "本地改动" : "工作树干净"}
                </StatusPill>
                <SheetTitle className="mt-4 font-label text-3xl tracking-wide">
                  {selectedSource.id}
                </SheetTitle>
                <SheetDescription>{selectedSource.url}</SheetDescription>
              </SheetHeader>
              <div className="space-y-5 p-5">
                <dl className="detail-list">
                  <div className="detail-row"><dt>类型</dt><dd>{selectedSource.kind}</dd></div>
                  <div className="detail-row"><dt>路径</dt><dd><code className="break-all">{selectedSource.path}</code></dd></div>
                  <div className="detail-row"><dt>Commit</dt><dd><code>{selectedSource.commit || "—"}</code></dd></div>
                  <div className="detail-row"><dt>Locked</dt><dd><code>{selectedSource.locked || "—"}</code></dd></div>
                  <div className="detail-row"><dt>最近变化</dt><dd>{formatDate(selectedSource.head_modified_at)}</dd></div>
                  <div className="detail-row"><dt>License</dt><dd>{selectedSource.license}</dd></div>
                </dl>
                {selectedSource.dirty_files.length > 0 && (
                  <section className="detail-section">
                    <h3>保留的本地变化</h3>
                    <ul className="mt-3 space-y-2 font-data text-[11px]">
                      {selectedSource.dirty_files.map((file) => (
                        <li key={file}>{file}</li>
                      ))}
                    </ul>
                  </section>
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      <AlertDialog
        open={Boolean(policyPreview)}
        onOpenChange={(open) => !open && setPolicyPreview(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-label text-2xl">
              {policyPreview?.target_enabled ? "启用来源" : "停用来源"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {policyPreview?.skill_count || 0} 个 Skills 受影响。仓库、说明文档和 Profile 原始选择都会保留。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={() => void applyPolicy()}>
              确认{policyPreview?.target_enabled ? "启用" : "停用"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-label text-2xl">添加 Skill 来源</DialogTitle>
            <DialogDescription>
              先验证并发现 Skills，确认后才会写入 Vault 专用来源目录。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Select value={addKind} onValueChange={(value) => { setAddKind((value || "git") as "git" | "skills-cli"); setAddPreview(null) }}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="git">Git 严格锁定</SelectItem>
                <SelectItem value="skills-cli">Skills CLI 自管理</SelectItem>
              </SelectContent>
            </Select>
            <Input
              value={sourceInput}
              onChange={(event) => { setSourceInput(event.target.value); setAddPreview(null) }}
              placeholder={addKind === "git" ? "Git 地址或 git clone 命令" : "Skills 地址或 npx skills add 命令"}
            />
            {addKind === "git" && (
              <Input value={branch} onChange={(event) => setBranch(event.target.value)} placeholder="main" />
            )}
            {addPreview && (
              <div className="border border-[var(--safe)]/30 bg-[var(--safe)]/[0.06] p-3 text-xs">
                <div className="flex items-center gap-2 font-medium text-[var(--safe)]">
                  <ShieldCheck className="size-4" /> Preview 已就绪
                </div>
                <p className="mt-2 text-muted-foreground">
                  {addPreview.action === "merge"
                    ? `复用已有来源，新增 ${addPreview.skills_to_add?.length || 0} 个 Skill`
                    : addPreview.action === "unchanged"
                      ? "请求的 Skill 已全部存在，无需写入"
                      : `自动名称：${addPreview.source_id}`}
                  {addPreview.dependency ? `；使用 ${addPreview.dependency.name}（${addPreview.dependency.resolution_source}）` : ""}
                </p>
              </div>
            )}
            {!sourceDependencyReady && (
              <div className="border border-[var(--warning)]/30 bg-[var(--warning)]/[0.06] p-3 text-xs">
                <div className="flex items-center gap-2 font-medium text-[var(--warning)]">
                  <AlertTriangle className="size-4" /> 缺少 {addKind === "git" ? "Git" : "Node.js / npx"}
                </div>
                <p className="mt-2 text-muted-foreground">应用仍可使用本地能力；安装依赖后再添加这个来源。</p>
                <Button className="mt-3" size="sm" variant="outline" onClick={() => setDependenciesOpen(true)}>
                  打开依赖中心
                </Button>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddOpen(false)}>取消</Button>
            {addPreview ? (
              <Button onClick={() => void applyAdd()}>
                <Plus /> {addPreview.action === "merge" ? "添加 Skill" : addPreview.action === "unchanged" ? "确认" : "添加来源"}
              </Button>
            ) : (
              <Button onClick={() => void previewAdd()} disabled={!sourceInput.trim() || !sourceDependencyReady}>
                <RefreshCw /> 检查来源
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={dependenciesOpen} onOpenChange={setDependenciesOpen}>
        <DialogContent className="sm:max-w-[620px]">
          <DialogHeader>
            <DialogTitle className="font-label text-2xl">依赖中心</DialogTitle>
            <DialogDescription>
              检测完全离线；只有确认安装 Preview 后才会调用系统包管理器。
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[55vh] space-y-3 overflow-y-auto pr-1">
            {dependencies.map((dependency) => (
              <div className="rounded-xl border border-border/70 p-4" key={dependency.id}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-medium">{dependency.label}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {dependency.capabilities.join("；")}
                    </p>
                  </div>
                  <StatusPill
                    status={dependency.status === "available" ? "safe" : dependency.status === "unverified" ? "warning" : "fault"}
                  >
                    {dependency.status}
                  </StatusPill>
                </div>
                {(dependency.version || dependency.path) && (
                  <p className="mt-3 break-all font-data text-[10px] text-muted-foreground">
                    {[dependency.version, dependency.path].filter(Boolean).join(" · ")}
                  </p>
                )}
                {dependency.status === "missing" && ["git", "node", "npm", "npx"].includes(dependency.id) && (
                  <Button
                    className="mt-3"
                    size="sm"
                    variant="outline"
                    onClick={() => void previewDependencyInstall(dependency.id === "git" ? "git" : "node")}
                  >
                    查看安装方案
                  </Button>
                )}
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => void refreshDependencies()}>
              <RefreshCw /> 重新检测
            </Button>
            <Button onClick={() => setDependenciesOpen(false)}>完成</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={Boolean(dependencyPreview)}
        onOpenChange={(open) => !open && setDependencyPreview(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-label text-2xl">
              安装 {dependencyPreview?.label}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {dependencyPreview?.can_execute
                ? `将通过 ${dependencyPreview.provider} 执行以下命令。`
                : "当前平台需要手动安装，应用不会自动提权。"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          {dependencyPreview?.display_command && (
            <code className="block break-all rounded-lg bg-muted p-3 text-xs">
              {dependencyPreview.display_command}
            </code>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={() => void applyDependencyInstall()}>
              {dependencyPreview?.can_execute ? "确认安装" : "打开官方说明"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
