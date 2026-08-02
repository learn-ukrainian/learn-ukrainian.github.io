// Project-owned termination companion for the stock Entire 0.8.42 plugin.
// OpenCode 1.17.13 does not reliably emit server.instance.disposed for
// non-interactive `opencode run`, so the stock plugin can leave sessions idle.
import type { Plugin } from "@opencode-ai/plugin"

export const EntireExitTrap: Plugin = async () => {
  let currentSessionID: string | null = null

  function endCurrentSession() {
    if (!currentSessionID) return
    const sessionID = currentSessionID
    currentSessionID = null
    try {
      Bun.spawnSync(
        [
          "sh",
          "-c",
          "if ! command -v entire >/dev/null 2>&1; then exit 0; fi; exec entire hooks opencode session-end",
        ],
        {
          stdin: new TextEncoder().encode(JSON.stringify({ session_id: sessionID }) + "\n"),
          stdout: "ignore",
          stderr: "ignore",
        },
      )
    } catch {
      // Entire is optional; termination capture can never crash OpenCode.
    }
  }

  process.once("beforeExit", endCurrentSession)
  process.once("exit", endCurrentSession)

  return {
    event: async ({ event }) => {
      try {
        switch (event.type) {
          case "session.created": {
            const session = (event as any).properties?.info
            if (session?.id) currentSessionID = session.id
            break
          }
          case "message.updated": {
            const message = (event as any).properties?.info
            if (message?.sessionID) currentSessionID = message.sessionID
            break
          }
          case "session.deleted":
          case "server.instance.disposed":
            endCurrentSession()
            break
        }
      } catch {
        // Lifecycle observation is optional and fail-open.
      }
    },
  }
}
