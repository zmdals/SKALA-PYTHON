"""
종합실습 1: 비동기 ETL 파이프라인 - 테스트 코드
- 실행: 터미널 test_pipeline.py가 있는 경로에서 'pytest -v' 실행
- pytest -v를 사용하면, 함수 호출 할 필요 없음.

최초 작성일: 2026-07-20
작성자: 임승민
"""

from pipeline import transform
import pandas as pd


def test_정상_데이터는_valid에_들어간다():
    rows = [
        {
            "id": 1,
            "username": "user1",
            "email": "user1@example.com",
            "age": 30,
            "is_active": True,
            "signup_date": "2024-01-01",
            "profile": {"country": "KR", "tier": "pro", "score": 90.0},
            "tags": [],
        }
    ]
    valid, invalid = transform(rows)
    assert len(valid) == 1
    assert len(invalid) == 0


def test_음수_나이는_invalid에_들어간다():
    rows = [
        {
            "id": 2,
            "username": "user2",
            "email": "user2@example.com",
            "age": -5,
            "is_active": True,
            "signup_date": "2024-01-01",
            "profile": {"country": "KR", "tier": "pro", "score": 90.0},
            "tags": [],
        }
    ]
    valid, invalid = transform(rows)
    assert len(valid) == 0
    assert len(invalid) == 1


def test_유효_무효_건수_합은_전체_건수와_같다():
    rows = [
        # invalid 데이터
        {
            "id": 2,
            "username": "user2",
            "email": "user2@example.com",
            "age": -5,
            "is_active": True,
            "signup_date": "2024-01-01",
            "profile": {"country": "KR", "tier": "pro", "score": 90.0},
            "tags": [],
        },
        # valid 데이터
        {
            "id": 1,
            "username": "user1",
            "email": "user1@example.com",
            "age": 30,
            "is_active": True,
            "signup_date": "2024-01-01",
            "profile": {"country": "KR", "tier": "pro", "score": 90.0},
            "tags": [],
        },
    ]
    valid, invalid = transform(rows)
    assert len(rows) == len(valid) + len(invalid)


def test_parquet_라운드트립(tmp_path):
    # 테스트용 가짜데이터
    df = pd.DataFrame({"id": [1, 2], "price": [10.5, 20.0]})

    # 임시 폴더에 parquet으로 저장.
    p = tmp_path / "test.parquet"
    df.to_parquet(p, index=False)

    # 저장된 parquet 다시 읽어옴
    back = pd.read_parquet(p)

    # 원본(df)이랑 읽어온 파일(back)이 같은지 확인
    pd.testing.assert_frame_equal(df, back)
