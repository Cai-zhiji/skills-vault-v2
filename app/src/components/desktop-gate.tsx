import { type ReactNode, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowLeft,
  ArrowRight,
  FolderInput,
  FolderOpen,
  LoaderCircle,
  PackagePlus,
  Sparkles,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ApiError, api } from "@/lib/api"
import { runtimeStartupError } from "@/lib/runtime"
import type {
  DesktopOnboardingPreview,
  DesktopOnboardingResult,
  DesktopStatusPayload,
} from "@/types/api"

type OnboardingAction = DesktopOnboardingPreview["action"]

const ACTIONS: Array<{
  id: OnboardingAction
  title: string
  description: string
  icon: typeof Sparkles
}> = [
  {
    id: "create",
    title: "创建新 Vault",
    description: "从空白工作区开始，稍后在里面创建自己的 Skills。",
    icon: Sparkles,
  },
  {
    id: "open",
    title: "打开已有 Vault",
    description: "直接继续使用已经由桌面版创建或迁移完成的 Vault。",
    icon: FolderOpen,
  },
  {
    id: "import",
    title: "导入 Skills 文件夹",
    description: "保留原文件夹，并把其中的 Skills 复制为“我的 Skills”。",
    icon: FolderInput,
  },
  {
    id: "migrate",
    title: "迁移旧版 Web Vault",
    description: "复制事实数据并重建运行状态，旧 Vault 保持不变。",
    icon: PackagePlus,
  },
]

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : "操作失败，请检查路径后重试"
}

function PreviewSummary({ preview }: { preview: DesktopOnboardingPreview }) {
  const candidate = preview.plan.candidate
  return (
    <div className="rounded-lg border border-border bg-muted/50 p-4 text-sm">
      <p className="mb-3 font-medium text-foreground">执行前确认</p>
      <dl className="grid gap-2 text-muted-foreground sm:grid-cols-[112px_1fr]">
        {preview.plan.source ? <><dt>读取位置</dt><dd className="break-all font-data text-xs text-foreground">{preview.plan.source}</dd></> : null}
        {preview.plan.destination ? <><dt>新 Vault</dt><dd className="break-all font-data text-xs text-foreground">{preview.plan.destination}</dd></> : null}
        {candidate ? <><dt>识别结果</dt><dd>{candidate.skill_count} 个可用 Skill</dd></> : null}
        {preview.plan.paths ? <><dt>初始化内容</dt><dd>{preview.plan.paths.length} 个目录或配置项</dd></> : null}
        {preview.plan.facts ? <><dt>迁移内容</dt><dd>{preview.plan.facts.length} 类事实数据，旧目录不会修改</dd></> : null}
      </dl>
    </div>
  )
}

