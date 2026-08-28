import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArchiveRestore,
  ArrowRight,
  CheckCircle2,
  Clock3,
  DatabaseBackup,
  FileClock,
  RotateCcw,
} from "lucide-react"

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
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"
import { formatDate, operationLabel } from "@/lib/format"
import { useOperation } from "@/lib/operation-context"
import type {
  ApplyResponse,
  BackupRow,
  PreviewTokenResponse,
  TransactionRow,
} from "@/types/api"

interface UpdateReportsPayload {
  reports: Array<Record<string, unknown>>
}

export function RecordsPage() {
  const [selectedTransaction, setSelectedTransaction] =
    useState<TransactionRow | null>(null)
  const [restorePreview, setRestorePreview] =
    useState<(PreviewTokenResponse & { backup_id: string }) | null>(null)
  const queryClient = useQueryClient()
  const { runOperation } = useOperation()

  const transactionsQuery = useQuery({
    queryKey: ["transactions"],
    queryFn: () => api.get<TransactionRow[]>("/api/transactions"),
  })
  const backupsQuery = useQuery({
    queryKey: ["backups"],
    queryFn: () => api.get<BackupRow[]>("/api/backups"),
  })
  const updatesQuery = useQuery({
    queryKey: ["update-reports"],
    queryFn: () => api.get<UpdateReportsPayload>("/api/updates"),
  })

  const previewRestore = async (backup: BackupRow) => {
    const result = await runOperation(
      "restore.preview",
      "生成恢复 Preview",
      "验证备份存在并绑定当前状态",
      () =>
        api.post<PreviewTokenResponse & { backup_id: string }>(
          "/api/backups/restore/preview",
          { backup_id: backup.id },
        ),
      () => `备份 ${backup.id} 可以恢复`,
    )
    if (result) setRestorePreview(result)
  }

  const applyRestore = async () => {
    if (!restorePreview) return
    const result = await runOperation(
      "restore.apply",
      "恢复平台备份",
      "应用已确认的备份并重新扫描状态",
      () =>
        api.post<ApplyResponse>("/api/backups/restore/apply", {
          preview_token: restorePreview.preview_token,
        }),
      (value) => `备份恢复完成；事务 ${value.transaction_id}`,
    )
    if (result) {
      setRestorePreview(null)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["transactions"] }),
        queryClient.invalidateQueries({ queryKey: ["backups"] }),
        queryClient.invalidateQueries({ queryKey: ["status"] }),
      ])
    }
  }

  const transactions = transactionsQuery.data || []
  const completeCount = transactions.filter((row) => row.status === "complete").length
  const failedCount = transactions.filter((row) =>
    ["failed", "rolled-back"].includes(row.status),
  ).length

  return (
    <div className="page-stack">
      {transactionsQuery.isError || backupsQuery.isError || updatesQuery.isError ? <QueryErrorState message="记录或备份暂时无法读取" onRetry={() => { void queryClient.invalidateQueries({ queryKey: ["transactions"] }); void queryClient.invalidateQueries({ queryKey: ["backups"] }); void queryClient.invalidateQueries({ queryKey: ["update-reports"] }) }} /> : null}
      <section className="record-ledger-head">
        <div className="record-ledger-title">
          <p className="eyebrow">LOCAL AUDIT LEDGER</p>
          <h2>每次写入都有去处</h2>
          <p>事务、备份和更新报告共同说明：做了什么、没有做什么、如何恢复。</p>
        </div>
        <div className="record-totals">
          <div><span>{transactions.length}</span><small>近期事务</small></div>
          <div><span>{completeCount}</span><small>已完成</small></div>
          <div><span>{failedCount}</span><small>失败 / 回滚</small></div>
          <div><span>{backupsQuery.data?.length || 0}</span><small>可用备份</small></div>
        </div>
      </section>

      <Tabs defaultValue="transactions" className="record-tabs">
        <TabsList>
          <TabsTrigger value="transactions"><FileClock /> 事务</TabsTrigger>
          <TabsTrigger value="backups"><DatabaseBackup /> 备份</TabsTrigger>
          <TabsTrigger value="updates"><Clock3 /> 更新报告</TabsTrigger>
        </TabsList>

        <TabsContent value="transactions" className="mt-4">
          <section className="ledger-table">
            <div className="ledger-row ledger-header">
              <span>操作</span><span>状态</span><span>时间</span><span></span>
            </div>
            {transactions.length ? transactions.map((row) => (
              <button
                key={row.transaction_id}
                type="button"
                className="ledger-row ledger-entry"
                onClick={() => setSelectedTransaction(row)}
              >
                <span>
                  <strong>{operationLabel(row.operation)}</strong>
                  <small>{row.transaction_id}</small>
                </span>
                <span>
                  <StatusPill
                    status={
                      row.status === "complete"
                        ? "safe"
                        : row.status === "no-op" || row.status === "unchanged"
                          ? "muted"
                          : "fault"
                    }
                  >
                    {row.status}
                  </StatusPill>
                </span>
                <span className="font-data text-[10px]">{formatDate(row.created_at)}</span>
                <span><ArrowRight className="size-4" /></span>
              </button>
            )) : <QueryEmptyState title="还没有事务记录" description="完成一次扫描、同步、更新或恢复后，操作记录会显示在这里。" />}
          </section>
        </TabsContent>

        <TabsContent value="backups" className="mt-4">
          <section className="backup-grid">
            {backupsQuery.data?.length ? backupsQuery.data.map((backup) => (
              <article className="backup-card" key={backup.id}>
                <div className="flex items-start justify-between gap-3">
                  <div className="backup-icon"><ArchiveRestore /></div>
                  <StatusPill status="safe">可恢复</StatusPill>
                </div>
                <h3 className="mt-5 font-data text-sm">{backup.id}</h3>
                <p className="mt-2 break-all text-[11px] leading-5 text-muted-foreground">{backup.path}</p>
                <Button variant="outline" className="mt-5" onClick={() => void previewRestore(backup)}>
                  <RotateCcw /> 预览恢复
                </Button>
              </article>
            )) : <QueryEmptyState title="还没有可用备份" description="应用会在重要写入前创建可恢复备份。" />}
          </section>
        </TabsContent>

        <TabsContent value="updates" className="mt-4">
          <section className="update-report-list">
            {updatesQuery.data?.reports?.length ? updatesQuery.data.reports.map((report, index) => (
              <article key={`${String(report.generated_at || "report")}-${index}`}>
                <div className="grid size-8 place-items-center border bg-surface">
                  <CheckCircle2 className="size-4 text-[var(--safe)]" />
                </div>
                <div className="min-w-0">
                  <h3>来源更新报告</h3>
                  <p>{formatDate(String(report.generated_at || ""))}</p>
                </div>
                <StatusPill status={report.applied ? "safe" : "muted"}>
                  {report.applied ? "已应用" : "仅检查"}
                </StatusPill>
              </article>
            )) : <QueryEmptyState title="还没有更新报告" description="检查来源更新后，报告会保留在这里。" />}
          </section>
        </TabsContent>
      </Tabs>

      <Sheet
        open={Boolean(selectedTransaction)}
        onOpenChange={(open) => !open && setSelectedTransaction(null)}
      >
        <SheetContent className="w-full p-0 sm:max-w-[520px]">
          {selectedTransaction && (
            <>
              <SheetHeader className="detail-sheet-header">
                <StatusPill status={selectedTransaction.status === "complete" ? "safe" : "warning"}>
                  {selectedTransaction.status}
                </StatusPill>
                <SheetTitle className="mt-4 font-label text-3xl tracking-wide">
                  {operationLabel(selectedTransaction.operation)}
                </SheetTitle>
                <SheetDescription>{selectedTransaction.transaction_id}</SheetDescription>
              </SheetHeader>
              <div className="p-5">
                <pre className="technical-json">{JSON.stringify(selectedTransaction, null, 2)}</pre>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      <AlertDialog
        open={Boolean(restorePreview)}
        onOpenChange={(open) => !open && setRestorePreview(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-label text-2xl">恢复平台备份</AlertDialogTitle>
            <AlertDialogDescription>
              将恢复备份 `{restorePreview?.backup_id}`。这会改变 Codex / Claude Code / Lux Neo 的受管部署，但不会删除 Vault 中的 Skill 文件。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={() => void applyRestore()}>确认恢复</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
