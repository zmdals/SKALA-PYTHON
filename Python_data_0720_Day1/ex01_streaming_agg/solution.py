'''
작성일: 2026-07-20
작성자: 임승민

실습 1: 대용량 로그 스트리밍 집계
- 20만 행 web_logs.csv를 메모리에 올리지 않고 제너레이터로 한 줄씩 처리
- Counter를 이용한 온라인 집계 (경로·상태코드·시간대·IP)
- functools.reduce를 활용한 fold 패턴 적용
'''

import csv
from collections import Counter
from functools import reduce
import tracemalloc

#CSV 제너레이터 함수
#제너레이터는 한번 끝까지 다 읽으면 소진 - 다시 읽으면 비어있음.
def read_logs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = csv.DictReader(f)
        for row in data:
            yield row

#집계 함수
# 파일을 한 번만 훑으며 4개 지표를 동시에 채움 (single-pass)
def aggregate(logs):
    #각 키의 빈 Counter객체 생성
    path_counter = Counter()
    status_counter = Counter()
    ip_counter = Counter()
    hour_counter = Counter()

    #각 Counter 객체에 키,밸류 삽입.
    for row in logs:
        path_counter[row['path']] += 1
        status_counter[row['status']] += 1
        ip_counter[row['ip']] += 1
        hour = row['timestamp'][11:13] # 'YYYY-MM-DDTHH:MM:SS' → HH 추출
        hour_counter[hour] += 1 
    return {"path": path_counter, "status": status_counter, "ip": ip_counter, "hour": hour_counter}

#집계 함수(functools reduce 적용)
def aggregate_with_reduce(logs):
    # fold 패턴: for-loop 누적을 reduce로 표현 (path 집계만 예시)
    def merge(counter, row):
        counter[row['path']] += 1
        return counter
    return reduce(merge, logs, Counter())

#결과 출력 함수
def print_report(result):
    # 상태코드: 5XX 비율 출력
    total = sum(result['status'].values())
    err_5xx = sum(c for s,c in result['status'].items() if str(s).startswith('5'))
    ratio = err_5xx / total * 100
    print(f"\n전체 {total} 건 중 상태코드 5XX 비율: {ratio:.1f}%")

    #상태코드 전체 집계 출력
    print("\n=== 상태코드 별 집계 ===")
    for status, count in result['status'].most_common():
        print(f"{status} : {count}건")

    #시간대 상위 TOP5 출력
    print("\n=== 인기있는 시간대 TOP5 ===")
    for hour, count in result['hour'].most_common(5):
        print(f"{hour:<2}시 : {count}건") #:<2 -> 왼쪽 정렬로 폭 2칸 고정

    #경로 상위 TOP5 출력
    print("\n=== 인기있는 경로 TOP5 ===")
    for path, count in result['path'].most_common(5):
        print(f"{path:<20} : {count}건")

    #IP 상위 TOP5 출력
    print("\n=== 상위 IP TOP5 ===")
    for ip, count in result['ip'].most_common(5):
        print(f"{ip :<20} : {count}건")

#확장과제
#메모리에 CSV 통째로 올림
def read_logs_bad(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()  # 20만 줄 통째로 리스트에
    return lines

def compare_memory(file_path):
    # 1) readlines 버전 측정
    tracemalloc.start()
    lines = read_logs_bad(file_path)
    current, peak = tracemalloc.get_traced_memory()
    print(f"[readlines] 최대 메모리: {peak / 1024 / 1024:.2f} MB")
    tracemalloc.stop()
    del lines

    # 2) 제너레이터 버전 측정
    tracemalloc.start()
    for row in read_logs(file_path):
        pass # 다른 작업 없이 순회만
    current, peak = tracemalloc.get_traced_memory()
    print(f"[제너레이터] 최대 메모리: {peak / 1024 / 1024:.2f} MB")
    tracemalloc.stop()

if __name__ == "__main__":
    file_path = "../../data/web_logs.csv"
    try:
        result = aggregate(read_logs(file_path))
    except FileNotFoundError as e:
        print("파일을 찾지 못했습니다.")
        exit(1)
    else:
        print_report(result)

        #fold 패턴 검증용 (path만 확인)
        print("\n=== reduce로 집계한 path (검증용) ===")
        reduce_result = aggregate_with_reduce(read_logs(file_path))
        print(reduce_result.most_common(5))
        print("일치 여부:", reduce_result == result['path']) #True

        # 확장 과제: 메모리 비교
        print("\n=== 메모리 비교 (readlines vs generator) ===")
        compare_memory(file_path)