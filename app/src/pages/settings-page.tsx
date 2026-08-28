import { useMemo, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useSearchParams } from "react-router-dom"
import { CircleHelp, FolderCog, Laptop, ShieldCheck, SlidersHorizontal, Wrench } from "lucide-react"
import { Button } from "@/components/ui/button"
import { QueryErrorState } from "@/components/query-state"
import { HelpHint } from "@/components/help-hint"
import { api } from "@/lib/api"
import { readPreferences, updatePreferences, vaultMetaKey, type AppPreferences, type DensityPreference, type ThemePreference } from "@/lib/preferences"
import type { DependenciesPayload, DesktopStatusPayload, StatusPayload } from "@/types/api"

const sections = [
  { id: "vault", label: "Vault", icon: FolderCog, title: "Vault 与工作区", description: "管理当前工作区和桌面配置。" },
  { id: "platform", label: "平台", icon: Laptop, title: "Agent 平台", description: "查看 Codex、Claude Code 与 Lux Neo 的目标位置。" },
  { id: "dependencies", label: "依赖", icon: ShieldCheck, title: "外部依赖", description: "Git、Node.js 与 Skills CLI 的检测结果位于来源页面。" },
  { id: "diagnostics", label: "诊断", icon: Wrench, title: "诊断与数据", description: "查看运行信息、日志位置和可恢复数据边界。" },
  { id: "appearance", label: "外观", icon: SlidersHorizontal, title: "外观与交互", description: "主题、密度和动态效果设置将在后续版本提供。" },
]

