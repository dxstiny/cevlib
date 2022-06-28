from typing import Any, Callable, List, Optional, TypeVar, cast, Iterable
from threading import Thread
import asyncio
from queue import Queue


T = TypeVar("T")


async def asyncRunInThread(target: Callable[[Any], None],
                           *args: Optional[Iterable[Any]]) -> None:
    thread = Thread(target = target, args = args)
    thread.start()
    while thread.is_alive():
        await asyncio.sleep(1)

async def asyncRunInThreadWithReturn(target: Callable[[Any], T],
                                     *args: Optional[Iterable[Any]]) -> T:
    queue: Queue[Any] = Queue()

    def _implement() -> None:
        ret = target(*args) if args else target() # type: ignore
        queue.put_nowait(ret)

    thread = Thread(target = _implement)
    thread.start()
    while thread.is_alive():
        await asyncio.sleep(1)
    return cast(T, queue.get_nowait())
