'''
최초 작성일: 2026-07-20
작성자: 임승민

실습 3: asyncio 기반 비동기 수집기
- 60건의 데이터를 동시에 수집 (동기 대비 처리 시간 비교)
- async/await + asyncio.gather로 동시 실행
- Semaphore로 동시 요청 수 제한 (백프레셔)
- 지수 백오프 재시도 + 타임아웃 + 예외 격리
'''

import time
import asyncio

MAX_CONCURRENT = 10 #동시 10개만 limit 개수.
sem = asyncio.Semaphore(MAX_CONCURRENT)

#동기 - fetch
def fetch_sync(item_id):
    time.sleep(0.1) #가짜 환경을 위해 0.1초 지연
    return {'id': item_id, 'ok': True}

def run_sync():
    start = time.perf_counter()
    results = [fetch_sync(i) for i in range(60)]
    spent = time.perf_counter() - start
    print(f'동기: {time.perf_counter() - start:.2f}초')  # 약
    return spent

#1. 비동기 - fetch
async def fetch(item_id):
    await asyncio.sleep(0.1) # time.sleep != asyncio.sleep
    return {'id': item_id, 'ok': True}

#2. 비동기 - fetch, limit(MAX_CONCURRENT) 존재
async def fetch_limited(item_id):
    async with sem: # 입장권 받기 (10장 다 나가있으면 대기)
        await asyncio.sleep(0.1)
        return {'id': item_id, 'ok': True}
    # with 블록 나가면 입장권 자동 반납

#3. 비동기 - fetch, limit + 타임 아웃 - 일정시간 지나면 -> 포기
async def fetch_with_timeout(item_id):
    async with sem:
        try:
            async with asyncio.timeout(3.0): # 3.0 초 넘으면 포기 -> TimeoutError 넘김
                await asyncio.sleep(0.1)
                return {'id': item_id, 'ok': True}
        except TimeoutError:
            return {'id': item_id, 'ok': False, 'reason': 'timeout'}

#4. 비동기 - fetch, limit + 타임아웃 + 재시도 
async def fetch_retry(item_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            # 아래 fetch_with_timeout에서 락 획득하기 때문에 데드락 걸림.
            # async with sem: 
                return await fetch_with_timeout(item_id)
        except Exception as e:
            if attempt == max_retries - 1:  # 마지막 시도였으면 포기
                return {'id': item_id, 'ok': False, 'error': str(e)}
            wait = 2 ** attempt  # 1 → 2 → 4초 (지수 백오프 -> 기다리는 시간 2배씩 늘어남.)
            print(f'{item_id} 실패, {wait}초 후 재시도')
            await asyncio.sleep(wait)

#예외 격리
async def main_async():
    #tasks = [fetch(i) for i in range(60)]
    #tasks = [fetch_limited(i) for i in range(60)]
    #tasks = [fetch_with_timeout(i) for i in range(60)]
    tasks = [fetch_retry(i) for i in range(60)]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    ok = [r for r in results if not isinstance(r, Exception)] # 정상 - ok에 저장.
    fail = [r for r in results if isinstance(r, Exception)] # 비정상 - fail에 저장.
    print(f'성공 {len(ok)}건 / 실패 {len(fail)}건')
    return results

# 비동기 
def run_async():
    start = time.perf_counter()
    results = asyncio.run(main_async())
    elapsed = time.perf_counter() - start
    print(f'비동기: {elapsed:.2f}초')
    return elapsed

if __name__ == "__main__":
    sync_time = run_sync()
    async_time = run_async()
    print(f'\n{sync_time / async_time:.1f}배 빨라짐')