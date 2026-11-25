import type { EngineInterface, Register } from 'claude-code'

const 브라우저도구 = 'mcp__Claude_Browser__preview_start'

async function 제품인가($: EngineInterface): Promise<boolean> {
  try {
    const r = await $.process.run(['bash', '-c', '. "$1" >/dev/null 2>&1 && nf_registered', '_', `${$.plugin.root}/bin/project-root.sh`], { timeoutMs: 10000 })
    return r.exitCode === 0
  } catch { return false }
}

async function 연다($: EngineInterface, 영어: boolean): Promise<string> {
  const 말 = (ko: string, en: string) => (영어 ? en : ko)
  if (!(await 제품인가($))) return 말('이 폴더는 야간비행에 등록되어 있지 않습니다.', 'This folder is not registered with Nightflight.')
  const r = await $.process.run(['python3', '-I', `${$.plugin.root}/bin/cockpit_server.py`, '.', '--뒤에서'], { timeoutMs: 20000 })
  const 주소 = (r.stdout || '').trim().split('\n')[0] || ''
  if (r.exitCode !== 0 || !/^http:\/\/127\.0\.0\.1:\d+\/$/.test(주소)) return 말('조종석 서버를 켜지 못했습니다. AI에게 말씀해 주십시오.', 'Could not start the cockpit. Please tell the AI.')
  try {
    const 답: any = await $.tool.call({ tool: 브라우저도구, url: 주소 } as any)
    if (!답 || 답.deny || 답.isError) return 말(`브라우저 칸을 열지 못했습니다. 주소: ${주소}`, `Could not open the browser pane. Address: ${주소}`)
    try { await $.tool.call({ tool: 'mcp__ccd_view__show_pane', pane: 'preview' } as any) } catch {}
    return 말(`조종석을 열었습니다: ${주소}`, `Opened the cockpit: ${주소}`)
  } catch {
    return 말(`조종석 서버는 켰지만 브라우저 칸을 열지 못했습니다. 클로드 데스크톱 앱에서 다시 입력해 주십시오. 주소: ${주소}`, `The cockpit is running but the browser pane did not open. Try again in the Claude desktop app. Address: ${주소}`)
  }
}

export async function 명령등록($: EngineInterface) {
  await $.command.register({ name: 'cockpit', description: '야간비행 조종석을 오른쪽 브라우저 칸에 엽니다 / Open the Nightflight cockpit in the right-hand browser pane' })
}

export const 조종석명령: Register = on => {
  on('command.run', { command: 'cockpit' }, async $ => {
    const 자리 = await $.env.get('NIGHTFLIGHT_HOME')
    const 집 = await $.env.get('HOME')
    let 영어 = false
    try { 영어 = (await $.fs.read(`${자리 || `${집}/.nightflight`}/language`)).trim().startsWith('en') } catch {}
    return { text: await 연다($, 영어) }
  })
}
