import { describe, expect, it } from "vitest"

import { availableModes, selectionKey } from "@/lib/selection"

describe("selection helpers", () => {
  it("normalizes order and ignores explicit off entries", () => {
    expect(selectionKey({ "my/b": "codex", "my/a": "off" })).toBe(
      selectionKey({ "my/b": "codex" }),
    )
  })

  it("only offers modes supported by a Skill", () => {
    expect(availableModes(["codex"])).toEqual(["off", "codex"])
    expect(availableModes(["codex", "claude"])).toEqual([
      "off",
      "both",
      "codex",
      "claude",
    ])
    expect(availableModes(["codex", "claude", "lux"])).toEqual([
      "off",
      "all",
      "both",
      "codex-lux",
      "claude-lux",
      "codex",
      "claude",
      "lux",
    ])
  })
})
