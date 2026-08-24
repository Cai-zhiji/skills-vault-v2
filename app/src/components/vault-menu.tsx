import { useEffect, useMemo, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Check,
  ChevronDown,
  ExternalLink,
  FolderOpen,
  LogOut,
  RefreshCw,
  Settings2,
  Vault,
} from "lucide-react"
import { open } from "@tauri-apps/plugin-dialog"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { api, ApiError } from "@/lib/api"
import { isTauriRuntime } from "@/lib/runtime"
import { useOperation } from "@/lib/operation-context"
import { readPreferences, vaultMetaKey, type AppPreferences } from "@/lib/preferences"
import type { DesktopLeaveResult, DesktopOnboardingPreview, DesktopOnboardingResult, DesktopStatusPayload } from "@/types/api"

function vaultLabel(path: string | null | undefined) {
  if (!path) return "未选择 Vault"
  return path.split(/[\\/]/).filter(Boolean).at(-1) || path
}

export function VaultMenu() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { operation, runOperation } = useOperation()
  const [switchOpen, setSwitchOpen] = useState(false)
  const [switchPath, setSwitchPath] = useState("")
  const [switchPreview, setSwitchPreview] = useState<DesktopOnboardingPreview | null>(null)
  const [leaveOpen, setLeaveOpen] = useState(false)
  const [leavePreview, setLeavePreview] = useState<DesktopOnboardingPreview | null>(null)
  const [preferences, setPreferences] = useState<AppPreferences>(() => readPreferences())
  const statusQuery = useQuery({
    queryKey: ["desktop-status"],
    queryFn: () => api.get<DesktopStatusPayload>("/api/desktop/status"),
  })
  const status = statusQuery.data
  const busy = operation.state === "running"
  const recentVaults = useMemo(() => (status?.recent_vaults || []).filter((path) => path !== status?.active_vault).sort((left, right) => Number(preferences.vaultMeta[vaultMetaKey(right)]?.favorite === true) - Number(preferences.vaultMeta[vaultMetaKey(left)]?.favorite === true)), [preferences.vaultMeta, status?.active_vault, status?.recent_vaults])
  const activeMeta = preferences.vaultMeta[vaultMetaKey(status?.active_vault)] || {}

  const refreshWorkspace = async () => {
    await queryClient.invalidateQueries()
  }

  useEffect(() => {
    const handlePreferences = (event: Event) => setPreferences((event as CustomEvent<AppPreferences>).detail)
    window.addEventListener("skills-vault-preferences", handlePreferences)
    return () => window.removeEventListener("skills-vault-preferences", handlePreferences)
  }, [])

  const previewSwitch = async () => {
    if (!switchPath.trim()) return
    try {
      const preview = await api.post<DesktopOnboardingPreview>("/api/desktop/onboarding/preview", { action: "open", source_path: switchPath.trim() })
      setSwitchPreview(preview)
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "无法识别这个 Vault")
    }
  }

  const applySwitch = async () => {
    if (!switchPreview) return
    const result = await runOperation(
      "desktop.vault.switch",
      "切换当前 Vault",
      "确认目标目录并重新装载工作台",
      () => api.post<DesktopOnboardingResult>("/api/desktop/onboarding/apply", { preview_token: switchPreview.preview_token }),
      (value) => `已切换到 ${vaultLabel(value.active_vault)}`,
    )
    if (result) {
      setSwitchOpen(false)
      setSwitchPreview(null)
      setSwitchPath("")
      await refreshWorkspace()
    }
  }

  const previewLeave = async () => {
    try {
      const preview = await api.post<DesktopOnboardingPreview>("/api/desktop/onboarding/preview", { action: "leave" })
      setLeavePreview(preview)
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "无法退出当前 Vault")
    }
  }

  const leaveVault = async () => {
    if (!leavePreview) return
    const result = await runOperation(
      "desktop.vault.leave",
      "退出当前 Vault",
      "清除活动工作区，不修改 Vault 文件",
      () => api.post<DesktopLeaveResult>("/api/desktop/onboarding/apply", { preview_token: leavePreview.preview_token }),
      () => "已退出当前 Vault",
    )
    if (result) {
      setLeaveOpen(false)
      setLeavePreview(null)
      await queryClient.invalidateQueries()
      navigate("/skills", { replace: true })
    }
  }

  const chooseRecent = (path: string) => {
    setSwitchPath(path)
    setSwitchPreview(null)
    setSwitchOpen(true)
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger render={<Button variant="ghost" className="vault-menu-trigger" disabled={busy} />}>
          <span className="vault-menu-mark"><Vault className="size-3.5" /></span>
          <span className="min-w-0 text-left"><span className="vault-menu-title"><span className="vault-status-dot" />{activeMeta.alias || vaultLabel(status?.active_vault)}</span><span className="vault-menu-path">{status?.active_vault || "选择一个本地工作区"}</span></span>
          <ChevronDown className="ml-auto size-3.5 shrink-0 opacity-50" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-80">
          <div className="px-3 py-2"><p className="eyebrow">ACTIVE VAULT</p><p className="mt-1 break-all font-data text-[10px] text-muted-foreground">{status?.active_vault || "尚未选择"}</p></div>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => { setSwitchPath(""); setSwitchPreview(null); setSwitchOpen(true) }}><FolderOpen />切换 Vault</DropdownMenuItem>
          {recentVaults.length ? <div className="px-3 pb-1 pt-2 text-[10px] text-muted-foreground">最近使用</div> : null}
          {recentVaults.map((path) => <DropdownMenuItem key={path} onClick={() => chooseRecent(path)}><Vault /><span className="min-w-0 truncate">{preferences.vaultMeta[vaultMetaKey(path)]?.alias || vaultLabel(path)}</span>{preferences.vaultMeta[vaultMetaKey(path)]?.favorite ? <span className="ml-auto text-[var(--copper)]">★</span> : <Check className="ml-auto size-3 opacity-0" />}</DropdownMenuItem>)}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => navigate("/settings?tab=vault")}><Settings2 />Vault 设置</DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate("/skills?action=scan")}><RefreshCw />重新扫描</DropdownMenuItem>
          {isTauriRuntime() ? <DropdownMenuItem onClick={() => window.open(`file://${status?.active_vault || ""}`, "_blank")}><ExternalLink />打开所在文件夹</DropdownMenuItem> : null}
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive" onClick={() => setLeaveOpen(true)}><LogOut />退出当前 Vault</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={leaveOpen} onOpenChange={setLeaveOpen}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>退出当前 Vault？</AlertDialogTitle><AlertDialogDescription>应用会回到 Vault 选择页，只清除当前活动工作区，不会删除、移动或修改“{vaultLabel(status?.active_vault)}”中的文件。</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel disabled={busy}>取消</AlertDialogCancel>{leavePreview ? <AlertDialogAction variant="destructive" onClick={() => void leaveVault()} disabled={busy}>确认退出</AlertDialogAction> : <Button variant="destructive" onClick={() => void previewLeave()} disabled={busy}>生成退出预览</Button>}</AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={switchOpen} onOpenChange={(open) => { if (!open) { setSwitchOpen(false); setSwitchPreview(null) } }}>
        <AlertDialogContent className="max-w-lg">
          <AlertDialogHeader><AlertDialogTitle>切换 Vault</AlertDialogTitle><AlertDialogDescription>先识别目录，再确认切换。切换只改变应用当前指向，不会修改目标目录。</AlertDialogDescription></AlertDialogHeader>
          {!switchPreview ? <div className="grid gap-3"><label className="grid gap-2 text-sm font-medium" htmlFor="switch-vault-path">Vault 文件夹<input id="switch-vault-path" value={switchPath} onChange={(event) => setSwitchPath(event.target.value)} placeholder="输入完整文件夹路径" className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50" autoFocus /></label>{isTauriRuntime() ? <Button variant="outline" onClick={async () => { const selected = await open({ directory: true, multiple: false, title: "选择要打开的 Vault" }); if (selected) setSwitchPath(selected) }}>选择文件夹…</Button> : null}<Button onClick={() => void previewSwitch()} disabled={!switchPath.trim()}>生成切换预览</Button></div> : <div className="grid gap-3"><div className="border border-border bg-muted/40 p-3 text-sm"><p className="font-medium">将打开</p><p className="mt-1 break-all font-data text-xs text-muted-foreground">{switchPreview.plan.source}</p></div><div className="flex gap-2"><Button onClick={() => void applySwitch()} disabled={busy}>确认切换</Button><Button variant="outline" onClick={() => setSwitchPreview(null)} disabled={busy}>修改路径</Button></div></div>}
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
