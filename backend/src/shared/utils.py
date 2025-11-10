import asyncio
from typing import Any, Coroutine
import logging
import time

logger = logging.getLogger()

async def run_blocking(func, *args):
    return await asyncio.to_thread(func, *args)


def run_async_in_background(coroutine: Coroutine[Any, Any, Any]) -> None:
    try:
        st1 = time.time()
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, so create one (likely in a worker thread)
        st = time.time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coroutine)
        logger.debug("created new loop. Time taken: %s", time.time() - st)
    else:
        loop.create_task(coroutine)
        logger.debug("using existing loop. Time taken: %s", time.time() - st1)