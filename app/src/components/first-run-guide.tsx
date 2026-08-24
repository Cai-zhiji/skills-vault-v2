import { useState } from "react"
import { ArrowRight, Boxes, CircleHelp, GitBranch, X } from "lucide-react"
import { useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { updatePreferences } from "@/lib/preferences"

export function FirstRunGuide() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(() => {
    try { return localStorage.getItem("skills-vault.preferences.v1")?.includes('"onboardingDismissed":true') !== true } catch { return true }
  })
  if (!open) return null
  const close = () => { updatePreferences({ onboardingDismissed: true }); setOpen(false) }
  return <section className="first-run-guide" aria-label="快速入门"><div className="first-run-guide-mark"><CircleHelp /></div><div className="first-run-guide-body"><div className="flex items-start justify-between gap-3"><div><p className="eyebrow">FIRST RUN / FIELD GUIDE</p><h2>先看状态，再做写入</h2></div><Button variant="ghost" size="icon-xs" aria-label="关闭快速入门" onClick={close}><X /></Button></div><div className="first-run-guide-steps"><button type="button" onClick={() => navigate("/skills")}><Boxes /><span><strong>浏览 Skills</strong><small>先确认来源、兼容平台和健康状态</small></span><ArrowRight /></button><button type="button" onClick={() => navigate("/sources")}><GitBranch /><span><strong>检查来源</strong><small>再处理更新、信任和依赖</small></span><ArrowRight /></button><button type="button" onClick={() => navigate("/help")}><CircleHelp /><span><strong>打开帮助</strong><small>随时查阅状态和恢复路径</small></span><ArrowRight /></button></div></div></section>
}
