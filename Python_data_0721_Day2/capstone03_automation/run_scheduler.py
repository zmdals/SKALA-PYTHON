"""
[종합실습 3] 스케줄러 모듈
- 인자:
- --interval 0: 1회 실행 (기본)
- --interval 60: 60초마다 반복 (Ctrl+C로 중지)

실행 예시: python Python_data_0721_Day2/capstone03_automation/run_scheduler.py
     python Python_data_0721_Day2/capstone03_automation/run_scheduler.py --interval 60
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import argparse
import time
from report import run_once


def main():
    ap = argparse.ArgumentParser(description="매출 리포트 자동 생성")
    ap.add_argument(
        "--interval", type=int, default=0,
        help="초 단위 반복 주기. 0이면 1회만 실행 (기본: 0)",
    )
    args = ap.parse_args()

    if args.interval == 0:
        run_once()
        return

    print(f"[스케줄러] {args.interval}초 간격으로 반복 실행 (Ctrl+C로 중지)")
    while True:
        run_once()
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
