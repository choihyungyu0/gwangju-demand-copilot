# Service Flow

## MVP Flow

1. 사용자가 광주 상권·관광 지역을 선택합니다.
2. 시스템은 선택 지역의 demand prediction summary를 표시합니다.
3. 시스템은 predicted score, average 대비 변화, risk level을 보여줍니다.
4. 시스템은 top factors를 설명해 수요 변화의 주요 원인을 드러냅니다.
5. Copilot은 staffing, inventory, promotion, risk actions 중심으로 추천합니다.

## Current Behavior

- 모든 예측 데이터는 `public/predictions.json`에서 로드합니다.
- Copilot 답변은 `src/utils/demand.js`의 template 함수로 생성합니다.
- 외부 AI API, 지도 API, backend, login은 포함하지 않습니다.
