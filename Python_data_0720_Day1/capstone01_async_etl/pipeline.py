"""
종합실습 1: 비동기 ETL 파이프라인 - 파이프라인
- ETL 은 Extract(추출) → Transform(변환) → Load(적재)의 약자
- Extract: 비동기 수집 · 동시성 제한 · 재시도 (← 실습 3)
- Transform: Pydantic 검증 → 유효/무효 분리 (← 실습 2)
- Load: DataFrame → CSV · Parquet 저장
- Orchestrate: `run()` 이 전체 단계를 순서대로 조율

최초 작성일: 2026-07-20
작성자: 임승민
"""

from pydantic import ValidationError
from models import User
import asyncio
import pandas as pd
from pathlib import Path
# import time

MAX_CONCURRENT = 10
sem = asyncio.Semaphore(
    MAX_CONCURRENT
)  # 동시 요청 10개로 제한 (백프레셔, 실습 3 재사용)


# 검증만 담당하는 순수 함수, 네트워크나 파일은 안건드림. 같은 입력이면 항상 같은 출력을 내므로 테스트하기 쉬움.
def transform(raw: list[dict]) -> tuple[list, list]:
    valid, invalid = [], []
    for i, row in enumerate(raw):
        try:
            valid.append(
                User(**row)
            )  # User(**row) 통과하면 -> User 인스턴스 만들어짐 -> valid에 저장.
        except ValidationError as e:
            invalid.append(
                {"index": i, "data": row, "errors": e.errors()}
            )  # 통과 못하면 ValidationError 던짐 -> invalid에 정보 저장.
    return valid, invalid


# 실제로는 외부 API 호출. 지금은 사용자 데이터를 흉내만 냄 (모의 실행)
async def fetch_one(item_id: int) -> dict:
    async with sem:
        await asyncio.sleep(0.05)
        return {
            "id": item_id,
            "username": f"user_{item_id:03d}",
            "email": f"user{item_id}@example.com",
            "age": 30,
            "is_active": True,
            "signup_date": "2024-01-01",
            "profile": {"country": "KR", "tier": "pro", "score": 80.0},
            "tags": [],
        }


# Extract - ids (id가 담긴 리스트)를 딕셔너리 담은 배열로 반환
# 비동기로 여러 건을 동시에 수집.
# return_exceptions=True로 -> 실패해도 전체가 죽지 않게 예외 격리.
async def extract(ids: list[int]) -> list[dict]:
    tasks = [fetch_one(i) for i in ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]


# Load - 검증 통과한 데이터만 DataFrame으로 변환 후 CSV·Parquet 저장
def load(valid: list, out_dir: str = "output") -> pd.DataFrame:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([v.model_dump() for v in valid])
    df.to_csv(f"{out_dir}/users.csv", index=False)
    df.to_parquet(f"{out_dir}/users.parquet", index=False)
    return df


# Orchestration (run) - 조율 —> 직접 일하지 않고 E→T→L 순서만 호출.
# 각 단계가 독립적이라 따로 테스트·수정 가능.
async def run(ids: list[int]) -> dict:
    raw = await extract(ids)  # E - extract 데이터 추출
    valid, invalid = transform(raw)  # T - transform 데이터 변환
    df = load(valid)  # L - load 데이터 로드
    return {
        "total": len(raw),
        "valid": len(valid),
        "invalid": len(invalid),
        "row_saved": len(df),
    }


if __name__ == "__main__":
    # start = time.perf_counter() # 수행시간 측정용 - 시작 시간
    summary = asyncio.run(run(list(range(1, 21))))  # id 1~20까지 20명 테스트
    print("==========요약 딕셔너리==========")
    print(summary)
    # print(time.perf_counter() - start)    # 수행시간 측정용
