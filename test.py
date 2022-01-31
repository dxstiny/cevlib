import asyncio

from cevlib.match import Match, MatchCache

from time import time

async def main():
    match = await Match.ByUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")
    cache = await MatchCache.FromMatch(match)

    print(cache.playByPlay)
    print(cache.competition)
    print(cache.topPlayers)
    print(cache.report)
    print(cache.gallery) # Disclaimer: Photos featured on the CEV Photo Galleries are downloadable copyright free for media purposes only and only if CEV is credited as the source material. They are protected by copyright for all other commercial purposes. Those wishing to use CEV Photo Gallery photos for other commercial purposes should contact press@cev.eu
    print(cache.matchCentreLink)
    print(cache.currentScore)
    print(cache.duration)
    print(cache.startTime)
    print(cache.venue)
    print(cache.homeTeam)
    print(cache.watchLink)
    print(cache.highlightsLink)
    print(cache.finished)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
