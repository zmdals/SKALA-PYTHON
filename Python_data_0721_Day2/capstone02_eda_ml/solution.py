"""
[종합실습 2] EDA + 통계 검정 + ML 파이프라인
- 입력: data/telco_churn.csv (7천 행)
- 탐색(EDA) → 시각화(Plotly) → 통계 검정(t-test·카이제곱) → ML(RandomForest)
- 흐름: EDA → 시각화 → 통계 검정 → 머신러닝 (이 순서를 지키는 것이 핵심)
"""

import polars as pl
import pandas as pd
import plotly.express as px
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
import joblib
from pathlib import Path

DATA_PATH = "../../data/telco_churn.csv"
OUTPUT_DIR = Path("output")


# 1. EDA — Polars로 데이터 탐색 & 가설 세우기
# Polars로 데이터 형태·타깃 비율·그룹별 평균을 파악
def eda() -> pl.DataFrame:
    df = pl.read_csv(DATA_PATH)
    print("=" * 60)
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns}")
    print(df.head())
    print(f"\n[describe]\n{df.describe()}")

    # ★ 타깃 비율 — 가장 먼저 확인해야 할 것
    print("\n[이탈(churn) 비율]")
    churn_dist = df.group_by("churn").len()
    print(churn_dist)

    # 이탈 여부별 평균 비교 → 가설 세우기
    print("\n[이탈 여부별 평균]")
    print(df.group_by("churn").agg([
        pl.col("monthly_charges").mean().alias("평균월요금"),
        pl.col("tenure_months").mean().alias("평균가입기간"),
        pl.col("total_charges").mean().alias("평균총요금"),
        pl.len().alias("인원"),
    ]))

    return df


# 2. Plotly 시각화 → HTML 리포트
# 박스플롯으로 이탈 여부별 월 요금 분포를 시각화
def step_plotly(pdf: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # churn을 문자열로 변환 (plotly 범주 표시용)
    pdf_plot = pdf.copy()
    pdf_plot["churn_label"] = pdf_plot["churn"].map({0: "잔류", 1: "이탈"})

    fig = px.box(
        pdf_plot,
        x="churn_label",
        y="monthly_charges",
        title="이탈 여부별 월 요금 분포",
        labels={"churn_label": "이탈 여부", "monthly_charges": "월 요금"},
        color="churn_label",
    )
    out_path = OUTPUT_DIR / "churn_charges.html"
    fig.write_html(str(out_path))
    print(f"Plotly HTML 생성: {out_path}")


# 3. 통계 검정 - 눈속임 방지 (p값(우연일 확률)-작을수록 우연x)
def step_stat_tests(pdf: pd.DataFrame) -> tuple[float, float]:
    """t-검정(수치 비교) + 카이제곱(범주 연관) 수행.
    ※ 연관(association) ≠ 인과(causation) — 해석 주의."""
    # t-검정: 이탈 고객 vs 잔류 고객의 월 요금 평균 차이
    churn_yes = pdf[pdf["churn"] == 1]["monthly_charges"]
    churn_no = pdf[pdf["churn"] == 0]["monthly_charges"]
    t_stat, p_t = stats.ttest_ind(churn_yes, churn_no, equal_var=False)
    print(f"\n[t-검정] t={t_stat:.2f}, p={p_t:.2e}")

    # 카이제곱: 계약 유형(contract) vs 이탈 여부(churn) 연관성
    table = pd.crosstab(pdf["contract"], pdf["churn"])
    chi2, p_chi, dof, expected = stats.chi2_contingency(table)
    print(f"[카이제곱] chi2={chi2:.2f}, p={p_chi:.2e}")

    # 해석 출력
    alpha = 0.05
    print("\n  해석:")
    print(f"  t-검정: {'유의 !!' if p_t < alpha else '유의하지 않음'} — 요금과 이탈 간 유의한 연관")
    print(f"  카이제곱: {'유의 !!' if p_chi < alpha else '유의하지 않음'} — 계약유형과 이탈 간 유의한 연관")

    return p_t, p_chi


# 4~5. 데이터 가공 + ColumnTransformer
# 숫자 컬럼과 범주 컬럼에 각각 다른 전처리를 적용하는 ColumnTransformer.
def build_preprocessor():
    num_cols = ["tenure_months", "monthly_charges", "total_charges",
                "senior", "num_services"]
    cat_cols = ["contract", "payment_method", "gender"]

    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imp", SimpleImputer(strategy="median")),  # 결측 → 중앙값
            ("sc", StandardScaler()),                   # 스케일 통일
        ]), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        # handle_unknown='ignore': 실전에서 못 보던 범주가 와도 안 터짐
    ])
    return preprocessor, num_cols, cat_cols


# 6~7. Pipeline 학습 + 평가
# ColumnTransformer + RandomForest Pipeline으로 이탈 예측 모델을 만든다.
# Pipeline을 쓰는 이유: 데이터 누수(leakage) 방지 — 전처리가 train 안에서만 학습됨.
def step_ml(pdf: pd.DataFrame) -> float:

    preprocessor, num_cols, cat_cols = build_preprocessor()

    feature_cols = num_cols + cat_cols
    X = pdf[feature_cols]
    y = pdf["churn"]

    # stratify=y: 이탈 비율을 train/test에 동일하게 유지
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    pipe = Pipeline([
        ("prep", preprocessor),
        ("model", RandomForestClassifier(n_estimators=200, random_state=42)),
    ])
    pipe.fit(X_tr, y_tr)  # ★ 전처리 + 모델 한 번에 학습 (누수 없음)

    # 평가 — ROC-AUC (불균형 데이터에서 정확도는 무의미)
    proba = pipe.predict_proba(X_te)[:, 1]  # ★ 확률을 쓴다 (0/1 아님)
    auc = roc_auc_score(y_te, proba)
    print(f"\nROC-AUC = {auc:.3f}")
    print(classification_report(y_te, pipe.predict(X_te)))

    # 모델 저장 — Pipeline 통째로 (전처리까지 포함)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = OUTPUT_DIR / "churn_model.joblib"
    joblib.dump(pipe, str(model_path))
    print(f"모델 저장: {model_path}")

    return auc


# ──────────────────────────────────────────────
# main
# ──────────────────────────────────────────────
def main():
    # STEP 0: EDA
    df_pl = eda()
    pdf = df_pl.to_pandas()

    # total_charges에 빈 문자열이 있을 수 있음 → 숫자 변환
    pdf["total_charges"] = pd.to_numeric(pdf["total_charges"], errors="coerce")

    # STEP 2: 시각화
    step_plotly(pdf)

    # STEP 3: 통계 검정
    p_t, p_chi = step_stat_tests(pdf)

    # STEP 5~7: ML
    auc = step_ml(pdf)

    # 최종 요약
    print("\n" + "=" * 60)
    print("종합실습 2 결과 요약")
    print(f"  t-검정      p = {p_t:.2e}")
    print(f"  카이제곱    p = {p_chi:.2e}")
    print(f"  ROC-AUC      = {auc:.3f}")
    print("  산출물: output/churn_charges.html, output/churn_model.joblib")

if __name__ == "__main__":
    main()