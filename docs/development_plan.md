# Development Plan

## Phase 1: Mock-data MVP

- Vite React frontend 구성
- 광주 5개 지역 mock prediction data 작성
- 수요 상세 UI와 template copilot panel 구현
- Vitest 기반 utility test harness 구성

## Phase 2: Public Data Collection

- 상권, 관광, 날씨, 지역 시설 데이터를 수집합니다.
- 지역 key, 날짜 key, 위치 정보를 정규화합니다.
- API quota, update interval, missing data 정책을 정리합니다.

## Phase 3: Demand Score Formula

- 유동인구, 관광 관심도, 날씨, 요일, 이벤트 feature를 조합합니다.
- 설명 가능한 rule 기반 score를 먼저 설계합니다.
- 실제 모델 도입 전 baseline metric을 확보합니다.

## Phase 4: Machine Learning Model

- 시간 단위 또는 일 단위 수요예측 target을 정의합니다.
- baseline model과 gradient boosting 계열 모델을 비교합니다.
- 예측 정확도와 설명 가능성을 함께 평가합니다.

## Phase 5: LLM-based Copilot

- 예측 결과와 top factors를 structured context로 제공합니다.
- staffing, inventory, promotion, risk action을 운영자 언어로 변환합니다.
- API key와 prompt logging 정책을 분리합니다.

## Phase 6: Presentation and Demo Polishing

- 심사위원용 demo scenario를 구성합니다.
- 데이터 출처, 모델 구조, 사회적 효과를 명확히 설명합니다.
- UI 흐름, 반응형 화면, fallback 상태를 정리합니다.