export function DesktopGate({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [action, setAction] = useState<OnboardingAction | null>(null)
  const [sourcePath, setSourcePath] = useState("")
  const [destination, setDestination] = useState("")
  const [preview, setPreview] = useState<DesktopOnboardingPreview | null>(null)
  const [busy, setBusy] = useState(false)
  const statusQuery = useQuery({
    queryKey: ["desktop-status"],
    queryFn: () => api.get<DesktopStatusPayload>("/api/desktop/status"),
    retry: 2,
  })

  if (statusQuery.isLoading) {
    return (
      <main className="grid min-h-screen place-items-center text-muted-foreground">
        <div className="flex items-center gap-2"><LoaderCircle className="size-4 animate-spin" />正在准备 Skills Vault…</div>
      </main>
    )
  }
  if (statusQuery.isError || !statusQuery.data) {
    const startupError = runtimeStartupError()
    return (
      <main className="grid min-h-screen place-items-center p-6">
        <div className="max-w-md rounded-lg border bg-background p-6 text-center">
          <h1 className="text-lg font-semibold">无法连接本地服务</h1>
          <p className="mt-2 text-sm text-muted-foreground">请重新启动应用；你的 Vault 数据不会受到影响。</p>
          {startupError ? <p className="mt-3 break-words font-data text-xs text-destructive">{startupError.message}</p> : null}
          <Button className="mt-5" onClick={() => statusQuery.refetch()}>重新连接</Button>
        </div>
      </main>
    )
  }
  if (statusQuery.data.mode === "ready") return children

  const selected = ACTIONS.find((item) => item.id === action)
  const needsSource = action !== null && action !== "create"
  const needsDestination = action === "create" || action === "import" || action === "migrate"

  const choose = (next: OnboardingAction) => {
    setAction(next)
    setPreview(null)
    setSourcePath("")
    setDestination(statusQuery.data.default_vault)
  }

  const requestPreview = async () => {
    if (!action) return
    setBusy(true)
    try {
      const result = await api.post<DesktopOnboardingPreview>("/api/desktop/onboarding/preview", {
        action,
        source_path: sourcePath,
        destination,
      })
      setPreview(result)
    } catch (error) {
      toast.error(errorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  const apply = async () => {
    if (!preview) return
    setBusy(true)
    try {
      const result = await api.post<DesktopOnboardingResult>("/api/desktop/onboarding/apply", {
        preview_token: preview.preview_token,
      })
      toast.success(`Vault 已就绪：${result.active_vault}`)
      await queryClient.invalidateQueries()
    } catch (error) {
      toast.error(errorMessage(error))
      setPreview(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8">
      <section className="mx-auto max-w-4xl overflow-hidden border border-foreground bg-background shadow-xl">
        <header className="border-b border-border px-6 py-7 sm:px-9">
          <p className="eyebrow">SKILLS VAULT · FIRST START</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">准备你的 Skills 工作区</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Vault 是你自己保管的文件夹。应用只会记住它的位置，升级或卸载不会删除其中的数据。
          </p>
          {statusQuery.data.configured_vault_missing ? (
            <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              上次使用的 Vault 已移动或不可访问，请重新选择。
            </p>
          ) : null}
        </header>

        <div className="p-6 sm:p-9">
          {!selected ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {ACTIONS.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.id}
                    className="group flex min-h-36 items-start gap-4 rounded-lg border border-border bg-card p-5 text-left transition hover:-translate-y-0.5 hover:border-foreground hover:shadow-md"
                    onClick={() => choose(item.id)}
                    type="button"
                  >
                    <span className="grid size-10 shrink-0 place-items-center rounded-md bg-foreground text-background"><Icon className="size-5" /></span>
                    <span>
                      <strong className="flex items-center gap-2 text-base">{item.title}<ArrowRight className="size-4 opacity-0 transition group-hover:translate-x-1 group-hover:opacity-100" /></strong>
                      <span className="mt-2 block text-sm leading-6 text-muted-foreground">{item.description}</span>
                    </span>
                  </button>
                )
              })}
            </div>
          ) : (
            <div className="mx-auto max-w-2xl">
              <Button variant="ghost" className="mb-5" onClick={() => { setAction(null); setPreview(null) }} disabled={busy}>
                <ArrowLeft />返回选择
              </Button>
              <h2 className="text-xl font-semibold">{selected.title}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{selected.description}</p>

              {!preview ? (
                <div className="mt-6 grid gap-5">
                  {needsSource ? (
                    <label className="grid gap-2 text-sm font-medium">
                      {action === "open" ? "Vault 文件夹" : action === "migrate" ? "旧版 Web Vault 文件夹" : "原 Skills 仓库或文件夹"}
                      <Input value={sourcePath} onChange={(event) => setSourcePath(event.target.value)} placeholder="输入完整文件夹路径" autoFocus />
                    </label>
                  ) : null}
                  {needsDestination ? (
                    <label className="grid gap-2 text-sm font-medium">
                      新 Vault 保存位置
                      <Input value={destination} onChange={(event) => setDestination(event.target.value)} placeholder="输入完整文件夹路径" autoFocus={!needsSource} />
                    </label>
                  ) : null}
                  <p className="text-xs leading-5 text-muted-foreground">下一步只生成预览，不会立即写入文件。</p>
                  <Button className="justify-self-start" onClick={requestPreview} disabled={busy || (needsSource && !sourcePath.trim()) || (needsDestination && !destination.trim())}>
                    {busy ? <LoaderCircle className="animate-spin" /> : <ArrowRight />}生成预览
                  </Button>
                </div>
              ) : (
                <div className="mt-6 grid gap-5">
                  <PreviewSummary preview={preview} />
                  <div className="flex flex-wrap gap-2">
                    <Button onClick={apply} disabled={busy}>{busy ? <LoaderCircle className="animate-spin" /> : null}确认并继续</Button>
                    <Button variant="outline" onClick={() => setPreview(null)} disabled={busy}>修改路径</Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
