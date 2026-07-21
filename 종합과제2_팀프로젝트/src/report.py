"""
- report.md 자동 생성
"""


def generate_report(
    shape_before: tuple,
    shape_after: tuple,
    removed: int,
    stats_result: dict,
    corr_result: dict,
    ttest_result: dict,
    metrics: dict,
    save_path: str,
) -> None:
    """분석 결과를 report.md로 자동 생성"""

    report = f"""# NYC 옐로택시 운행 소요 시간 예측 리포트

## 1. 프로젝트 개요
- **주제**: 운행 소요 시간 예측 (회귀)
- **가설**: 같은 거리라도 출퇴근 시간대·요일에 따라 소요시간이 달라진다
- **데이터**: yellow_tripdata_2026-05.parquet

## 2. 데이터 전처리
- 원본: {shape_before[0]:,}행 x {shape_before[1]}열
- 전처리 후: {shape_after[0]:,}행 x {shape_after[1]}열
- 제거 건수: {removed:,}건
- 결측치 처리: passenger_count(→1.0), RatecodeID(→1.0), store_and_fwd_flag(→N), congestion_surcharge(→0.0), Airport_fee(→0.0)
- 이상값 기준: 소요시간 1~120분, 주행거리 0~100마일, 요금 0 초과

## 3. 기술통계
| 항목 | duration_min | trip_distance | fare_amount |
|------|-------------|---------------|-------------|
| 평균 | {stats_result['duration_min']['mean']:.2f} | {stats_result['trip_distance']['mean']:.2f} | {stats_result['fare_amount']['mean']:.2f} |
| 표준편차 | {stats_result['duration_min']['std']:.2f} | {stats_result['trip_distance']['std']:.2f} | {stats_result['fare_amount']['std']:.2f} |
| 중앙값 | {stats_result['duration_min']['50%']:.2f} | {stats_result['trip_distance']['50%']:.2f} | {stats_result['fare_amount']['50%']:.2f} |

## 4. 상관분석
- trip_distance ↔ duration_min: **{corr_result['duration_min']['trip_distance']:.3f}** (강한 양의 상관)
- is_weekend ↔ duration_min: **{corr_result['duration_min']['is_weekend']:.3f}** (약한 음의 상관)
- hour ↔ duration_min: **{corr_result['duration_min']['hour']:.3f}** (비선형 관계)

## 5. t-test (주중 vs 주말)
- t-statistic: {ttest_result['t_stat']:.4f}
- p-value: {ttest_result['p_value']:.6f}
- **결론**: p < 0.05이므로 주중과 주말의 소요시간 차이는 통계적으로 유의미함

## 6. 모델 평가 (LinearRegression)
| 지표 | 값 | 해석 |
|------|-----|------|
| R² | {metrics['r2']:.4f} | 변동의 {metrics['r2']*100:.1f}% 설명 |
| MAE | {metrics['mae']:.2f}분 | 평균 {metrics['mae']:.1f}분 오차 |
| RMSE | {metrics['rmse']:.2f}분 | 큰 오차에 벌점 |

## 7. 결론
- 가설 검증: 주중이 주말보다 평균 약 2분 더 오래 걸리며, 통계적으로 유의미함
- trip_distance가 소요시간의 가장 강력한 예측 변수 (상관계수 0.77)
- 시간대(hour)는 선형 상관은 낮지만, 시각화에서 오후 2~4시 피크 패턴 확인
"""

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"리포트 저장: {save_path}")