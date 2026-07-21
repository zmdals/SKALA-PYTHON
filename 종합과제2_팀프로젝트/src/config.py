"""
- 설정값 모음
"""

RAW_DATA_PATH = "data/raw/yellow_tripdata_2026-05.parquet"
OUTPUT_DIR = "outputs"

DURATION_MIN = 1
DURATION_MAX = 120

FEATURES = ["trip_distance", "hour", "day_of_week", "is_weekend","PULocationID"]
TARGET = "duration_min"

# Pipeline용 컬럼 분류
NUMERIC_FEATURES = ["trip_distance", "hour", "day_of_week", "is_weekend"]
CATEGORICAL_FEATURES = ["PULocationID"] #범주형 변수