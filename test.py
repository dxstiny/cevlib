import os

import asyncio

from cevlib.match import Match, MatchCache

async def main():
    match = await Match.byUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/women/clw-38-lp-salo-v-asptt-mulhouse-vb/")

    cache = await match.cache()
    # OR
    cache = await MatchCache.FromMatch(match)

    print("playByPlay", cache.playByPlay)
    print("competition", cache.competition)
    print("topPlayers", cache.topPlayers)
    print("report", cache.report)
    print("info", cache.info)
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

if os.name == "nt": # windows only
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
