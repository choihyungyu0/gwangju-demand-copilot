export function getScoreLabel(score) {
  if (score >= 90) return '매우 높음'
  if (score >= 80) return '높음'
  if (score >= 60) return '보통'
  return '낮음'
}

export function getRiskClass(riskLevel) {
  const riskMap = {
    낮음: 'risk-low',
    중간: 'risk-medium',
    높음: 'risk-high',
  }

  return riskMap[riskLevel] ?? 'risk-unknown'
}

function toTextList(items) {
  return Array.isArray(items) ? items.join(', ') : String(items ?? '')
}

export function buildCopilotAnswer(area, question = '') {
  if (!area) {
    return '선택된 지역 데이터가 없습니다.'
  }

  const factors = toTextList(area.top_factors)
  const recommendations = toTextList(area.recommendations)
  const areaType = area.area_type_summary ?? '상권 유형 정보 없음'
  const tourismScore = area.tourism_score ?? 0
  const touristSpotCount = area.tourist_spot_count ?? 0
  const eventCount = area.event_count ?? 0
  const cultureCount = area.culture_count ?? 0
  const normalizedQuestion = question.trim()
  const questionContext = normalizedQuestion
    ? `질문: ${normalizedQuestion}`
    : '질문: 현재 선택 지역의 운영 대응 방향'

  return [
    `${questionContext}`,
    `${area.area_name}의 예측 수요 점수는 ${area.predicted_score}점(${getScoreLabel(area.predicted_score)})입니다.`,
    `상권 유형은 ${areaType}이며 관광 점수 ${tourismScore}점, 관광지 ${touristSpotCount}곳, 행사 ${eventCount}건, 문화시설 ${cultureCount}곳입니다.`,
    `주요 요인은 ${factors}입니다.`,
    `추천 실행은 ${recommendations}입니다.`,
    `현재는 mock 데이터 기반 답변이며 외부 AI API는 호출하지 않습니다.`,
  ].join('\n')
}
