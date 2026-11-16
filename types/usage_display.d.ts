export type Usage = {
  contextPercent: number | null
  limits: { kind: string; percentUsed: number; resetsAt: string | null }[]
}

declare module 'claude-code' {
  interface PluginState {
    nightflight: { usage: Usage | null; usageIsOn: boolean }
  }
}
