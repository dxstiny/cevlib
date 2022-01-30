import asyncio

from cevlib.match import Match

async def main():
    match = await Match.ByUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")
    await match.init()
    print(await match.competition())
    print(await match.currentScore())
    print(await match.duration())
    print(await match.startTime())
    print(await match.venue())
    print(await match.playByPlay())
    print(await match.homeTeam())
    print(await match.matchCentreLink())
    print(await match.watchLink())
    print(await match.highlightsLink())

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
