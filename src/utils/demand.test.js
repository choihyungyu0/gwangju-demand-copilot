import { describe, expect, it } from 'vitest'
import {
  buildCopilotAnswer,
  buildScoreExplanation,
  getScoreBadgeText,
  getScoreLabel,
} from './demand'

const area = {
  area_name: '충장로 / 금남로',
  area_type_summary: '상업·관광 혼합 상권',
  predicted_score: 78,
  commercial_score: 100,
  tourism_component_score: 74,
  visitor_component_score: 92,
  event_component_score: 33,
  weather_component_score: 58,
  score_level: '높음',
  score_summary:
    '충장로 / 금남로의 최종 수요예측 점수는 78점이며 높음 수준입니다.',
  score_reason_1: '상권 밀집도가 높아 기본 수요가 높습니다.',
  score_reason_2: '관광/행사 영향으로 주말 방문 가능성이 높습니다.',
  score_reason_3: '방문자 증가 추세가 있어 수요 상승 가능성이 있습니다.',
  risk_summary: '비 예보가 있어 실내 유입 동선과 우천 안내를 준비해야 합니다.',
  recommended_action_1: '기본 인력은 유지하고 점심·저녁 피크에 탄력 배치하세요.',
  recommended_action_2: '우천 안내, 실내 체류 상품, 배달 노출을 강화하세요.',
  recommended_action_3: '방문자 증가에 맞춰 인기 품목 재고를 선제적으로 확보하세요.',
  tourism_score: 74,
  tourist_spot_count: 8,
  event_count: 5,
  culture_count: 4,
  visitor_count_gu: 172000,
  visitor_growth: 14.5,
  visitor_score: 92,
  rain_flag: 1,
  weather_score: 58,
  weather_risk_level: '중간',
}

describe('getScoreLabel', () => {
  it('labels very high scores', () => {
    expect(getScoreLabel(90)).toBe('매우 높음')
  })

  it('labels high scores', () => {
    expect(getScoreLabel(78)).toBe('높음')
  })

  it('labels normal scores', () => {
    expect(getScoreLabel(60)).toBe('보통')
  })

  it('labels low scores', () => {
    expect(getScoreLabel(45)).toBe('낮음')
  })
})

describe('getScoreBadgeText', () => {
  it('returns an owner-friendly operating band', () => {
    expect(getScoreBadgeText(78)).toBe('성장 대응 구간')
  })
})

describe('buildScoreExplanation', () => {
  it('summarizes score breakdown, reasons, risk, and actions', () => {
    const explanation = buildScoreExplanation(area)

    expect(explanation).toContain(area.score_summary)
    expect(explanation).toContain('상권 100점')
    expect(explanation).toContain('관광 74점')
    expect(explanation).toContain(area.score_reason_1)
    expect(explanation).toContain(area.risk_summary)
    expect(explanation).toContain(area.recommended_action_1)
  })
})

describe('buildCopilotAnswer', () => {
  it('explains the final score and owner actions', () => {
    const answer = buildCopilotAnswer(area, '이번 주말 운영 전략은?')

    expect(answer).toContain(area.area_name)
    expect(answer).toContain('최종 수요예측 점수는 78점')
    expect(answer).toContain(area.score_reason_1)
    expect(answer).toContain('관광 74점')
    expect(answer).toContain('방문 수요는 92점')
    expect(answer).toContain('날씨 점수는 58점')
    expect(answer).toContain(area.risk_summary)
    expect(answer).toContain(area.recommended_action_2)
  })
})
