"""
- 데이터 로딩 + 기본 EDA
"""
import pandas as pd
import polars as pl


def load_pandas(path: str) -> pd.DataFrame:
    try:
        return pd.read_parquet(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")


def load_polars(path: str) -> pl.DataFrame:
    try:
        return pl.read_parquet(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

def print_basic_eda(df: pd.DataFrame) -> None:
    print("=== 기본 정보 ===")
    df.info()

    print("\n=== 기술 통계 ===")
    print(df.describe())

    print("\n=== 결측치 현황 ===")
    missing = df.isnull().sum()
    for col in df.columns:
        if missing[col] > 0:
            print(f"  {col}: {missing[col]:,}건 ({missing[col]/len(df)*100:.1f}%)")

    print(f"\n중복 행: {df.duplicated().sum():,}건")