'''
최초 작성일: 2026-07-20
작성자: 임승민

실습 2: Pydantic v2 중첩 스키마 검증
- api_response.json 40건 중 오염 데이터 4건을 걸러내는 검증기 구현
- Field()로 범위 제약, field_validator로 커스텀 이메일 형식 검증
- 중첩 모델(Profile)로 profile 필드 자동 검증
- try/except로 실패해도 멈추지 않고 유효/무효 분리 + 탈락 사유 기록
'''

import json
from pydantic import BaseModel, Field, field_validator, ValidationError

#json 데이터 로드
def safe_load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(e)
    else:
        print('파일을 정상적으로 로드 했습니다.')
        return data
    finally:
        print('파일 로드 종료')

#Profile 스키마 모델 정의
class Profile(BaseModel):
    country : str = Field(min_length=1)
    tier: str
    score: float = Field(ge=0, le=100)

#User 스키마 모델 정의
class User(BaseModel):
    id : int
    username : str
    email : str # str로 받고 아래 field_validator에서 직접 형식 검증 (EmailStr 대신 커스텀 구현)
    age : int = Field(ge=0, le=150) # 음수 나이 거부 (오염 데이터: age=-5)
    is_active : bool
    signup_date : str
    profile: Profile # 중첩 모델 — 자동으로 Profile로 변환+검증
    tags: list[str] = []

    #이메일 필드 커스텀 validator
    @field_validator('email')
    @classmethod
    def check_email_format(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError("이메일에 @가 없습니다.")
        local, _, domain = v.partition('@') #partition('@') -> @를 기준으로 3조각으로 나눔 -> 예) user1, @, example.com
        if '.' not in domain:
            raise ValueError('이메일 도메인 형식이 올바르지 않습니다')
        return v
    
#데이터 검증 및 분리. valid - 정상, invalid - 비정상
def validate_users(data: list[dict]) -> tuple[list,list]:
    valid, invalid = [], []
    for i, row in enumerate(data):
        try:
            user = User(**row)
            valid.append(user)
        except ValidationError as e:
            invalid.append({'index': i, 'data': row, 'errors': e.errors()}) #e.errors() -> 어떤 필드가 왜 틀렸는지 리스트.
    return valid, invalid

#오류 확인표 출력
def print_invalid_report(invalid):
    print(f"{'행':<4}{'필드':<15}{'사유'}")
    for item in invalid: 
        for err in item['errors']:
            field = '.'.join(str(x) for x in err['loc'])  # 중첩 경로 (예: profile.score), 'loc': ('age',...) 이런식으로 오류 필드가 담김.
            print(f"{item['index']:<4}{field:<15}{err['msg']}")


if __name__ == '__main__':
    file_path = '../../data/api_response.json'
    raw = safe_load_json(file_path)
    data = raw['results']

    #전체 건수 + 검증 데이터 분리 출력
    valid, invalid = validate_users(data)
    print(f'\n전체 {len(raw["results"])}건 → 유효 {len(valid)} / 오염 {len(invalid)}')

    #오염 데이터 정리 표 출력
    print("\n===========오염 데이터 정리===========")
    print_invalid_report(invalid)