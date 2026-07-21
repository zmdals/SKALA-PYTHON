"""
- 통계분석: 기술통계, 상관계수, t-test
"""
import pandas as pd
from scipy.stats import ttest_ind


def print_descriptive_stats(df: pd.DataFrame) -> dict:
    """기술통계: 평균·표준편차·분위수"""
    cols = ["duration_min", "trip_distance", "fare_amount"]
    stats = df[cols].describe()
    print("=== 기술통계 ===")
    print(stats)
    return stats.to_dict()


def print_correlation(df: pd.DataFrame) -> dict:
    """변수 간 상관계수"""
    cols = ["duration_min", "trip_distance", "hour", "day_of_week", "is_weekend"]
    corr = df[cols].corr()
    print("\n=== 상관계수 ===")
    print(corr.round(3))

    # target과의 상관계수만 따로
    print("\n[duration_min과의 상관계수]")
    for col in cols[1:]:
        print(f"  {col}: {corr.loc['duration_min', col]:.3f}")

    return corr.to_dict()


def run_ttest(df: pd.DataFrame) -> dict:
    """
    t-test: 주중 vs 주말 평균 소요시간 차이 검정
    - 귀무가설(H0): 주중과 주말의 평균 소요시간은 같다
    - 대립가설(H1): 주중과 주말의 평균 소요시간은 다르다
    """
    weekday = df[df["is_weekend"] == 0]["duration_min"]
    weekend = df[df["is_weekend"] == 1]["duration_min"]

    t_stat, p_value = ttest_ind(weekday, weekend)

    print("\n=== t-test: 주중 vs 주말 소요시간 ===")
    print(f"  주중 평균: {weekday.mean():.2f}분 ({len(weekday):,}건)")
    print(f"  주말 평균: {weekend.mean():.2f}분 ({len(weekend):,}건)")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value: {p_value:.6f}")

    if p_value < 0.05:
        print("  → p < 0.05이므로 귀무가설 기각. 주중과 주말의 소요시간에 유의미한 차이가 있다.")
    else:
        print("  → p >= 0.05이므로 귀무가설 채택. 유의미한 차이가 없다.")

    return {"t_stat": t_stat, "p_value": p_value}