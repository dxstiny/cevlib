import asyncio

from cevlib.match import Match

async def main():
    x = await Match.ByUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")
    await x.init()
    print(await x.currentScore())
    print(await x.startTime())
    print(await x.venue())
    print(await x.playByPlay())
    print(await x.homeTeam())

asyncio.run(main())
