import asyncio

from cevlib.match import Match
from cevlib.types.results import Result

async def main() -> None:
    match = await Match.byUrl("https://www.cev.eu/match-centres/2022-european-cups/cev-volleyball-cup-2022-women/ccw-54-mladost-zagreb-v-lks-commercecon-lodz/")

    await match.init()
    async def implement(x: Match, score: Result) -> None:
        print(score)
        print(await x.duration())

    match.addScoreObserver(implement)
    match.setScoreObserverInterval(10) # 10s

    while True:
        await asyncio.sleep(1)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
