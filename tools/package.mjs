import { createHash } from "node:crypto"
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs"
import os from "node:os"
import path from "node:path"

import { commandVersion, findPython, npmCommand, run } from "./process-utils.mjs"

process.on("uncaughtException", (error) => {
  process.stderr.write(`打包未完成：${error.message}\n`)
  process.exit(1)
})

const diagnoseOnly = process.argv.includes("--diagnose")
const project = process.cwd()
const manifest = JSON.parse(readFileSync(path.join(project, "package.json"), "utf8"))
const python = findPython()
const diagnostics = {
  node: process.version,
  npm: commandVersion(npmCommand),
  python: python?.version || null,
  rustc: commandVersion("rustc"),
  cargo: commandVersion("cargo"),
  platform: process.platform,
  architecture: process.arch,
  version: manifest.version,
}

process.stdout.write(`${JSON.stringify(diagnostics, null, 2)}\n`)
if (diagnoseOnly) process.exit(0)

const missing = []
if (!python) missing.push("Python 3")
if (!diagnostics.rustc || !diagnostics.cargo) missing.push("Rust/Cargo（https://rustup.rs）")
if (missing.length) {
  throw new Error(`打包工具链不完整：${missing.join("、")}。安装后可重新运行 npm run package。`)
}

const buildVenv = path.join(project, ".venv-build")
const venvPython = process.platform === "win32"
  ? path.join(buildVenv, "Scripts", "python.exe")
  : path.join(buildVenv, "bin", "python")
if (!existsSync(venvPython)) {
  run(python.command, [...python.prefix, "-m", "venv", buildVenv])
}
run(venvPython, ["-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements-build.txt"])
run(process.execPath, ["tools/test-all.mjs"])
run(venvPython, ["tools/build-sidecar.py"])
run(npmCommand, ["run", "tauri", "--", "build"])

const bundleRoot = path.join(project, "src-tauri", "target", "release", "bundle")
if (!existsSync(bundleRoot)) throw new Error("Tauri 未生成 bundle 目录")
const platformName = process.platform === "darwin" ? "macos" : process.platform === "win32" ? "windows" : "linux"
const outputRoot = path.join(project, "dist", "packages", manifest.version, `${platformName}-${process.arch}`)
mkdirSync(outputRoot, { recursive: true })

function filesUnder(root) {
  return readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    const item = path.join(root, entry.name)
    return entry.isDirectory() ? filesUnder(item) : [item]
  })
}

for (const entry of readdirSync(bundleRoot, { withFileTypes: true })) {
  cpSync(path.join(bundleRoot, entry.name), path.join(outputRoot, entry.name), { recursive: true })
}
const checksums = {}
for (const file of filesUnder(outputRoot)) {
  if (file.endsWith("checksums.json") || file.endsWith("build-metadata.json")) continue
  checksums[path.relative(outputRoot, file).split(path.sep).join("/")] = createHash("sha256").update(readFileSync(file)).digest("hex")
}
writeFileSync(path.join(outputRoot, "checksums.json"), `${JSON.stringify(checksums, null, 2)}\n`)
writeFileSync(path.join(outputRoot, "build-metadata.json"), `${JSON.stringify({
  ...diagnostics,
  builtAt: new Date().toISOString(),
  hostname: os.hostname(),
  signed: false,
  distribution: "internal/testing",
}, null, 2)}\n`)
process.stdout.write(`安装包已输出到 ${outputRoot}\n`)
