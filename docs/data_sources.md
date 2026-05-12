# Planned Public Data Sources

이 문서는 향후 실제 데이터 연동 단계에서 검토할 공공데이터 후보를 정리합니다. 현재 MVP는 외부 API를 호출하지 않고 mock data만 사용합니다.

## Sources

- 소상공인시장진흥공단 상가/상권정보
- 한국관광공사 관광빅데이터 정보서비스
- 한국관광공사 국문 관광정보 서비스
- 광주광역시 지역특화거리 점포현황
- 광주광역시 전통시장 점포 현황
- 기상청 단기예보 조회서비스

## 한국관광공사 국문 관광정보 서비스 / TourAPI

- 상태: 실제 연동 준비 완료, API 키가 없으면 mock 관광 feature 사용
- 서비스: `한국관광공사_국문 관광정보 서비스_GW`
- 활용 API: `KorService2/locationBasedList2`
- 기준 좌표: `data/processed/areas.csv`의 `center_lat`, `center_lng`, `radius_m`
- 인증 정보: `TOUR_API_SERVICE_KEY` 환경 변수 또는 로컬 `.env`

### Planned/Used Features

- `tourist_spot_count`: TourAPI 관광지 유형(`contentTypeId=12`)을 상권 반경 안에서 집계합니다.
- `culture_count`: TourAPI 문화시설 유형(`contentTypeId=14`)을 상권 반경 안에서 집계합니다.
- `event_count`: TourAPI 행사/공연/축제 유형(`contentTypeId=15`)을 상권 반경 안에서 집계합니다.
- `tourism_score`: 관광지, 행사, 문화시설 수를 가중 합산해 0-100 범위로 만든 MVP용 관광 영향 점수입니다.

### Outputs

- raw API-like JSON: `data/raw/tourism_api_results.json`
- real processed feature CSV: `data/processed/tourism_area_features_real.csv`
- fallback mock feature CSV: `data/processed/tourism_area_features.csv`
- merged feature CSV: `data/processed/area_features_full.csv`

## 한국관광공사 관광빅데이터 / 방문자 수 데이터

- 상태: mock feature pipeline 구성 완료, 향후 실제 관광빅데이터 방문자 수로 대체 예정
- 목적: 상권 공급량과 관광/행사 매력도만으로 설명하기 어려운 실제 방문 수요 흐름을 보완합니다.
- 현재 output: `data/processed/visitor_area_features.csv`

### Planned/Used Features

- `visitor_count_gu`: 구 또는 지역 단위 방문자 규모를 나타내는 수요 흐름 지표입니다.
- `visitor_growth`: 직전 기간 대비 방문자 증가율입니다. 양수면 방문자 증가 추세, 음수면 감소 가능성을 의미합니다.
- `visitor_score`: 방문자 규모와 증가 추세를 0-100 범위로 환산한 MVP용 방문 수요 점수입니다.

## 기상청 단기예보 조회서비스

- 상태: mock feature pipeline 구성 완료, 향후 실제 기상청 단기예보 API로 대체 예정
- 목적: 강수, 기온 등 외부 날씨 변수가 보행·관광·야외 홍보 수요에 주는 리스크를 보완합니다.
- 현재 output: `data/processed/weather_area_features.csv`

### Planned/Used Features

- `temp`: 지역별 예보 기온입니다.
- `rain_mm`: 예보 강수량입니다.
- `rain_flag`: 강수 여부입니다. 1이면 비가 있는 조건으로 간주합니다.
- `weather_score`: 기온과 강수 영향을 0-100 범위로 환산한 MVP용 날씨 수요 점수입니다.
- `weather_risk_level`: 강수량과 날씨 점수에 따른 낮음/중간/높음 리스크 구분입니다.

## Integration Notes

- 지역 단위 key를 먼저 표준화한 뒤 상권, 관광, 날씨 데이터를 결합합니다.
- API key는 로컬 `.env` 또는 배포 환경 변수로만 관리하고 저장소에는 커밋하지 않습니다.
- 초기 모델 검증 전에는 수집 raw data와 가공 feature를 분리해 재현성을 확보합니다.
