"""
- ML Pipeline: 
- 1.전처리
- 2.모델 학습
- 3.평가
- 4.저장
"""
import pandas as pd
import joblib
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config import FEATURES, TARGET, NUMERIC_FEATURES, CATEGORICAL_FEATURES

#Pipeline 구성 → 학습 → 평가 → 저장
def build_and_train(df: pd.DataFrame, save_path: str) -> dict:
    X = df[FEATURES]
    y = df[TARGET]

    # 훈련/검증 분리
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"훈련: {len(X_train):,}건 / 검증: {len(X_test):,}건")

    # ColumnTransformer: #전처리 변수 지정
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)
        ]
    )

    # Pipeline: 전처리 → 선형회귀
    pipeline = Pipeline(
        steps =[
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]
    )

    # 학습
    pipeline.fit(X_train, y_train)

    coef = pipeline.named_steps["model"].coef_
    for name, c in zip(FEATURES, coef):
        print(f"  {name}: {c:.4f}")
    # 예측
    y_pred = pipeline.predict(X_test)

    # 평가 지표
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print("\n=== 모델 평가 ===")
    print(f"  R²:   {r2:.4f}  (1에 가까울수록 좋음, 변동의 {r2*100:.1f}% 설명)")
    print(f"  MAE:  {mae:.2f}분 (평균적으로 {mae:.1f}분 틀림)")
    print(f"  RMSE: {rmse:.2f}분 (큰 오차에 벌점)")

    # 모델 저장
    joblib.dump(pipeline, save_path)
    print(f"\n모델 저장: {save_path}")

    return {"r2": r2, "mae": mae, "rmse": rmse}