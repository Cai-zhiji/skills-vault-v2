import { spawnSync } from "node:child_process"

export const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm"

export function findPython() {
  const candidates = process.platform === "win32"
    ? [["py", ["-3"]], ["python", []], ["python3", []]]
    : [["python3", []], ["python", []]]
  for (const [command, prefix] of candidates) {
    const result = spawnSync(command, [...prefix, "--version"], { encoding: "utf8" })
    if (result.status === 0) return { command, prefix, version: `${result.stdout}${result.stderr}`.trim() }
  }
  return null
}

export function commandVersion(command, args = ["--version"]) {
  const result = spawnSync(command, args, { encoding: "utf8" })
  if (result.status !== 0) return null
  return `${result.stdout}${result.stderr}`.trim().split(/\r?\n/, 1)[0]
}

export function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || process.cwd(),
    env: options.env || process.env,
    stdio: options.capture ? "pipe" : "inherit",
    encoding: "utf8",
  })
  if (result.error) throw result.error
  if (result.status !== 0) {
    throw new Error(`${command} 执行失败（退出码 ${result.status ?? "unknown"}）`)
  }
  return result
}
