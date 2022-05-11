from typing import Any, Callable, List, Optional
from threading import Thread
import asyncio
from queue import Queue


async def asyncRunInThread(target: Callable, args: Optional[List[Any]]) -> None:
    return target(*args)
    # NOTE threads don't work with PyScript
    
    t1 = Thread(target = target, args = args)
    t1.start()
    while t1.is_alive():
        await asyncio.sleep(1)

async def asyncRunInThreadWithReturn(target: Any, *args) -> Any:
    return target(*args)
    # NOTE threads don't work with PyScript

    q = Queue()

    def _implement() -> None:
        ret = target(*args) if args else target()
        q.put_nowait(ret)

    t1 = Thread(target = _implement)
    t1.start()
    while t1.is_alive():
        await asyncio.sleep(1)
    return q.get_nowait()
