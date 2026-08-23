import { invoke } from "@tauri-apps/api/core"

export interface DesktopRuntimeConfig {
  apiBase: string
  token: string
  startupId: string
  sidecarVersion: string
}

let desktopRuntime: DesktopRuntimeConfig | null = null
let startupError: Error | null = null

export function isTauriRuntime() {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window
}

export async function initializeRuntime() {
  if (!isTauriRuntime()) return null
  try {
    desktopRuntime = await invoke<DesktopRuntimeConfig>("runtime_config")
    return desktopRuntime
  } catch (error) {
    startupError = error instanceof Error ? error : new Error(String(error))
    return null
  }
}

export function runtimeConfig() {
  return desktopRuntime
}

export function runtimeStartupError() {
  return startupError
}
