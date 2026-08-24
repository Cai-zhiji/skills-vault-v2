import { useState } from "react"
import { CheckCircle2, ExternalLink, FileText, ShieldCheck, TerminalSquare } from "lucide-react"
import { useQuery } from "@tanstack/react-query"

import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import type { DesktopStatusPayload, StatusPayload } from "@/types/api"

export function AboutPage() {
  const [updateChecked, setUpdateChecked] = useState(false)
  const runtimeQuery = useQuery({ queryKey: ["runtime"], queryFn: () => api.get<{ version: string; pid: number; desktop: boolean }>("/api/runtime") })
  const desktopQuery = useQuery({ queryKey: ["desktop-status"], queryFn: () => api.get<DesktopStatusPayload>("/api/desktop/status") })
  const statusQuery = useQuery({ queryKey: ["status"], queryFn: () => api.get<StatusPayload>("/api/status") })
  const version = runtimeQuery.data?.version || statusQuery.data?.app_version || "2.1.0"
  return <div className="page-stack about-page"><section className="about-plate"><div><p className="eyebrow">IDENTITY / BUILD RECORD</p><h2>Skills Vault</h2><p>本地优先的 Agent Skills 管理工作台。应用负责理解和协调，Vault 负责保管你的事实数据。</p></div><div className="about-version"><span>VERSION</span><strong>{version}</strong><small>INTERNAL / TESTING</small></div></section><section className="about-grid"><article><ShieldCheck /><h3>数据边界</h3><p>Vault、来源、说明文档和备份属于用户数据。应用升级或卸载不会删除这些内容。</p></article><article><TerminalSquare /><h3>运行时</h3><p>当前由本地 sidecar 提供服务，进程号 {runtimeQuery.data?.pid || "—"}，桌面模式 {runtimeQuery.data?.desktop ? "已启用" : "诊断模式"}。</p></article><article><FileText /><h3>当前工作区</h3><p>{desktopQuery.data?.active_vault || "尚未选择 Vault"}</p><small>{statusQuery.data?.catalog.skills || 0} 个 Skills · {statusQuery.data?.managed_links || 0} 个受管目标</small></article></section><section className="about-release"><div><p className="eyebrow">RELEASE NOTES / 2.1</p><h3>本次版本</h3><ul><li>新增 Vault 生命周期管理、帮助和设置入口。</li><li>增强错误详情、重试和安全诊断导出。</li><li>帮助中心支持全文搜索和首次使用引导。</li></ul></div><div className="about-update"><Button variant="outline" onClick={() => setUpdateChecked(true)}><CheckCircle2 />检查更新</Button>{updateChecked ? <p>当前已是最新内部测试版本 {version}。</p> : <p>更新检查只读取应用版本，不会访问 Vault 内容。</p>}</div></section><section className="about-links"><div><p className="eyebrow">DOCUMENTATION</p><h3>需要更多信息？</h3><p>使用帮助解释状态和操作边界；记录页面保留事务、备份和恢复入口。</p></div><div className="flex flex-wrap gap-2"><Button variant="outline" onClick={() => window.open("/help", "_self")}><FileText />打开帮助</Button><Button variant="outline" onClick={() => window.open("/records", "_self")}><ExternalLink />查看记录</Button></div></section></div>
}
