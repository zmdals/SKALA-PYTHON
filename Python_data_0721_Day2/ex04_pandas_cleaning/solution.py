"""
실습 4: Pandas 2.x 데이터 정제
- 데이터 정제: 결측 처리 그룹별 중앙값 대치, 이상치 IQR 윈저라이징, 타입 정규화 astype · to_datetime
- 집계, 결합: 그룹 요약 groupby.agg, 교차표 pivot_table, 병합 merge (키 기준)

최초 작성일: 2026-07-21
작성자: 임승민
"""

import pandas as pd
pd.options.mode.copy_on_write = True # pandas 2.x 권장 / CoW

file_path = "../../data/sales_raw.csv"

# 0. 진단(데이터 로드 & 확인)
#CSV 로드 후 진단 정보(shape·dtype·결측·describe)를 출력한다.
def load_and_diagnose(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print("=" * 60)
    print(f"Shape: {df.shape}")
    print(f"\n[dtypes]\n{df.dtypes}")
    print(f"\n[결측치 개수]\n{df.isna().sum()}")
    print(f"\n[수치형 요약]\n{df.describe()}")
    print("=" * 60)
    return df     # 실제 값 눈으로 확인

# 1. 타입 정규화
# 숫자는 숫자로, 날짜는 날짜로, 범주는 category로 변환.
# errors='coerce' → 변환 실패한 값은 NaN 처리.
def normalize_types(df: pd.DataFrame) -> pd.DataFrame:

    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["category"] = df["category"].astype("category")
    df["region"] = df["region"].astype("category")
    return df

# 2. 결측 처리 — 그룹별 중앙값 대치
# 수치형 컬럼의 결측치를 카테고리별 중앙값으로 대치(replace).
# transform: 행 수를 유지하면서 그룹 연산 결과를 되돌려주는 메서드.
def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    # 범주형 결측 → 최빈값으로 채우기
    for col in ["region", "category"]:
        if df[col].isna().sum() > 0:
            mode_val = df[col].mode()[0]
            df[col] = df[col].fillna(mode_val)

    for col in ["unit_price", "quantity", "discount"]:
        df[col] = df.groupby("category", observed=True)[col].transform(
            lambda s: s.fillna(s.median())
        )
    # 그룹별 중앙값으로도 못 채운 잔여 결측(그룹 전체가 NaN인 경우) → 전체 중앙값
    for col in ["unit_price", "quantity", "discount"]:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].median())
    return df

# 3. 이상치 처리 — IQR(사분위 범위) 윈저라이징
# 통계에서 "Q1 - 1.5×IQR 보다 작거나, Q3 + 1.5×IQR 보다 크면 이상치" 로 보는 것이 표준 
# IQR 기반 윈저라이징: 극단값을 경계선까지 끌어당긴다(삭제 아님).
def winsorize(s: pd.Series, k: float = 1.5) -> pd.Series:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    low, high = q1 - k * iqr, q3 + k * iqr
    return s.clip(lower=low, upper=high)

def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """unit_price · quantity 컬럼의 이상치를 윈저라이징한다."""
    for col in ["unit_price", "quantity"]:
        before = df[col].max()
        df[col] = winsorize(df[col])
        after = df[col].max()
        print(f"  {col} max: {before:,.1f} → {after:,.1f}")
    return df

# 파생컬럼 셍성 및 반환
def compute_amount(df: pd.DataFrame) -> pd.DataFrame:
    """amount = quantity × unit_price × (1 - discount) 파생 컬럼 생성."""
    df["amount"] = df["quantity"] * df["unit_price"] * (1 - df["discount"])
    return df
# 4. 집계
def aggregate(df: pd.DataFrame) -> None:
    """groupby.agg(세로 요약)과 pivot_table(가로세로 교차표)을 출력한다."""
    # 1. groupby.agg — 카테고리별 요약
    summary = df.groupby("category", observed=True).agg(
        건수=("amount", "count"),
        평균가=("unit_price", "mean"),
        중앙값=("unit_price", "median"),
        총매출=("amount", "sum"),
    ).round(1)
    print("\n[카테고리별 요약 — groupby.agg]")
    print(summary)

    # 2. pivot_table — 카테고리 × 지역 교차표
    pivot = df.pivot_table(
        index="category",
        columns="region",
        values="amount",
        aggfunc="sum",
        fill_value=0,
        observed=True,
    ).round(0)
    print("\n[카테고리 × 지역 매출 교차표 — pivot_table]")
    print(pivot)

if __name__ == "__main__":
    # STEP 0: 진단
    df = load_and_diagnose(file_path)

    # STEP 1: 타입 정규화 (이 단계에서 변환 실패한 값 → NaN → 결측 증가)
    df = normalize_types(df)
    print("\n[타입 정규화 후]")
    print(f"dtypes:\n{df.dtypes}")
    print(f"\n결측치:\n{df.isna().sum()}")

    # STEP 2: 결측 처리 (반드시 타입 정규화 '다음')
    df = fill_missing(df)
    print(f"\n[결측 처리 후 결측치]\n{df.isna().sum()}")

    # STEP 3: 이상치 처리
    print("\n[이상치 윈저라이징]")
    df = handle_outliers(df)

    # 파생 컬럼
    df = compute_amount(df)

    # STEP 4~5: 집계
    aggregate(df)

    # 최종 확인
    print(f"\n[최종 dtypes]\n{df.dtypes}")
    print(f"\n완료 — 정제 후 {df.shape[0]}행 × {df.shape[1]}열")