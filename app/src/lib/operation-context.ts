import { createContext, useContext } from "react"

export type OperationState = "idle" | "running" | "success" | "failed"

export interface Operation {
  key: string
  title: string
  phase: string
  state: OperationState
  summary?: string
  error?: string
  startedAt?: string
  errorCode?: string
  errorDetails?: Record<string, unknown>
  retryable?: boolean
}

export interface OperationContextValue {
  operation: Operation
  runOperation: <T>(
    key: string,
    title: string,
    phase: string,
    task: () => Promise<T>,
    successMessage: (result: T) => string,
  ) => Promise<T | undefined>
  dismissOperation: () => void
  retryOperation: () => Promise<void>
}

export const idleOperation: Operation = {
  key: "idle",
  title: "等待操作",
  phase: "所有写操作都会在这里持续显示",
  state: "idle",
}

export const OperationContext = createContext<OperationContextValue | null>(null)

export function useOperation(): OperationContextValue {
  const value = useContext(OperationContext)
  if (!value) throw new Error("useOperation must be used inside OperationProvider")
  return value
}
