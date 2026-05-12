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

## Integration Notes

- 지역 단위 key를 먼저 표준화한 뒤 상권, 관광, 날씨 데이터를 결합합니다.
- API key는 로컬 `.env` 또는 배포 환경 변수로만 관리하고 저장소에는 커밋하지 않습니다.
- 초기 모델 검증 전에는 수집 raw data와 가공 feature를 분리해 재현성을 확보합니다.
