export function getScoreLabel(score) {
  const value = Number(score) || 0
  if (value >= 85) return '매우 높음'
  if (value >= 70) return '높음'
  if (value >= 55) return '보통'
  return '낮음'
}

export function getScoreBadgeText(score) {
  const value = Number(score) || 0
  if (value >= 85) return '수요 집중 구간'
  if (value >= 70) return '성장 대응 구간'
  if (value >= 55) return '기본 운영 구간'
  return '보수 운영 구간'
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

function numberValue(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

function scoreReasons(area) {
  return [
    area.score_reason_1,
    area.score_reason_2,
    area.score_reason_3,
  ].filter(Boolean)
}

function recommendedActions(area) {
  return [
    area.recommended_action_1,
    area.recommended_action_2,
    area.recommended_action_3,
  ].filter(Boolean)
}

function modelFeatures(area) {
  return String(area.top_model_features ?? '')
    .split(',')
    .map((feature) => feature.trim())
    .filter(Boolean)
}

function hasModelMetrics(area) {
  return area.model_mae !== undefined && area.model_mae !== null && area.model_mae !== ''
}

export function buildScoreExplanation(area) {
  if (!area) {
    return '선택된 지역 데이터가 없습니다.'
  }

  const predictedScore = numberValue(area.predicted_score)
  const scoreLevel = area.score_level ?? getScoreLabel(predictedScore)
  const reasons = scoreReasons(area)
  const actions = recommendedActions(area)
  const strongestReason = reasons[0] ?? '상권, 방문, 관광, 날씨 요인을 함께 반영했습니다.'
  const actionText = actions.length > 0 ? toTextList(actions) : '기본 운영을 유지하세요.'
  const modelText = hasModelMetrics(area)
    ? `AI 모델은 RandomForestRegressor이며 MAE ${area.model_mae}, RMSE ${area.model_rmse}, R2 ${area.model_r2}입니다. 주요 영향 변수는 ${toTextList(modelFeatures(area))}입니다.`
    : 'AI 모델 학습 결과는 아직 생성되지 않았습니다.'

  return [
    area.score_summary ??
      `${area.area_name}의 최종 수요예측 점수는 ${predictedScore}점이며 ${scoreLevel} 수준입니다.`,
    `점수 구성은 상권 ${numberValue(area.commercial_score)}점, 관광 ${numberValue(area.tourism_component_score)}점, 방문 수요 ${numberValue(area.visitor_component_score)}점, 행사 영향 ${numberValue(area.event_component_score)}점, 날씨 ${numberValue(area.weather_component_score)}점입니다.`,
    `가장 큰 근거는 "${strongestReason}" 입니다.`,
    `리스크 요약: ${area.risk_summary ?? '특이 리스크 정보가 없습니다.'}`,
    modelText,
    `추천 행동: ${actionText}`,
  ].join('\n')
}

export function buildCopilotAnswer(area, question = '') {
  if (!area) {
    return '선택된 지역 데이터가 없습니다.'
  }

  const predictedScore = numberValue(area.predicted_score)
  const reasons = scoreReasons(area)
  const actions = recommendedActions(area)
  const actionText = actions.length > 0 ? toTextList(actions) : '기본 운영을 유지하세요'
  const topFeatures = modelFeatures(area)
  const modelInsight = hasModelMetrics(area)
    ? `모델 기준 주요 영향 변수는 ${toTextList(topFeatures)}입니다.`
    : '모델 학습 결과는 아직 생성되지 않아 rule-based MVP 점수를 중심으로 설명합니다.'
  const strongestReason = reasons[0] ?? '복합 수요 요인이 반영되었습니다.'
  const tourismScore = numberValue(area.tourism_component_score, area.tourism_score ?? 0)
  const visitorScore = numberValue(area.visitor_component_score, area.visitor_score ?? 0)
  const weatherScore = numberValue(area.weather_component_score, area.weather_score ?? 0)
  const eventScore = numberValue(area.event_component_score)
  const visitorGrowth = numberValue(area.visitor_growth)
  const visitorGrowthText = `${visitorGrowth > 0 ? '+' : ''}${visitorGrowth}%`
  const rainFlag = numberValue(area.rain_flag)
  const weatherRiskLevel = area.weather_risk_level ?? '정보 없음'
  const weatherImpact =
    rainFlag === 1 || weatherRiskLevel === '높음'
      ? '강수 가능성이 있어 야외 홍보보다 실내 유입 전략과 우천 안내가 중요합니다.'
      : '날씨 부담이 낮아 현장 홍보와 보행 유입 전략을 함께 가져갈 수 있습니다.'
  const normalizedQuestion = question.trim()
  const questionContext = normalizedQuestion
    ? `질문: ${normalizedQuestion}`
    : '질문: 현재 선택 지역의 운영 대응 방향'

  return [
    questionContext,
    `${area.area_name}의 최종 수요예측 점수는 ${predictedScore}점(${area.score_level ?? getScoreLabel(predictedScore)}, ${getScoreBadgeText(predictedScore)})입니다.`,
    `가장 강한 근거는 ${strongestReason}`,
    `관광/행사 영향은 관광 ${tourismScore}점, 행사 ${eventScore}점으로 반영됐고 방문 수요는 ${visitorScore}점, 방문자 증가율은 ${visitorGrowthText}입니다.`,
    `날씨 점수는 ${weatherScore}점이며 리스크는 ${weatherRiskLevel}입니다. ${weatherImpact}`,
    `${modelInsight}`,
    `리스크 요약: ${area.risk_summary ?? '특이 리스크 정보가 없습니다.'}`,
    `추천 행동은 ${actionText}입니다.`,
    '현재는 MVP scoring formula와 mock/공공데이터 feature 기반 답변이며 외부 AI API는 호출하지 않습니다.',
  ].join('\n')
}
