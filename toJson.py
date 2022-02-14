import asyncio

from cevlib.match import Match

import json

async def main():
    match = await Match.ByUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/women/clw-50-vk-dukla-liberec-v-dinamo-moscow/")

    x = await match.toJson()
    with open("sample.json", "w") as outfile:
        jdata = json.dumps(x, indent=4)
        outfile.write(jdata)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
