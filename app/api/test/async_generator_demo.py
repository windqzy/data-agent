"""演示两个异步任务在同一个线程上交替消费生成器。"""

import asyncio
import threading
from collections.abc import AsyncIterator
from time import perf_counter


def log(start: float, message: str) -> None:
    elapsed = perf_counter() - start
    print(f"[{elapsed:5.2f}s] [线程 {threading.get_ident()}] {message}", flush=True)


async def fake_stream(
    name: str, delay: float, count: int, start: float
) -> AsyncIterator[str]:
    for i in range(1, count + 1):
        log(start, f"{name}：开始等待 {delay} 秒，准备第 {i} 条数据")
        # 暂停当前任务，让事件循环有机会执行另一个任务。
        await asyncio.sleep(delay)
        yield f"{name} 的第 {i} 条数据"


async def consume_stream(
    name: str, delay: float, count: int, start: float
) -> None:
    async for chunk in fake_stream(name, delay, count, start):
        log(start, f"{name}：收到 -> {chunk}")
    log(start, f"{name}：结束")


async def main() -> None:
    start = perf_counter()
    print("两个异步任务共用一个线程；等待时让出执行机会，不保证严格轮流。")
    print("A 每 1 秒产生一条，共 3 条；B 每 0.6 秒产生一条，共 5 条。")
    # 同时安排两个任务。若逐个 await，则前一个结束后才会启动后一个。
    await asyncio.gather(
        consume_stream("任务 A", delay=1.0, count=3, start=start),
        consume_stream("任务 B", delay=0.6, count=5, start=start),
    )
    log(start, "全部完成：两路等待各约 3 秒，并发总耗时约 3 秒。")


if __name__ == "__main__":
    asyncio.run(main())
