# -*- coding: utf-8 -*-

import asyncio
from typing import Any


class Timer:
    """
    A class to manage a timer that executes a callback function after a specified timeout.

    """
    def __init__(self, timeout: int, callback):
        """
        Initializes the Timer with the given timeout and callback function.

        Parameters
        ----------
        timeout : int
            The timeout duration in seconds.
        callback : Any
            The callback function to be executed after the timeout.
        """
        self._timeout: int = timeout
        self._callback: Any = callback
        self._task: asyncio.Task = asyncio.ensure_future(self._job())

    def start(self) -> None:
        """
        Starts the timer. If the timer is already running, it cancels the current task and starts a new one.
        """
        self._task.cancel()
        self._task = asyncio.ensure_future(self._job())

    async def _job(self) -> None:
        """
        The internal coroutine that manages the timer. It sleeps for the specified timeout and then executes the callback function.
        """
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self) -> None:
        """
        Cancels the timer. If the timer is not running, it does nothing.
        """
        self._task.cancel()


async def timeout_callback() -> None:
    await asyncio.sleep(0.1)
    print('echo!')
