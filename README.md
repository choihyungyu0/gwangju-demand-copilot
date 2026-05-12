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
