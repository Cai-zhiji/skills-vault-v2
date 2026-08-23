export interface ApiErrorPayload {
  code?: string
  error?: string
  details?: Record<string, unknown>
}

export class ApiError extends Error {
  readonly code: string
  readonly details: Record<string, unknown>
  readonly status: number

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.error || `请求失败（${status}）`)
    this.name = "ApiError"
    this.status = status
    this.code = payload.code || "request_failed"
    this.details = payload.details || {}
  }
}

async function parsePayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || ""
  if (!contentType.includes("application/json")) {
    return { error: await response.text() }
  }
  return response.json() as Promise<unknown>
}

function isErrorPayload(value: unknown): value is ApiErrorPayload {
  return typeof value === "object" && value !== null
}

export async function apiRequest<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const headers = new Headers(options?.headers)
  if (options?.body) headers.set("Content-Type", "application/json")
  const runtime = runtimeConfig()
  if (runtime?.token) headers.set("Authorization", `Bearer ${runtime.token}`)
  const requestUrl = runtime ? new URL(path, runtime.apiBase).toString() : path
  const response = await fetch(requestUrl, {
    ...options,
    headers,
  })
  const payload = await parsePayload(response)
  if (!response.ok) {
    throw new ApiError(
      response.status,
      isErrorPayload(payload) ? payload : { error: "请求失败" },
    )
  }
  return payload as T
}

export const api = {
  get<T>(path: string): Promise<T> {
    return apiRequest<T>(path)
  },
  post<T>(path: string, body: Record<string, unknown> = {}): Promise<T> {
    return apiRequest<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    })
  },
  put<T>(path: string, body: Record<string, unknown>): Promise<T> {
    return apiRequest<T>(path, {
      method: "PUT",
      body: JSON.stringify(body),
    })
  },
}
import { runtimeConfig } from "@/lib/runtime"
