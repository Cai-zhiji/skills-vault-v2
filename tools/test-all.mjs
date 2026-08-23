import { findPython, npmCommand, run } from "./process-utils.mjs"

const python = findPython()
if (!python) throw new Error("未找到 Python 3")

run(npmCommand, ["--prefix", "app", "run", "typecheck"])
run(npmCommand, ["--prefix", "app", "run", "lint"])
run(npmCommand, ["--prefix", "app", "test", "--", "--run"])
run(npmCommand, ["--prefix", "app", "run", "build"])
run(python.command, [...python.prefix, "-m", "unittest", "discover", "-s", "server", "-p", "test_*.py"], {
  env: { ...process.env, PYTHONPATH: "server" },
})
process.stdout.write("全部检查已通过。\n")
