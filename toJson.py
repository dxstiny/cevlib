import asyncio

from cevlib.match import Match, MatchCache

from time import time

import json

async def main():
    match = await Match.ByUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/women/clw-25-sc-prometey-dnipro-v-lokomotiv-kaliningrad-region/")

    x = await match.toJson()
    with open("sample.json", "w") as outfile:
        jdata = json.dumps(x, indent=4)
        outfile.write(jdata)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())