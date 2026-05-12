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
  const visitorCount = area.visitor_count_gu ?? 0
  const visitorGrowth = area.visitor_growth ?? 0
  const visitorScore = area.visitor_score ?? 0
  const visitorSummary = area.visitor_summary ?? '방문 수요 정보 없음'
  const visitorGrowthText = `${visitorGrowth > 0 ? '+' : ''}${visitorGrowth}%`
  const temp = area.temp ?? 0
  const rainMm = area.rain_mm ?? 0
  const rainFlag = area.rain_flag ?? 0
  const weatherScore = area.weather_score ?? 0
  const weatherRiskLevel = area.weather_risk_level ?? '정보 없음'
  const weatherSummary = area.weather_summary ?? '날씨 정보 없음'
  const rainText = Number(rainFlag) === 1 ? '강수 있음' : '강수 영향 낮음'
  const visitorTrend =
    visitorGrowth > 0
      ? '방문자 증가 추세가 있어 수요 상승 가능성이 있습니다.'
      : visitorGrowth < 0
        ? '방문자 감소 가능성이 있어 보수적인 운영이 필요합니다.'
        : '방문자 흐름은 안정적인 편입니다.'
  const weatherAction =
    Number(rainFlag) === 1 || weatherRiskLevel === '높음'
      ? '방문 수요가 있더라도 야외 홍보보다는 실내 유입 전략과 우천 안내를 준비하는 것이 좋습니다.'
      : '날씨가 양호해 야외 동선 안내와 현장 프로모션을 함께 운영하기 좋습니다.'
  const normalizedQuestion = question.trim()
  const questionContext = normalizedQuestion
    ? `질문: ${normalizedQuestion}`
    : '질문: 현재 선택 지역의 운영 대응 방향'

  return [
    `${questionContext}`,
    `${area.area_name}의 예측 수요 점수는 ${area.predicted_score}점(${getScoreLabel(area.predicted_score)})입니다.`,
    `상권 유형은 ${areaType}이며 관광 점수 ${tourismScore}점, 관광지 ${touristSpotCount}곳, 행사 ${eventCount}건, 문화시설 ${cultureCount}곳입니다.`,
    `방문 수요 점수는 ${visitorScore}점이고 방문자 수는 ${visitorCount.toLocaleString('ko-KR')}명, 증가율은 ${visitorGrowthText}입니다. ${visitorTrend}`,
    `방문 수요 요약: ${visitorSummary}`,
    `날씨는 ${Number(temp).toFixed(1)}℃, 강수량 ${Number(rainMm).toFixed(1)}mm, ${rainText}입니다. 날씨 점수는 ${weatherScore}점이고 리스크는 ${weatherRiskLevel}입니다. ${weatherSummary}`,
    `${weatherAction}`,
    `주요 요인은 ${factors}입니다.`,
    `추천 실행은 ${recommendations}입니다.`,
    `현재는 mock 데이터 기반 답변이며 외부 AI API는 호출하지 않습니다.`,
  ].join('\n')
}
