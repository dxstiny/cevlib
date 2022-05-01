import asyncio
from cevlib.competitions import Competitions, Competition

async def main():
    competitions = await Competitions.GetAll() # get all competitions (Competitions object)
    print( competitions )

    link = competitions.get(0) # get the first competition (CompetitionLink object)
    print( link )

    assert link
    competition = await Competition.FromUrl(link.href) # get the first competition (Competition object)
    print( competition )

    assert competition
    round = competition.get(1) # get the first round (Round object)
    print( round )

    assert round
    pool = round.get(0) # get the first pool (Pool object)
    print( pool )

    assert pool
    standingsPool = pool.standingsPool # get this pool's standings (StandingsPool object)
    print( standingsPool )

    assert pool
    draw = pool.get(0) # get the first draw (Draw object)
    print( draw )

    assert draw
    match = draw.get(0) # get the first match (CalendarMatch object)
    print ( match )

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
