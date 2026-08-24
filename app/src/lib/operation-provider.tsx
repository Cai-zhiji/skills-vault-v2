import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react"
import { toast } from "sonner"

import { ApiError } from "@/lib/api"
import {
  idleOperation,
  OperationContext,
  type Operation,
  type OperationContextValue,
} from "@/lib/operation-context"

export function OperationProvider({ children }: { children: ReactNode }) {
  const [operation, setOperation] = useState<Operation>(idleOperation)
  const activeKeys = useRef(new Set<string>())
  const retryRef = useRef<(() => Promise<void>) | null>(null)

  const runOperation = useCallback(
    async function runOperation<T>(
      key: string,
      title: string,
      phase: string,
      task: () => Promise<T>,
      successMessage: (result: T) => string,
    ): Promise<T | undefined> {
      if (activeKeys.current.has(key)) return undefined
      activeKeys.current.add(key)
      setOperation({
        key,
        title,
        phase,
        state: "running",
        startedAt: new Date().toISOString(),
      })
      try {
        const result = await task()
        const summary = successMessage(result)
        setOperation({ key, title, phase: "已完成", state: "success", summary })
        retryRef.current = null
        toast.success(summary)
        return result
      } catch (error: unknown) {
        const message =
          error instanceof ApiError || error instanceof Error
            ? error.message
            : "操作失败，状态未改变"
        setOperation({
          key,
          title,
          phase: "未完成；请根据错误处理后重试",
          state: "failed",
          error: message,
          errorCode: error instanceof ApiError ? error.code : "request_failed",
          errorDetails: error instanceof ApiError ? error.details : undefined,
          retryable: true,
        })
        retryRef.current = async () => {
          await runOperation(key, title, phase, task, successMessage)
        }
        return undefined
      } finally {
        activeKeys.current.delete(key)
      }
    },
    [],
  )

  const value = useMemo<OperationContextValue>(
    () => ({
      operation,
      runOperation,
      dismissOperation: () => {
        retryRef.current = null
        setOperation(idleOperation)
      },
      retryOperation: async () => {
        if (retryRef.current) await retryRef.current()
      },
    }),
    [operation, runOperation],
  )

  return (
    <OperationContext.Provider value={value}>
      {children}
    </OperationContext.Provider>
  )
}
