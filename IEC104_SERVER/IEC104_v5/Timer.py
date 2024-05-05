import asyncio


class Timer:
    def __init__(self, timeout: int, callback):
        self._timeout: int = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    def start(self) -> None:
        self._task.cancel()
        self._task = asyncio.ensure_future(self._job())

    async def _job(self) -> None:
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self) -> None:
        self._task.cancel()


async def timeout_callback() -> None:
    await asyncio.sleep(0.1)
    print('echo!')