export function SettingsPage() {
  const [params, setParams] = useSearchParams()
  const active = params.get("tab") || "vault"
  const current = sections.find((section) => section.id === active) || sections[0]
  const queryClient = useQueryClient()
  const [preferences, setPreferences] = useState<AppPreferences>(() => readPreferences())
  const desktopQuery = useQuery({ queryKey: ["desktop-status"], queryFn: () => api.get<DesktopStatusPayload>("/api/desktop/status") })
  const statusQuery = useQuery({ queryKey: ["status"], queryFn: () => api.get<StatusPayload>("/api/status") })
  const runtimeQuery = useQuery({ queryKey: ["runtime"], queryFn: () => api.get<{ version: string; pid: number; desktop: boolean }>("/api/runtime") })
  const dependenciesQuery = useQuery({ queryKey: ["dependencies"], queryFn: () => api.get<DependenciesPayload>("/api/dependencies") })
  const activePath = desktopQuery.data?.active_vault || ""
  const meta = preferences.vaultMeta[vaultMetaKey(activePath)] || {}
  const update = (patch: Partial<AppPreferences>) => { const next = updatePreferences(patch); setPreferences(next) }
  const updateMeta = (patch: typeof meta) => update({ vaultMeta: { ...preferences.vaultMeta, [vaultMetaKey(activePath)]: { ...meta, ...patch } } })
  const diagnostics = useMemo(() => ({ app_version: runtimeQuery.data?.version || statusQuery.data?.app_version || "—", sidecar: runtimeQuery.data?.desktop ? "desktop" : "browser-diagnostic", vault: activePath ? "selected" : "not-selected", catalog_skills: statusQuery.data?.catalog.skills || 0, managed_links: statusQuery.data?.managed_links || 0, dependencies: (dependenciesQuery.data?.dependencies || []).map((item) => ({ id: item.id, status: item.status, version: item.version })), note: "Paths, Skill content, session tokens and user file contents are excluded." }), [activePath, dependenciesQuery.data?.dependencies, runtimeQuery.data?.desktop, runtimeQuery.data?.version, statusQuery.data?.app_version, statusQuery.data?.catalog.skills, statusQuery.data?.managed_links])
  const downloadDiagnostics = () => { const blob = new Blob([JSON.stringify(diagnostics, null, 2)], { type: "application/json" }); const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = "skills-vault-diagnostics.json"; anchor.click(); URL.revokeObjectURL(url) }
  const refreshQueries = () => { void queryClient.invalidateQueries() }
  const queryError = desktopQuery.isError || statusQuery.isError || runtimeQuery.isError || dependenciesQuery.isError
  return (
    <div className="page-stack settings-page">
      <section className="settings-intro">
        <div className="settings-intro-copy"><p className="eyebrow">DESKTOP CONFIGURATION</p><h2>设置</h2><p>应用设置只影响本机界面和运行方式，不拥有或覆盖 Vault 中的用户数据。</p></div>
        <div className="settings-intro-aside"><CircleHelp className="settings-intro-mark" /><span>LOCAL / PRIVATE</span></div>
      </section>
      {queryError ? <QueryErrorState onRetry={refreshQueries} /> : null}
      <div className="settings-layout">
        <nav className="settings-nav" aria-label="设置分类">
          <p className="settings-nav-label eyebrow">CONFIG INDEX</p>
          {sections.map((section) => {
            const Icon = section.icon
            return <button key={section.id} type="button" className={active === section.id ? "settings-nav-item settings-nav-item-active" : "settings-nav-item"} onClick={() => setParams({ tab: section.id })}><span className="settings-nav-marker" /><Icon /><span>{section.label}</span></button>
          })}
        </nav>
        <section className="settings-panel">
          <div className="settings-panel-heading"><div><p className="eyebrow">{current.label.toUpperCase()}</p><h3>{current.title}</h3></div><div className="flex items-center gap-2"><HelpHint text={`查看${current.label}帮助`} /><span className="settings-panel-state">DESKTOP</span></div></div>
          <p className="settings-panel-description">{current.description}</p>
          {active === "vault" ? <div className="settings-content-stack"><div className="settings-note"><strong>当前 Vault 的切换入口在左上角。</strong><span>在那里可以查看路径、打开最近 Vault、重新扫描或退出当前 Vault。退出不会删除任何文件。</span></div><div className="settings-field-grid"><label>显示名称<input value={meta.alias || ""} onChange={(event) => updateMeta({ alias: event.target.value })} placeholder={activePath.split(/[\\/]/).filter(Boolean).at(-1) || "当前 Vault"} /></label><label>标签<input value={(meta.tags || []).join(", ")} onChange={(event) => updateMeta({ tags: event.target.value.split(",").map((tag) => tag.trim()).filter(Boolean) })} placeholder="例如：工作、研究" /></label></div><label className="settings-check"><input type="checkbox" checked={meta.favorite === true} onChange={(event) => updateMeta({ favorite: event.target.checked })} />收藏当前 Vault，显示在最近列表顶部</label></div> : null}
          {active === "platform" ? <div className="settings-content-stack"><div className="settings-data-list"><div><span>运行模式</span><strong>{runtimeQuery.data?.desktop ? "Tauri 桌面" : "浏览器诊断"}</strong></div><div><span>应用版本</span><strong>{runtimeQuery.data?.version || "—"}</strong></div><div><span>受管目标</span><strong>{statusQuery.data?.managed_links ?? "—"}</strong></div></div><div className="settings-note"><strong>平台目录由系统适配器计算。</strong><span>请在 Skills 页面查看每个 Skill 的实际安装状态。</span></div></div> : null}
          {active === "dependencies" ? <div className="settings-content-stack"><div className="settings-dependency-list">{(dependenciesQuery.data?.dependencies || []).map((dependency) => <div key={dependency.id}><span><strong>{dependency.label}</strong><small>{dependency.version || dependency.path || "未检测到版本"}</small></span><em data-status={dependency.status}>{dependency.status}</em></div>)}</div><div className="settings-note"><strong>缺失依赖不会阻止本地 Skills 管理。</strong><span>需要来源更新或 Skills CLI 能力时，再按来源页面提供的官方入口安装。</span></div></div> : null}
          {active === "diagnostics" ? <div className="settings-content-stack"><div className="settings-note"><strong>诊断导出遵循最小披露。</strong><span>只包含版本、运行模式、数量和依赖状态，不包含 Skill 正文、令牌、完整路径或用户文件内容。</span></div><div className="settings-log-row"><div><span>本机日志目录</span><code>{desktopQuery.data?.config_root ? `${desktopQuery.data.config_root}/logs` : "—"}</code></div><Button variant="outline" size="sm" onClick={() => { if (desktopQuery.data?.config_root) void navigator.clipboard.writeText(`${desktopQuery.data.config_root}/logs`) }}>复制路径</Button></div><Button onClick={downloadDiagnostics}><Wrench />导出安全诊断</Button></div> : null}
          {active === "appearance" ? <div className="settings-content-stack"><div className="settings-preference-grid"><label>主题<select value={preferences.theme} onChange={(event) => update({ theme: event.target.value as ThemePreference })}><option value="workbench">工作台</option><option value="light">浅色</option><option value="dark">深色</option></select></label><label>密度<select value={preferences.density} onChange={(event) => update({ density: event.target.value as DensityPreference })}><option value="comfortable">舒适</option><option value="compact">紧凑</option></select></label></div><label className="settings-check"><input type="checkbox" checked={preferences.reduceMotion} onChange={(event) => update({ reduceMotion: event.target.checked })} />减少动态效果</label><label className="settings-check"><input type="checkbox" checked={preferences.shortcuts} onChange={(event) => update({ shortcuts: event.target.checked })} />启用键盘快捷键和命令面板</label><div className="settings-note"><strong>设置立即生效。</strong><span>这些偏好只保存在本机桌面配置，不会修改 Vault 内容。</span></div></div> : null}
        </section>
      </div>
    </div>
  )
}
