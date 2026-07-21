"""
[실습 5] Polars · DuckDB 성능 비교
- 입력: data/events_large.csv (100만 행)
- 같은 집계를 Pandas · Polars · DuckDB 세 엔진으로 돌려 비교 + 결과 일치 검증
질의 정의: "event_type 별로 묶고, 건수와 amount 평균을 구한 뒤, 건수 내림차순으로 정렬"
"""

import time
import pandas as pd
import polars as pl
import duckdb

DATA_PATH = "../../data/events_large.csv"


# 1. Pandas 기준선 (Eager — 단일 스레드)
def run_pandas() -> tuple[pd.DataFrame, float]:
    #Pandas의 파일 읽기부터 결과까지 전체 시간 확인
    start = time.perf_counter()
    df = pd.read_csv(DATA_PATH)
    result = (
        df.groupby("event_type")
        .agg(cnt=("amount", "count"), avg=("amount", "mean"))
        .sort_values("cnt", ascending=False)
        .reset_index()
    )
    spend_time = (time.perf_counter() - start) * 1000
    return result, spend_time


# 2. Polars Lazy (scan_csv + collect)
# Polars: scan_csv(지연) → 계획 최적화 → collect(실행). -> collect() 호출 될 때 데이터를 읽어들임.

def run_polars() -> tuple[pd.DataFrame, float]:
    start = time.perf_counter()
    result = (
        pl.scan_csv(DATA_PATH)          # ★ scan = 계획만 세움
        .group_by("event_type")
        .agg([
            pl.len().alias("cnt"),
            pl.col("amount").mean().alias("avg"),
        ])
        .sort("cnt", descending=True)
        .collect()                       # ★ 여기서 실제 실행
    )
    spend_time = (time.perf_counter() - start) * 1000
    return result.to_pandas(), spend_time


# 3. DuckDB — db 연결 -> SQL로 파일 직접 조회
# DuckDB: CSV를 DB에 넣지 않고 SQL로 바로 조회

def run_duckdb() -> tuple[pd.DataFrame, float]:
    start = time.perf_counter()
    result = duckdb.sql(f"""
        SELECT event_type,
               COUNT(amount) AS cnt,
               AVG(amount)   AS avg
        FROM '{DATA_PATH}'
        GROUP BY event_type
        ORDER BY cnt DESC
    """).df()
    spend_time = (time.perf_counter() - start) * 1000
    return result, spend_time


# 4. 결과 일치 검증 (성능보다 우선)
# 세 엔진의 결과가 동일한지 검증한다. 비교 전 정렬·타입·컬럼순서를 맞춰야 한다.
def verify_results(a: pd.DataFrame, b: pd.DataFrame, c: pd.DataFrame) -> None:

    a = a.sort_values("event_type").reset_index(drop=True)
    b = b.sort_values("event_type").reset_index(drop=True)
    c = c.sort_values("event_type").reset_index(drop=True)

    # atol=1e-6: 부동소수점 미세 오차는 정상이므로 허용
    pd.testing.assert_frame_equal(a, b, check_dtype=False, atol=1e-6)
    pd.testing.assert_frame_equal(a, c, check_dtype=False, atol=1e-6)
    print("세 엔진 결과 일치!")


# STEP 5: 벤치마크 표
if __name__ == "__main__":
    # 각 엔진 실행
    res_pandas, t_pandas = run_pandas()
    res_polars, t_polars = run_polars()
    res_duck, t_duck = run_duckdb()

    print("[Pandas 결과 상위 5행]")
    print(res_pandas.head())

    # 결과 일치 검증
    verify_results(res_pandas, res_polars, res_duck)

    # 벤치마크 표
    benchmarks = [
        ("Polars", t_polars),
        ("DuckDB", t_duck),
        ("Pandas", t_pandas),
    ]
    base = t_pandas
    print(f"\n{'엔진':<10}{'시간(ms)':>10}{'배속':>10}")
    print("-" * 30)
    for name, t in sorted(benchmarks, key=lambda x: x[1]):
        print(f"{name:<10}{t:>10.0f}{base / t:>9.1f}x")