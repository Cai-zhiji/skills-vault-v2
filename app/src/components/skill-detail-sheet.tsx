import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Braces,
  CopyPlus,
  FileText,
  GitBranch,
  ShieldAlert,
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { StatusPill } from "@/components/status-pill"
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
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"
import { formatDate, shortHash } from "@/lib/format"
import { useOperation } from "@/lib/operation-context"
import type {
  ApplyResponse,
  SkillDetailPayload,
  SkillGuidePayload,
} from "@/types/api"

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="detail-row">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  )
}

export function SkillDetailSheet({
  skillId,
  onOpenChange,
}: {
  skillId: string | null
  onOpenChange: (open: boolean) => void
}) {
  const [deriveOpen, setDeriveOpen] = useState(false)
  const [derivedName, setDerivedName] = useState("")
  const queryClient = useQueryClient()
  const { runOperation } = useOperation()
  const detailQuery = useQuery({
    queryKey: ["skill", skillId],
    queryFn: () =>
      api.get<SkillDetailPayload>(`/api/skills/${encodeURIComponent(skillId || "")}`),
    enabled: Boolean(skillId),
  })
  const guideQuery = useQuery({
    queryKey: ["skill-guide", skillId],
    queryFn: () =>
      api.get<SkillGuidePayload>(
        `/api/skills/${encodeURIComponent(skillId || "")}/guide`,
      ),
    enabled: Boolean(skillId),
  })
  const skill = detailQuery.data

  const derive = async () => {
    if (!skillId || !derivedName.trim()) return
    const result = await runOperation(
      "skill.derive",
      "派生 Skill",
      "复制上游内容并记录来源基线",
      () =>
        api.post<ApplyResponse>("/api/derive", {
          source_skill_id: skillId,
          new_name: derivedName.trim(),
        }),
      () => `已创建 my/${derivedName.trim()}`,
    )
    if (result) {
      setDeriveOpen(false)
      setDerivedName("")
      await queryClient.invalidateQueries({ queryKey: ["skills"] })
      await queryClient.invalidateQueries({ queryKey: ["status"] })
    }
  }

  return (
    <>
      <Sheet open={Boolean(skillId)} onOpenChange={onOpenChange}>
        <SheetContent className="w-full gap-0 p-0 sm:max-w-[560px]">
          {skill ? (
            <>
              <SheetHeader className="detail-sheet-header">
                <div className="flex flex-wrap items-center gap-2 pr-10">
                  <StatusPill status={skill.source_id === "my" ? "safe" : "muted"}>
                    {skill.source_id}
                  </StatusPill>
                  <StatusPill
                    status={skill.risk_signals.length ? "warning" : "safe"}
                  >
                    {skill.risk_signals.length
                      ? `${skill.risk_signals.length} 个风险信号`
                      : "未见明显风险"}
                  </StatusPill>
                </div>
                <SheetTitle className="mt-4 font-label text-3xl tracking-wide">
                  {skill.name}
                </SheetTitle>
                <SheetDescription className="mt-2 leading-6">
                  {skill.summary_zh || skill.description || "暂无说明"}
                </SheetDescription>
              </SheetHeader>

              <Tabs defaultValue="overview" className="min-h-0 flex-1">
                <TabsList className="mx-4 mt-4 grid w-[calc(100%-2rem)] grid-cols-3">
                  <TabsTrigger value="overview">概览</TabsTrigger>
                  <TabsTrigger value="guide">说明文档</TabsTrigger>
                  <TabsTrigger value="technical">技术信息</TabsTrigger>
                </TabsList>
                <ScrollArea className="h-[calc(100vh-210px)]">
                  <TabsContent value="overview" className="m-0 p-4">
                    <dl className="detail-list">
                      <DetailRow label="调用方式">
                        <div className="flex flex-wrap gap-2">
                          <code>{skill.invocation.codex}</code>
                          <code>{skill.invocation.claude}</code>
                        </div>
                      </DetailRow>
                      <DetailRow label="兼容平台">
                        {skill.compatibility.platforms.join(" / ") || "—"}
                      </DetailRow>
                      <DetailRow label="Codex">
                        <StatusPill
                          status={skill.enablement.codex.selected ? "safe" : "muted"}
                        >
                          {skill.enablement.codex.state}
                        </StatusPill>
                      </DetailRow>
                      <DetailRow label="Claude Code">
                        <StatusPill
                          status={skill.enablement.claude.selected ? "safe" : "muted"}
                        >
                          {skill.enablement.claude.state}
                        </StatusPill>
                      </DetailRow>
                      <DetailRow label="分类">{skill.classification}</DetailRow>
                      <DetailRow label="审核状态">{skill.review_status}</DetailRow>
                      <DetailRow label="依赖">
                        {skill.requires.length ? skill.requires.join("、") : "无"}
                      </DetailRow>
                    </dl>

                    {skill.recommended_for.length > 0 && (
                      <section className="detail-section">
                        <h3>适合场景</h3>
                        <ul>
                          {skill.recommended_for.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </section>
                    )}

                    {skill.risk_signals.length > 0 && (
                      <section className="detail-section border-[var(--copper)]/30 bg-[var(--copper)]/[0.06]">
                        <h3 className="flex items-center gap-2">
                          <ShieldAlert className="size-4" /> 风险信号
                        </h3>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {skill.risk_signals.map((item) => (
                            <StatusPill key={item} status="warning">
                              {item}
                            </StatusPill>
                          ))}
                        </div>
                      </section>
                    )}
                  </TabsContent>

                  <TabsContent value="guide" className="m-0 p-5">
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <div>
                        <p className="eyebrow">MARKDOWN GUIDE</p>
                        <p className="mt-1 font-data text-[10px] text-muted-foreground">
                          {guideQuery.data?.path || "正在读取…"}
                        </p>
                      </div>
                      <FileText className="size-4 text-muted-foreground" />
                    </div>
                    <article className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {guideQuery.data?.markdown || "正在读取说明文档…"}
                      </ReactMarkdown>
                    </article>
                  </TabsContent>

                  <TabsContent value="technical" className="m-0 p-4">
                    <dl className="detail-list">
                      <DetailRow label="路径">
                        <code className="break-all">{skill.path}</code>
                      </DetailRow>
                      <DetailRow label="来源 Commit">
                        <code>{shortHash(skill.source_commit)}</code>
                      </DetailRow>
                      <DetailRow label="最后变化">
                        {formatDate(
                          skill.upstream_modified_at || skill.local_modified_at,
                        )}
                      </DetailRow>
                      <DetailRow label="Fingerprint">
                        <code>{shortHash(skill.fingerprint)}</code>
                      </DetailRow>
                      <DetailRow label="脚本">
                        {skill.scripts.length ? skill.scripts.join("、") : "无"}
                      </DetailRow>
                    </dl>
                    <section className="detail-section">
                      <h3 className="flex items-center gap-2">
                        <Braces className="size-4" /> 领域元数据
                      </h3>
                      <pre className="technical-json">
                        {JSON.stringify(
                          {
                            origin: skill.origin_detail,
                            compatibility: skill.compatibility,
                            source: skill.source,
                          },
                          null,
                          2,
                        )}
                      </pre>
                    </section>
                  </TabsContent>
                </ScrollArea>
              </Tabs>

              <div className="detail-actions">
                {skill.source_id !== "my" && (
                  <Button variant="outline" onClick={() => setDeriveOpen(true)}>
                    <CopyPlus /> 派生到 my-skills
                  </Button>
                )}
              </div>
            </>
          ) : (
            <div className="grid h-full place-items-center p-8 text-sm text-muted-foreground">
              {detailQuery.isError ? "无法读取 Skill 详情" : "正在读取 Skill…"}
            </div>
          )}
        </SheetContent>
      </Sheet>

      <Dialog open={deriveOpen} onOpenChange={setDeriveOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-label text-xl">派生 Skill</DialogTitle>
            <DialogDescription>
              复制上游 Skill 到 `my-skills`，并记录来源 commit 与内容指纹。上游仓库不会被修改。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <label className="text-xs font-medium" htmlFor="derived-name">
              新名称
            </label>
            <Input
              id="derived-name"
              value={derivedName}
              onChange={(event) => setDerivedName(event.target.value)}
              placeholder={`${skill?.name || "skill"}-custom`}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeriveOpen(false)}>
              取消
            </Button>
            <Button onClick={() => void derive()} disabled={!derivedName.trim()}>
              <GitBranch /> 创建派生
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
