import asyncio

from cevlib.match import Match, MatchCache

from time import time

import json

async def main():
    match = await Match.ByUrl("https://www.cev.eu/match-centres/2022-european-cups/cev-volleyball-cup-2022-women/ccw-54-mladost-zagreb-v-lks-commercecon-lodz/")

    x = await match.toJson()
    with open("sample.json", "w") as outfile:
        jdata = json.dumps(x, indent=4)
        outfile.write(jdata)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())