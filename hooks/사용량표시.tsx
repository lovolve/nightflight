import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Usage } from '../types/사용량표시'

// 앱의 입력창 위에 대화 용량과 한도를 한 줄로 표시한다. 터미널은 상태줄이 같은 값을 표시한다.
// 사용자가 켜겠다고 답했을 때만 표시한다(`bin/상태줄켜기.py 켜기` 가 표시를 남긴다).
const usage = atom({ plugin: 'nightflight', key: 'usage' } as const, null)
const isOn = atom({ plugin: 'nightflight', key: 'usageIsOn' } as const, false)

const 한도이름: Record<string, string> = { five_hour: '5시간 한도', seven_day: '7일 한도' }

function 남은시간(끝: string | null, 지금: number): string | null {
  const 때 = 끝 ? Date.parse(끝) : NaN
  if (Number.isNaN(때)) return null
  const 분 = Math.max(0, Math.floor((때 - 지금) / 60000))
  if (분 >= 1440) return `${Math.floor(분 / 1440)}일 뒤 초기화`
  if (분 >= 60) return `${Math.floor(분 / 60)}시간 뒤 초기화`
  return `${분}분 뒤 초기화`
}

export function 줄(값: Usage, 지금: number): string {
  const 칸: string[] = []
  if (값.contextPercent !== null) 칸.push(`이 대화 용량 ${Math.round(값.contextPercent)}%`)
  for (const 한도 of 값.limits) {
    const 이름 = 한도이름[한도.kind]
    if (!이름) continue
    const 남음 = 남은시간(한도.resetsAt, 지금)
    칸.push(`${이름} ${Math.round(한도.percentUsed)}% 사용${남음 ? ` (${남음})` : ''}`)
  }
  return 칸.join(' · ')
}

function 값으로(e: {
  context: { percent?: number }
  rateLimits: { kind: string; percentUsed: number; resetsAt?: string }[]
}): Usage {
  return {
    contextPercent: e.context.percent ?? null,
    limits: e.rateLimits.map(한도 => ({
      kind: 한도.kind,
      percentUsed: 한도.percentUsed,
      resetsAt: 한도.resetsAt ?? null,
    })),
  }
}

async function 켬확인($: EngineInterface) {
  const 자리 = await $.env.get('NIGHTFLIGHT_HOME')
  const 집 = await $.env.get('HOME')
  const 표시 = `${자리 || `${집}/.nightflight`}/앱표시켬`
  const 켬 = await $.fs.exists(표시)
  await update($, isOn, () => 켬)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const 답 = await next(e)
    await 켬확인($)
    const 지금값 = await $.session.usage()
    await update($, usage, () => 값으로(지금값))
    return 답
  })

  on('session.measure', async ($, e, next) => {
    await 켬확인($)
    await update($, usage, () => 값으로(e))
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const 값 = await read($, usage)
    const 켬 = await read($, isOn)
    if (e.surface !== 'desktop' || e.props.hasSurvey || !켬 || 값 === null) return next(e)
    const 글 = 줄(값, await $.clock.now())
    if (!글) return next(e)

    const { Box, Text } = $.ui.resolve(e)
    const 곧참 = (값.contextPercent ?? 0) >= 85

    return (
      <Box>
        <Text dimColor={!곧참} weight={곧참 ? 'semibold' : 'regular'} size="footnote">
          {글}
          {곧참 ? ' — 곧 새 대화로 시작해야 합니다' : ''}
        </Text>
      </Box>
    )
  })
}
