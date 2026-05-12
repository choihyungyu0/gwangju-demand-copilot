import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { buildCopilotAnswer, getRiskClass, getScoreLabel } from './utils/demand'

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
              <span>수요 점수</span>
              <strong>{selectedArea.predicted_score}</strong>
              <em>{getScoreLabel(selectedArea.predicted_score)}</em>
            </div>
            <div className="metric-card">
              <span>평균 대비</span>
              <strong>{selectedArea.change_vs_avg}</strong>
              <em>최근 평균 기준</em>
            </div>
          </div>

          <p className="summary">{selectedArea.summary}</p>

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

          <div className="insight-grid">
            <section>
              <h3>주요 예측 요인</h3>
              <ul>
                {selectedArea.top_factors.map((factor) => (
                  <li key={factor}>{factor}</li>
                ))}
              </ul>
            </section>
            <section>
              <h3>추천 실행</h3>
              <ul>
                {selectedArea.recommendations.map((recommendation) => (
                  <li key={recommendation}>{recommendation}</li>
                ))}
              </ul>
            </section>
          </div>

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
