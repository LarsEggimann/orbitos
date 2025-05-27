import asyncio
from typing import Any, Coroutine


async def run_blocking(func, *args):
    return await asyncio.to_thread(func, *args)


def run_async_in_background(coroutine: Coroutine[Any, Any, Any]) -> None:
    try:
        asyncio.get_running_loop().create_task(coroutine)
    except RuntimeError:
        asyncio.run(coroutine)
