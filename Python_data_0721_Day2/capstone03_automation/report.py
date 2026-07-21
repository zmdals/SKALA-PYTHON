"""
[종합실습 3] 리포트 생성 모듈
- aggregate(): 순수 함수 — 입력만 받아 결과만 돌려줌 (파일 안 건드림)
- render(): 집계 결과를 Jinja2 템플릿에 부어 HTML 파일로 저장
- run_once(): 세 실행 방식(루프·schedule·cron)이 모두 호출하는 단일 함수
"""

import sys
from pathlib import Path

# 이 스크립트의 위치를 기준으로 config.py를 찾을 수 있게 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from config import CONFIG

#데이터 → 리포트에 넣을 값들을 계산. 파일은 안 건드림(순수 함수)

def aggregate(df: pd.DataFrame, top_n: int = 10) -> dict:
    # 타입 변환 + amount 계산
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0)
    df["amount"] = df["quantity"] * df["unit_price"] * (1 - df["discount"])

    return {
        "kpi": {
            "총매출": int(df["amount"].sum()),
            "주문수": len(df),
            "평균주문액": round(float(df["amount"].mean()), 1),
        },
        "by_category": (
            df.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
            .to_dict("records")
        ),
    }


# 집계 결과를 Jinja2 템플릿에 렌더링하여 HTML 파일로 저장
def render(data: dict, cfg) -> Path:
    # 템플릿 경로: 이 파일 기준 templates/ 폴더
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    tpl = env.get_template("report.html")

    html = tpl.render(
        title=cfg.title,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **data,
    )

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    # ★ 타임스탬프를 파일명에 -> 이전 리포트가 안 지워짐 (이력 보존)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = cfg.output_dir / f"report_{stamp}.html"
    out.write_text(html, encoding="utf-8")
    return out

# 리포트 1회 생성. 루프·schedule·cron 모두 이 함수를 호출
def run_once():
    df = pd.read_csv(CONFIG.data_path)
    data = aggregate(df, CONFIG.top_n)
    path = render(data, CONFIG)
    print(f"리포트 생성: {path}")


if __name__ == "__main__":
    run_once()
