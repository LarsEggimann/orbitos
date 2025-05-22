import asyncio

async def run_blocking(func, *args):
    return await asyncio.to_thread(func, *args)