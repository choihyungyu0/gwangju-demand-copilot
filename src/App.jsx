import { useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  buildCopilotAnswer,
  getRiskClass,
  getScoreBadgeText,
  getScoreLabel,
} from './utils/demand'

function App() {
  const [areas, setAreas] = useState([])
  const [selectedAreaId, setSelectedAreaId] = useState('')
  const [question, setQuestion] = useState('이번 주말 인력과 재고를 어떻게 준비할까요?')
  const [copilotAnswer, setCopilotAnswer] = useState('')
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let ignore = false

    fetch('/predictions.json')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to load prediction data')
        }
        return response.json()
      })
      .then((data) => {
        if (ignore) return
        setAreas(data)
        setSelectedAreaId(data[0]?.area_id ?? '')
      })
      .catch(() => {
        if (!ignore) {
          setLoadError('예측 데이터를 불러오지 못했습니다.')
        }
      })

    return () => {
      ignore = true
    }
  }, [])

  const selectedArea = useMemo(
    () => areas.find((area) => area.area_id === selectedAreaId) ?? areas[0],
    [areas, selectedAreaId],
  )

  useEffect(() => {
    if (selectedArea) {
      setCopilotAnswer(buildCopilotAnswer(selectedArea, question))
    }
  }, [selectedArea])

  function handleGenerateAnswer() {
    setCopilotAnswer(buildCopilotAnswer(selectedArea, question))
  }

  if (loadError) {
    return (
      <main className="app-shell state-shell">
        <h1>광주 상권·관광 수요예측 코파일럿</h1>
        <p>{loadError}</p>
      </main>
    )
  }

  if (!selectedArea) {
    return (
      <main className="app-shell state-shell">
        <h1>광주 상권·관광 수요예측 코파일럿</h1>
        <p>예측 데이터를 준비하고 있습니다.</p>
      </main>
    )
  }

  const areaTypeSummary = selectedArea.area_type_summary ?? '상권 유형 정보 없음'
  const tourismScore = selectedArea.tourism_score ?? 0
  const touristSpotCount = selectedArea.tourist_spot_count ?? 0
  const eventCount = selectedArea.event_count ?? 0
  const cultureCount = selectedArea.culture_count ?? 0
  const visitorCount = selectedArea.visitor_count_gu ?? 0
  const visitorGrowth = selectedArea.visitor_growth ?? 0
  const visitorScore = selectedArea.visitor_score ?? 0
  const visitorSummary = selectedArea.visitor_summary ?? '방문 수요 정보 없음'
  const visitorGrowthText = `${visitorGrowth > 0 ? '+' : ''}${visitorGrowth}%`
  const temp = selectedArea.temp ?? 0
  const rainMm = selectedArea.rain_mm ?? 0
  const rainFlag = selectedArea.rain_flag ?? 0
  const weatherScore = selectedArea.weather_score ?? 0
  const weatherRiskLevel = selectedArea.weather_risk_level ?? '정보 없음'
  const weatherSummary = selectedArea.weather_summary ?? '날씨 정보 없음'
  const tempText = `${Number(temp).toFixed(1)}℃`
  const rainMmText = `${Number(rainMm).toFixed(1)}mm`
  const rainText = Number(rainFlag) === 1 ? '예' : '아니오'
  const scoreLevel = selectedArea.score_level ?? getScoreLabel(selectedArea.predicted_score)
  const scoreBadgeText = getScoreBadgeText(selectedArea.predicted_score)
  const scoreSummary = selectedArea.score_summary ?? selectedArea.summary
  const commercialScore = selectedArea.commercial_score ?? 0
  const tourismComponentScore = selectedArea.tourism_component_score ?? tourismScore
  const visitorComponentScore = selectedArea.visitor_component_score ?? visitorScore
  const eventComponentScore = selectedArea.event_component_score ?? 0
  const weatherComponentScore = selectedArea.weather_component_score ?? weatherScore
  const scoreReasons = [
    selectedArea.score_reason_1,
    selectedArea.score_reason_2,
    selectedArea.score_reason_3,
  ].filter(Boolean)
  const riskSummary = selectedArea.risk_summary ?? '리스크 정보 없음'
  const recommendedActions = [
    selectedArea.recommended_action_1,
    selectedArea.recommended_action_2,
    selectedArea.recommended_action_3,
  ].filter(Boolean)
  const modelMetricsAvailable =
    selectedArea.model_mae !== undefined &&
    selectedArea.model_mae !== null &&
    selectedArea.model_mae !== ''
  const topModelFeatures = String(selectedArea.top_model_features ?? '')
    .split(',')
    .map((feature) => feature.trim())
    .filter(Boolean)

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Public Data AI Competition MVP</p>
          <h1>광주 상권·관광 수요예측 코파일럿</h1>
          <p className="subtitle">
            공공데이터와 AI 기반 수요예측을 가정한 광주 상권·관광 운영 의사결정
            프로토타입입니다.
          </p>
        </div>
        <div className="status-strip" aria-label="현재 MVP 상태">
          <span>Mock data</span>
          <span>Frontend only</span>
          <span>No external API</span>
        </div>
      </header>

      <div className="dashboard-grid">
        <aside className="area-panel" aria-label="광주 지역 목록">
          <div className="panel-heading">
            <span>지역 선택</span>
            <strong>{areas.length}</strong>
          </div>
          <div className="area-list">
            {areas.map((area) => (
              <button
                aria-pressed={area.area_id === selectedArea.area_id}
                className={`area-button ${
                  area.area_id === selectedArea.area_id ? 'active' : ''
                }`}
                key={area.area_id}
                onClick={() => setSelectedAreaId(area.area_id)}
                type="button"
              >
                <span className="area-id">{area.area_id}</span>
                <span className="area-name">{area.area_name}</span>
                <span className="area-meta">
                  {area.district} · {area.risk_level} 리스크
                </span>
              </button>
            ))}
          </div>
        </aside>

        <section className="detail-card" aria-labelledby="selected-area-title">
          <div className="detail-header">
            <div>
              <span className="area-code">{selectedArea.area_id}</span>
              <h2 id="selected-area-title">{selectedArea.area_name}</h2>
              <p>{selectedArea.district}</p>
            </div>
            <span className={`risk-pill ${getRiskClass(selectedArea.risk_level)}`}>
              {selectedArea.risk_level} 리스크
            </span>
          </div>

          <div className="metric-row">
            <div className="metric-card score-metric">
              <span>최종 수요예측 점수</span>
              <strong>{selectedArea.predicted_score}</strong>
              <em>{scoreBadgeText}</em>
            </div>
            <div className="metric-card">
              <span>점수 등급</span>
              <strong>{scoreLevel}</strong>
              <em>최근 평균 대비 {selectedArea.change_vs_avg}</em>
            </div>
          </div>

          <p className="summary">{scoreSummary}</p>

          <section className="score-section" aria-labelledby="score-title">
            <div>
              <h3 id="score-title">점수 구성</h3>
              <p>최종 점수는 5개 구성 요소의 가중합으로 계산됩니다.</p>
            </div>
            <dl className="score-components" aria-label="수요예측 점수 구성">
              <div>
                <dt>상권 점수</dt>
                <dd>{commercialScore}</dd>
              </div>
              <div>
                <dt>관광 점수</dt>
                <dd>{tourismComponentScore}</dd>
              </div>
              <div>
                <dt>방문 수요 점수</dt>
                <dd>{visitorComponentScore}</dd>
              </div>
              <div>
                <dt>행사 영향 점수</dt>
                <dd>{eventComponentScore}</dd>
              </div>
              <div>
                <dt>날씨 점수</dt>
                <dd>{weatherComponentScore}</dd>
              </div>
            </dl>
          </section>

          <div className="score-explain-grid">
            <section>
              <h3>예측 근거 3개</h3>
              <ol>
                {scoreReasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ol>
            </section>
            <section>
              <h3>리스크 요약</h3>
              <p className="risk-summary">{riskSummary}</p>
              <h3 className="subsection-title">추천 행동 3개</h3>
              <ol>
                {recommendedActions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ol>
            </section>
          </div>

          <section className="tourism-section" aria-labelledby="tourism-title">
            <div>
              <h3 id="tourism-title">상권 유형 요약</h3>
              <p>{areaTypeSummary}</p>
            </div>
            <dl className="tourism-metrics" aria-label="관광 및 이벤트 지표">
              <div>
                <dt>관광 점수</dt>
                <dd>{tourismScore}</dd>
              </div>
              <div>
                <dt>관광지 수</dt>
                <dd>{touristSpotCount}</dd>
              </div>
              <div>
                <dt>행사 수</dt>
                <dd>{eventCount}</dd>
              </div>
              <div>
                <dt>문화시설 수</dt>
                <dd>{cultureCount}</dd>
              </div>
            </dl>
          </section>

          <section className="visitor-section" aria-labelledby="visitor-title">
            <div>
              <h3 id="visitor-title">방문 수요 요약</h3>
              <p>{visitorSummary}</p>
            </div>
            <dl className="visitor-metrics" aria-label="방문 수요 지표">
              <div>
                <dt>방문자 수</dt>
                <dd>{visitorCount.toLocaleString('ko-KR')}</dd>
              </div>
              <div>
                <dt>방문자 증가율</dt>
                <dd>{visitorGrowthText}</dd>
              </div>
              <div>
                <dt>방문 수요 점수</dt>
                <dd>{visitorScore}</dd>
              </div>
            </dl>
          </section>

          <section className="weather-section" aria-labelledby="weather-title">
            <div>
              <h3 id="weather-title">날씨 리스크 요약</h3>
              <p>{weatherSummary}</p>
            </div>
            <dl className="weather-metrics" aria-label="날씨 리스크 지표">
              <div>
                <dt>기온</dt>
                <dd>{tempText}</dd>
              </div>
              <div>
                <dt>강수량</dt>
                <dd>{rainMmText}</dd>
              </div>
              <div>
                <dt>비 여부</dt>
                <dd>{rainText}</dd>
              </div>
              <div>
                <dt>날씨 점수</dt>
                <dd>{weatherScore}</dd>
              </div>
              <div>
                <dt>날씨 리스크</dt>
                <dd>{weatherRiskLevel}</dd>
              </div>
            </dl>
          </section>

          <section className="model-section" aria-labelledby="model-title">
            <div>
              <h3 id="model-title">AI 모델 정보</h3>
              <p>
                {modelMetricsAvailable
                  ? '일별 학습 데이터로 만든 설명 가능한 MVP 모델입니다.'
                  : '모델 학습 결과는 아직 생성되지 않았습니다.'}
              </p>
            </div>
            {modelMetricsAvailable ? (
              <div className="model-content">
                <dl className="model-metrics" aria-label="AI 모델 성능 지표">
                  <div>
                    <dt>모델 방식</dt>
                    <dd>RandomForestRegressor</dd>
                  </div>
                  <div>
                    <dt>MAE</dt>
                    <dd>{selectedArea.model_mae}</dd>
                  </div>
                  <div>
                    <dt>RMSE</dt>
                    <dd>{selectedArea.model_rmse}</dd>
                  </div>
                  <div>
                    <dt>R2</dt>
                    <dd>{selectedArea.model_r2}</dd>
                  </div>
                </dl>
                <div className="model-features">
                  <strong>주요 영향 변수 TOP 5</strong>
                  <ol>
                    {topModelFeatures.map((feature) => (
                      <li key={feature}>{feature}</li>
                    ))}
                  </ol>
                </div>
              </div>
            ) : (
              <p className="model-empty">
                학습 스크립트 실행 후 MAE/RMSE/R2와 주요 변수가 표시됩니다.
              </p>
            )}
          </section>

          <section className="forecast-section">
            <h3>7일 수요 전망</h3>
            <ol className="forecast-list">
              {selectedArea.forecast.map((day) => (
                <li key={day.day ?? day.date}>
                  <span className="forecast-day">{day.day ?? day.date.slice(5)}</span>
                  <div className="forecast-bar" aria-hidden="true">
                    <span style={{ width: `${day.score}%` }} />
                  </div>
                  <strong>{day.score}</strong>
                </li>
              ))}
            </ol>
          </section>
        </section>

        <aside className="copilot-panel" aria-label="AI 코파일럿 패널">
          <div className="panel-heading">
            <span>AI 코파일럿</span>
            <strong>Mock</strong>
          </div>
          <label htmlFor="copilot-question">질문</label>
          <textarea
            id="copilot-question"
            onChange={(event) => setQuestion(event.target.value)}
            rows="7"
            value={question}
          />
          <button onClick={handleGenerateAnswer} type="button">
            답변 생성
          </button>
          <div className="copilot-answer" aria-live="polite">
            {copilotAnswer}
          </div>
        </aside>
      </div>
    </main>
  )
}

export default App
