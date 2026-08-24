import { AlertOctagon, CheckCircle2, CircleDotDashed, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useOperation } from "@/lib/operation-context"
import { cn } from "@/lib/utils"

export function OperationRail() {
  const { operation, dismissOperation, retryOperation } = useOperation()
  const isIdle = operation.state === "idle"
  const isRunning = operation.state === "running"
  const isFailed = operation.state === "failed"

  const Icon = isRunning
    ? CircleDotDashed
    : isFailed
      ? AlertOctagon
      : operation.state === "success"
        ? CheckCircle2
        : CircleDotDashed

  return (
    <section
      aria-live="polite"
      aria-busy={isRunning}
      className={cn(
        "operation-panel relative overflow-hidden border-t px-4 py-4",
        isFailed && "bg-[var(--fault)]/[0.055]",
      )}
    >
      {isRunning && <div className="operation-scan" aria-hidden="true" />}
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "mt-0.5 grid size-7 shrink-0 place-items-center rounded-sm border bg-surface",
            isRunning && "border-[var(--copper)] text-[var(--copper)]",
            isFailed && "border-[var(--fault)] text-[var(--fault)]",
            operation.state === "success" &&
              "border-[var(--safe)] text-[var(--safe)]",
          )}
        >
          <Icon className={cn("size-4", isRunning && "animate-spin")} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-label text-sm tracking-wide text-foreground">
                {operation.title}
              </p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {operation.phase}
              </p>
            </div>
            {!isIdle && !isRunning && (
              <Button
                variant="ghost"
                size="icon-xs"
                aria-label="关闭操作信息"
                onClick={dismissOperation}
              >
                <X />
              </Button>
            )}
          </div>
          {operation.summary && (
            <p className="mt-2 text-xs font-medium text-[var(--safe)]">
              {operation.summary}
            </p>
          )}
          {operation.error && (
            <div className="mt-3 border-l-2 border-[var(--fault)] pl-3">
              <p className="text-xs font-medium text-[var(--fault)]">
                {operation.error}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {operation.retryable && <Button variant="outline" size="xs" onClick={() => void retryOperation()}>重试</Button>}
                {operation.errorCode && <span className="self-center font-data text-[9px] text-muted-foreground">{operation.errorCode}</span>}
              </div>
              {operation.errorDetails && Object.keys(operation.errorDetails).length > 0 && (
                <details className="mt-2 text-[10px] text-muted-foreground">
                  <summary className="cursor-pointer">查看错误详情</summary>
                  <pre className="technical-json mt-2 max-h-32">{JSON.stringify(operation.errorDetails, null, 2)}</pre>
                </details>
              )}
              <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
                未确认的写入不会继续执行。处理原因后重新生成 Preview。
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
