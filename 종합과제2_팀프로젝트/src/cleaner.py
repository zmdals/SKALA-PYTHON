"""
- 데이터 전처리(Preprocessing): 결측치 처리 + 이상치 제거 + features 생성
    - 1.결측치: 
"""
import pandas as pd
from config import DURATION_MIN, DURATION_MAX

#결측치 처리 (5개 컬럼)
# 1. passenger_count: null/0 → 1.0 (기사가 단말기에 미입력, 최빈값이 1명)
# 2. RatecodeID: null → 1.0(Standard rate), 99 → 1.0 (99는 공식 결측코드)
# 3. store_and_fwd_flag: null → "N" (99.9%가 N)
# 4. congestion_surcharge: null → 0.0 (요금 미부과로 처리)
# 5. Airport_fee: null → 0.0 (공항 요금 미부과로 처리)
def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["passenger_count"] = df["passenger_count"].fillna(1.0)
    df.loc[df["passenger_count"] == 0, "passenger_count"] = 1.0
    df["RatecodeID"] = df["RatecodeID"].fillna(1.0)
    df.loc[df["RatecodeID"] == 99, "RatecodeID"] = 1.0
    df["store_and_fwd_flag"] = df["store_and_fwd_flag"].fillna("N")
    df["congestion_surcharge"] = df["congestion_surcharge"].fillna(0.0)
    df["Airport_fee"] = df["Airport_fee"].fillna(0.0)
    return df

#이상치 제거 
# IQR 구해서 이상치 제거 안한 이유:
# IQR은 "기준을 모를 때 데이터 분포에서 기준을 만들어내는 방법"
# 운행 시간은 1분 미만 or 120분 초과되면 비정상(이상치)의 확실한 기준이 있으므로,
# IQR을 쓰면 괜히 정상데이터가 삭제 될 수 있음.
# 아래 조건 미충족 -> 이상치
# 정상 데이터 기준:
#1. 운행시간 정상 범위 안 (최소: 1분, 최대: 120분)
#2. 주행거리 0 초과 (주행거리 음수 X)
#3. 주행요금 0 초과 (요금 음수 X)
#4. 100마일 미만 (뉴욕 시내 기준 비정상)
def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df["duration_min"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    before = len(df)
    df = df[
        (df["duration_min"] >= DURATION_MIN) 
        & (df["duration_min"] <= DURATION_MAX)
        & (df["trip_distance"] > 0)
        & (df["fare_amount"] > 0)
        & (df["trip_distance"] <= 100) 
    ]
    after = len(df)
    print(f"이상값 제거: {before:,} → {after:,} ({before - after:,}건 제거)")

    return df

#시간 관련 feature 생성
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df["tpep_pickup_datetime"].dt.hour #시간 추출
    df["day_of_week"] = df["tpep_pickup_datetime"].dt.dayofweek #요일 추춘
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int) #주말여부 추출
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = handle_missing(df)
    df = remove_outliers(df)
    df = engineer_features(df)
    return df