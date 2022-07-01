import asyncio

from cevlib.match import Match

from time import time

async def main() -> None:
    # cache up to 300ms

    match = await Match.byUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")
    match2 = await Match.byUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")

    t1 = time()
    cache = await match.cache()
    print(cache.venue)
    print(cache.result)
    print(cache.homeTeam)
    print(cache.competition)
    t2 = time()

    print(await match2.init())
    print(await match2.venue())
    print(await match2.result())
    print(await match2.homeTeam())
    print(await match2.competition())
    t3 = time()

    print(t2 - t1)
    print(t3 - t2)

    # BUT
    # cache up to 1s faster

    match = await Match.byUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")
    match2 = await Match.byUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")

    t1 = time()
    cache = await match.cache()
    print(cache.result)
    print(cache.homeTeam)
    print(cache.report)
    t2 = time()

    print(await match2.init())
    print(await match2.result())
    print(await match2.homeTeam())
    print(await match2.report())
    t3 = time()

    print(t2 - t1)
    print(t3 - t2)

    return

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
