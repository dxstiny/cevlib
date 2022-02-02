import asyncio

from cevlib.match import Match, MatchCache

from time import time

import json

async def main():
    match = await Match.ByUrl("https://www.cev.eu/match-centres/2022-european-cups/cev-volleyball-challenge-cup-2022-men/chcm-61-halkbank-ankara-v-tallinn-technical-university/")

    cache = await MatchCache.FromMatch(match)

    print("playByPlay", cache.playByPlay)
    print("competition", cache.competition)
    print("topPlayers", cache.topPlayers)
    print("report", cache.report)
    print("gallery", cache.gallery) # Disclaimer: Photos featured on the CEV Photo Galleries are downloadable copyright free for media purposes only and only if CEV is credited as the source material. They are protected by copyright for all other commercial purposes. Those wishing to use CEV Photo Gallery photos for other commercial purposes should contact press@cev.eu
    print("matchCentreLink", cache.matchCentreLink)
    print("currentScore", cache.currentScore)
    print("duration", cache.duration)
    print("startTime", cache.startTime)
    print("venue", cache.venue)
    print("homeTeam", cache.homeTeam)
    print("watchLink", cache.watchLink)
    print("highlightsLink", cache.highlightsLink)
    print("state", cache.state)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
