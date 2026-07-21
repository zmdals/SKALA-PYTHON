"""
- plot_duration_by_hour
"""
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd

#한글폰트 고정
matplotlib.rcParams["font.family"] = "AppleGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

#Seaborn 정적 차트: 시간대별 평균 소요시간 (주중 vs 주말)
def plot_duration_by_hour(df:pd.DataFrame, save_path: str) -> None:
    hourly = df.groupby(["hour", "is_weekend"])["duration_min"].mean().reset_index()
    hourly["구분"] = hourly["is_weekend"].map({0: "주중", 1: "주말"})

    plt.figure(figsize=(12, 5))
    sns.barplot(data=hourly, x="hour", y="duration_min", hue="구분")
    plt.title("시간대별 평균 소요시간 (주중 vs 주말)")
    plt.xlabel("승차 시간대")
    plt.ylabel("평균 소요시간 (분)")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"Seaborn 차트 저장: {save_path}")

#Plotly 인터랙티브 차트: 주행 거리 vs 소요시간 산점도
def plot_interactive_duration(df: pd.DataFrame, save_path: str) -> None:
    """Plotly 인터랙티브 차트: 시간대×요일별 평균 소요시간 히트맵"""
    day_labels = ["월", "화", "수", "목", "금", "토", "일"]

    pivot = df.groupby(["day_of_week", "hour"])["duration_min"].mean().reset_index()
    pivot["요일"] = pivot["day_of_week"].map(dict(enumerate(day_labels)))

    fig = px.density_heatmap(
        pivot,
        x="hour",
        y="요일",
        z="duration_min",
        title="시간대 × 요일별 평균 소요시간 (분)",
        labels={"hour": "승차 시간대", "요일": "요일", "duration_min": "평균 소요시간(분)"},
        color_continuous_scale="YlOrRd",
    )
    fig.update_layout(yaxis=dict(categoryorder="array", categoryarray=day_labels))
    fig.write_html(save_path)
    print(f"Plotly 차트 저장: {save_path}")
