import asyncio

from cevlib.match import Match, MatchCache

from time import time

import json

async def main():
    match = await Match.ByUrl("https://www.cev.eu/match-centres/2022-european-cups/cev-volleyball-cup-2022-women/ccw-54-mladost-zagreb-v-lks-commercecon-lodz/")

    # cache = await MatchCache.FromMatch(match)

    await match.init()
    async def implement(score):
        print(score)
        print(await match.duration())

    match.addScoreObserver(implement)

    while True:
        await asyncio.sleep(1)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
