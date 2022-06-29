import asyncio

from cevlib.match import Match

import json

async def main():
    match = await Match.byUrl("https://www.cev.eu/match-centres/2022-european-cups/cev-volleyball-challenge-cup-2022-women/chcw-78-rc-cannes-v-savino-del-bene-scandicci/")

    x = await match.toJson()
    with open("sample.json", "w") as outfile:
        jdata = json.dumps(x, indent=4)
        outfile.write(jdata)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
