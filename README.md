# 광주 상권·관광 수요예측 코파일럿

광주 지역 상권과 관광지의 수요 변화를 공공데이터와 AI로 예측하는 public-data AI competition prototype입니다. 현재 단계는 실제 API와 모델을 연결하기 전, mock data로 사용자 흐름과 테스트 harness를 검증하는 MVP입니다.

## Tech Stack

- React
- Vite
- Vitest
- Testing Library
- Mock JSON data in `public/predictions.json`

## How to Run

```bash
npm install
npm run dev
```

## How to Test

```bash
npm run test:run
```

## Data pipeline commands

```bash
python scripts/inspect_store_columns.py
python scripts/collect_store_data.py
python scripts/match_area_by_radius.py
python scripts/debug_area_matches.py
python scripts/make_mock_dataset.py
python scripts/make_score.py
python scripts/make_prediction_json.py
```

## Real tourism data integration

한국관광공사 국문 관광정보 서비스 / TourAPI를 사용해 실제 관광지, 행사, 문화시설 지표를 만들 수 있습니다. API 키가 없어도 Vercel build와 React MVP는 그대로 동작하며, `TOUR_API_SERVICE_KEY`가 없으면 기존 mock 관광 데이터가 fallback으로 사용됩니다.

1. 공공데이터포털에서 `한국관광공사_국문 관광정보 서비스_GW` 활용신청을 합니다.
2. 발급받은 서비스 키를 로컬 `.env` 파일에 저장합니다.

```bash
TOUR_API_SERVICE_KEY=your_tour_api_key_here
```

3. 실제 관광 데이터를 수집하고, 상권 feature에 적용한 뒤 예측 JSON을 다시 만듭니다.

```bash
python scripts/collect_tourism_data.py
python scripts/apply_tourism_features.py
python scripts/make_prediction_json.py
```

`collect_tourism_data.py`는 `data/processed/areas.csv`의 `center_lat`, `center_lng`, `radius_m`을 사용해 TourAPI 위치기반 관광정보를 조회합니다. 수집 원본은 `data/raw/tourism_api_results.json`, 가공 feature는 `data/processed/tourism_area_features_real.csv`에 저장됩니다. `apply_tourism_features.py`는 real CSV가 있으면 이를 사용하고, 없으면 `data/processed/tourism_area_features.csv` mock 데이터를 사용합니다.

## Visitor demand feature pipeline

방문 수요 feature는 공급 측면의 상권 데이터와 유입 매력도를 나타내는 관광/행사 데이터를 보완하는 실제 수요 흐름 지표입니다. 현재는 `data/processed/visitor_area_features.csv`에 mock 방문자 수, 방문자 증가율, 방문 수요 점수, 방문 수요 요약을 생성합니다.

향후에는 한국관광공사 관광빅데이터의 방문자 수 데이터를 활용해 구 단위 또는 지역 반경 기반 방문 흐름으로 교체할 계획입니다. 실제 데이터가 준비되기 전까지는 mock visitor feature를 fallback으로 사용합니다.

```bash
python scripts/make_mock_visitor_features.py
python scripts/merge_visitor_features.py
python scripts/make_prediction_json.py
```

## Weather feature pipeline

날씨 feature는 상권 공급, 관광/행사 매력도, 방문 수요 흐름에 더해 외부 수요 리스크를 반영합니다. 현재는 `data/processed/weather_area_features.csv`에 mock 기온, 강수량, 비 여부, 날씨 점수, 날씨 리스크, 날씨 요약을 생성합니다.

향후에는 기상청 단기예보 조회서비스의 실제 예보 데이터를 사용해 지역별 강수와 기온 영향을 교체할 계획입니다. 실제 API 키나 실시간 예보가 준비되기 전까지는 mock weather feature를 fallback으로 사용하며, npm build와 Vercel 배포는 Python이나 API 키를 요구하지 않습니다.

```bash
python scripts/make_mock_weather_features.py
python scripts/merge_weather_features.py
python scripts/make_prediction_json.py
```

## Demand scoring logic

MVP의 최종 수요예측 점수는 `data/processed/area_features_scored.csv`에 저장됩니다. 현재 공식은 설명 가능한 rule-based scoring이며, 각 점수는 0-100 범위로 정규화하거나 안전한 fallback 값을 사용합니다.

- `commercial_score`: 25%
- `tourism_component_score`: 20%
- `visitor_component_score`: 25%
- `event_component_score`: 10%
- `weather_component_score`: 20%

```bash
python scripts/calculate_demand_score.py
python scripts/make_prediction_json.py
```

이 공식은 초기 MVP용 기준선입니다. 실제 방문자·매출·날씨·행사 데이터가 충분히 쌓이면 가중치는 검증 데이터로 보정하거나 머신러닝 모델로 교체할 수 있습니다.

## Machine learning model pipeline

머신러닝 파이프라인은 5개 지역 단일 행만으로 모델을 학습하지 않기 위해 `data/processed/daily_demand_training.csv`를 먼저 만듭니다. 현재는 2026-05-01부터 2026-06-29까지 60일 × 5개 지역의 MVP 학습 데이터를 생성합니다.

`train_demand_model.py`는 scikit-learn이 설치된 환경에서 `RandomForestRegressor`를 학습하고, 테스트 기간 기준 `MAE`, `RMSE`, `R2`를 `data/processed/model_metrics.json`에 저장합니다. 변수 중요도는 `data/processed/feature_importance.csv`, 일별 예측 결과는 `data/processed/daily_model_predictions.csv`에 저장합니다.

현재 모델은 MVP 수준의 scenario-based 학습 데이터로 동작합니다. 향후 실제 방문자 수, 행사, 날씨, 매출 proxy 데이터가 누적되면 모델 신뢰도와 feature importance 해석이 더 좋아집니다.

```bash
python scripts/make_daily_training_dataset.py
python scripts/train_demand_model.py
python scripts/apply_model_insights.py
python scripts/make_prediction_json.py
```

## Current MVP Scope

- 광주 5개 상권·관광 지역 mock demand prediction
- 선택 지역별 수요 점수, 평균 대비 변화, 리스크, 주요 요인 표시
- 7일 수요 전망 리스트
- 외부 AI API 없이 template 기반 AI copilot 답변 생성
- Vitest 기반 utility test harness

## Future Plan

- 공공데이터 API 연동
- 상권·관광·날씨·이벤트 데이터를 수집하는 preprocessing pipeline 구성
- 초기 demand score formula 설계
- 머신러닝 기반 수요예측 모델 검증
- LLM 기반 copilot 설명과 추천 고도화
- 발표용 demo scenario와 UI polishing
