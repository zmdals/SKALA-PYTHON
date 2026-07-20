"""
종합실습 1: 비동기 ETL 파이프라인 - 데이터 모델
- 실습 2의 Pydantic 모델 재사용

최초 작성일: 2026-07-20
작성자: 임승민
"""

from pydantic import BaseModel, Field, field_validator


class Profile(BaseModel):
    country: str
    tier: str
    score: float = Field(ge=0, le=100)


class User(BaseModel):
    id: int
    username: str
    email: str
    age: int = Field(ge=0, le=150)
    is_active: bool
    signup_date: str
    profile: Profile
    tags: list[str] = []

    # 이메일 형식 체크: 1.@ 없는지, 2.도메인에 . 없는지
    @field_validator("email")
    @classmethod
    def check_email_format(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("이메일에 @가 없습니다.")
        local, _, domain = v.partition("@")
        if "." not in domain:
            raise ValueError("이메일 도메인 형식이 올바르지 않습니다")
        return v
