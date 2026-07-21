"""
- [종합실습 3] 설정 모듈
- frozen=True: 만든 뒤엔 수정 불가 → 설정값이 몰래 바뀌는 버그를 원천 차단.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    data_path: Path = Path("../../data/sales_raw.csv")
    output_dir: Path = Path("output")
    title: str = "일일 매출 리포트"
    top_n: int = 10


CONFIG = Config()