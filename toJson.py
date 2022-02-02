import asyncio

from cevlib.match import Match, MatchCache

from time import time

import json

async def main():
    match = await Match.ByUrl("https://www.cev.eu/match-centres/2022-european-cups/cev-volleyball-challenge-cup-2022-men/chcm-61-halkbank-ankara-v-tallinn-technical-university/")

    x = await match.toJson()
    with open("sample.json", "w") as outfile:
        jdata = json.dumps(x, indent=4)
        outfile.write(jdata)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())