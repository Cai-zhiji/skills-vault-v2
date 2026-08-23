import { spawn } from "node:child_process"
import process from "node:process"

import { commandVersion, findPython, npmCommand } from "./process-utils.mjs"

const mode = process.argv[2] || "desktop"
const python = findPython()

if (!python) {
  process.stderr.write("未找到 Python 3。开发服务需要 Python，但最终安装包不需要。\n")
  process.exit(1)
}

if (mode === "desktop" && (!commandVersion("rustc") || !commandVersion("cargo"))) {
  process.stderr.write([
    "未找到 Rust/Cargo，暂时无法启动 Tauri 桌面开发模式。",
    "请按 https://rustup.rs 安装 Rust 1.77.2 或更高版本，然后重新运行 npm run dev。",
    "你仍可立即运行 npm run dev:web 使用浏览器开发模式。",
    "",
  ].join("\n"))
  process.exit(1)
}

const children = []
let stopping = false

function start(command, args) {
  const child = spawn(command, args, { cwd: process.cwd(), env: process.env, stdio: "inherit" })
  children.push(child)
  child.on("exit", (code, signal) => {
    if (stopping) return
    stopping = true
    for (const other of children) {
      if (other !== child && !other.killed) other.kill()
    }
    process.exitCode = signal ? 1 : (code ?? 1)
  })
  return child
}

function stop() {
  if (stopping) return
  stopping = true
  for (const child of children) {
    if (!child.killed) child.kill("SIGTERM")
  }
}

process.on("SIGINT", stop)
process.on("SIGTERM", stop)

if (mode === "desktop") {
  process.stdout.write("启动 Skills Vault 桌面开发模式…\n")
  start(npmCommand, ["run", "tauri", "--", "dev"])
} else if (mode === "web") {
  process.stdout.write("启动 Skills Vault 浏览器开发模式…\n")
  start(python.command, [...python.prefix, "server/http_server.py", "--port", "8766"])
  start(npmCommand, ["--prefix", "app", "run", "dev", "--", "--host", "127.0.0.1"])
} else {
  process.stderr.write(`未知开发模式：${mode}\n`)
  process.exit(1)
}
