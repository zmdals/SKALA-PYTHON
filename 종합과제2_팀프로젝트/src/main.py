"""
End2End 데이터 분석 프로젝트 - 메인 실행
- 주제: NYC 옐로택시 운행 소요 시간 예측 (회귀)
- 가설: 같은 거리라도 출퇴근 시간대엔 더 오래 걸린다

작성일: 2026-07-21
작성자: 3반 임승민
"""
import pandas as pd
from config import RAW_DATA_PATH, OUTPUT_DIR
from loader import load_pandas, load_polars, print_basic_eda
from cleaner import clean_data
from eda import plot_duration_by_hour, plot_interactive_duration
from stats import print_descriptive_stats, print_correlation, run_ttest
from pipeline import build_and_train
from report import generate_report

pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


def main():
    # 1. 데이터 로딩
    df_pd = load_pandas(RAW_DATA_PATH)
    df_pl = load_polars(RAW_DATA_PATH)
    print(f"Pandas shape: {df_pd.shape}")
    print(f"Polars shape: {df_pl.shape}\n") #위와 결과 동일해야함

    # 2. 기본 EDA
    print_basic_eda(df_pd)
    
    # 3. 전처리
    shape_before = df_pd.shape
    df = clean_data(df_pd)
    shape_after = df.shape
    removed = shape_before[0] - shape_after[0]
    print(f"\n전처리 후 shape: {shape_after}")
    print(f"결측치 잔존: {df.isnull().sum().sum()}건")
    print(f"\nduration_min 통계:\n{df['duration_min'].describe()}")

    # 4. 시각화
    plot_duration_by_hour(df, f"{OUTPUT_DIR}/figures/duration_by_hour.png")
    plot_interactive_duration(df, f"{OUTPUT_DIR}/figures/duration_heatmap.html")

    # 5. 통계분석
    stats_result = print_descriptive_stats(df)
    corr_result = print_correlation(df)
    ttest_result = run_ttest(df)

    # 6. ML Pipeline
    metrics = build_and_train(df, f"{OUTPUT_DIR}/models/model.joblib")

    # 7. 리포트 생성
    generate_report(
        shape_before=shape_before,
        shape_after=shape_after,
        removed=removed,
        stats_result=stats_result,
        corr_result=corr_result,
        ttest_result=ttest_result,
        metrics=metrics,
        save_path=f"{OUTPUT_DIR}/report.md",
    )

if __name__ == "__main__":
    main()