import { describe, expect, it } from 'vitest'
import { buildCopilotAnswer, getScoreLabel } from './demand'

describe('getScoreLabel', () => {
  it('labels very high scores', () => {
    expect(getScoreLabel(95)).toBe('매우 높음')
  })

  it('labels high scores', () => {
    expect(getScoreLabel(85)).toBe('높음')
  })

  it('labels normal scores', () => {
    expect(getScoreLabel(72)).toBe('보통')
  })

  it('labels low scores', () => {
    expect(getScoreLabel(50)).toBe('낮음')
  })
})

describe('buildCopilotAnswer', () => {
  it('includes the selected area data in the template answer', () => {
    const area = {
      area_name: '충장로 / 금남로',
      area_type_summary: '상업·관광 혼합 상권',
      predicted_score: 92,
      tourism_score: 74,
      tourist_spot_count: 8,
      event_count: 5,
      culture_count: 4,
      top_factors: ['주말 도심 쇼핑 유동인구 증가', '금남로 문화행사'],
      recommendations: ['판매 인력 보강', '테이크아웃 재고 확대'],
    }

    const answer = buildCopilotAnswer(area, '이번 주말 운영 전략은?')

    expect(answer).toContain(area.area_name)
    expect(answer).toContain(String(area.predicted_score))
    expect(answer).toContain(area.area_type_summary)
    expect(answer).toContain(`관광 점수 ${area.tourism_score}점`)
    expect(answer).toContain(`행사 ${area.event_count}건`)
    expect(answer).toContain(`문화시설 ${area.culture_count}곳`)
    area.top_factors.forEach((factor) => {
      expect(answer).toContain(factor)
    })
    area.recommendations.forEach((recommendation) => {
      expect(answer).toContain(recommendation)
    })
  })
})
