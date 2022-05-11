import asyncio

from cevlib.cevlib_match import Match

async def main():
    # get a match object by its match centre url
    match: Match = await Match.ByUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")

    # print all available properties

    print(await match.playByPlay())
    print(await match.competition())
    print(await match.topPlayers())
    print(await match.report())
    print(match.gallery) # Disclaimer: Photos featured on the CEV Photo Galleries are downloadable copyright free for media purposes only and only if CEV is credited as the source material. They are protected by copyright for all other commercial purposes. Those wishing to use CEV Photo Gallery photos for other commercial purposes should contact press@cev.eu
    print(match.matchCentreLink)

    await match.init()

    print(await match.currentScore())
    print(await match.duration())
    print(await match.startTime())
    print(await match.venue())
    print(await match.homeTeam())
    print(await match.watchLink())
    print(await match.highlightsLink())
    print(await match.state())

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
