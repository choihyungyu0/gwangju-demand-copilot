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
